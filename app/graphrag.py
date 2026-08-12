"""GraphRAG layer - grounded question answering over the graph.

Turns a natural-language question into an intent plus entity names, pulls
evidence using ONLY the parameterised query functions in app/queries.py
(no Cypher is ever built from the question), and composes an answer from
that evidence - via Gemini when a key is available, otherwise with a
retrieval template. Because it stands entirely on the query layer it
behaves identically in mock and live mode.

The heuristic keyword rules are ordered so that more specific patterns
win: "co-invest" must beat "invest", and "most connected" must beat
"investor" matching the portfolio keyword.
"""
import json
import os
import re

from . import db, queries

INTENTS = ("portfolio", "pairs", "interlocks", "alumni", "reach", "path",
           "hubs", "neighborhood")
_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

_KEYWORDS = (
    (re.compile(r"most connected|hub|popular"), "hubs"),
    (re.compile(r"co-?invest|share|together"), "pairs"),
    (re.compile(r"board"), "interlocks"),
    (re.compile(r"alumni|study|student|placed|intern|mentor|college|university"), "alumni"),
    (re.compile(r"within|reach"), "reach"),
    (re.compile(r"invest"), "portfolio"),
    (re.compile(r"connect"), "path"),
)

_type_cache = {}


def _client():
    from google import genai
    return genai.Client()


def _extract_json(text):
    """Best-effort JSON object extraction from an LLM response."""
    text = (text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        return {}
    try:
        data = json.loads(text[start:end + 1])
        return data if isinstance(data, dict) else {}
    except ValueError:
        return {}


def _llm_parse(question):
    """Strict-JSON intent/entity extraction via Gemini; None on any failure."""
    try:
        resp = _client().models.generate_content(
            model=_MODEL,
            contents=(
                "Classify this graph question. Return ONLY strict JSON "
                '{"intent": "...", "entities": ["..."]}. '
                "intent must be exactly one of: portfolio, pairs, interlocks, "
                "alumni, reach, path, hubs, neighborhood. entities: up to 4 "
                "node names mentioned in the question, verbatim.\n"
                'Question: "%s"' % question))
        data = _extract_json(resp.text)
        if data.get("intent") not in INTENTS:
            return None
        names = [str(n) for n in (data.get("entities") or []) if str(n).strip()]
        return {"intent": data["intent"], "entities": names[:4]}
    except Exception:
        return None


def _tokens(ql):
    return [t for t in re.sub(r"[^\w\s]", " ", ql).split() if len(t) > 1]


def _ground_one(domain, ql, term):
    """Ground a name to a graph node; None when it does not exist."""
    term = term.strip()
    if not term:
        return None
    exact = term.lower()
    for r in queries.search_ci(domain, term):
        if r["name"].lower() == exact:
            return {"name": r["name"], "type": r["type"]}
    for r in queries.search_ci(domain, term):
        if r["name"].lower() in ql:
            return {"name": r["name"], "type": r["type"]}
    return None


def _ground(domain, ql, names):
    entities, unmatched, seen = [], [], set()
    for name in names:
        ent = _ground_one(domain, ql, name)
        if ent is None:
            unmatched.append(name)
        elif ent["name"].lower() not in seen:
            seen.add(ent["name"].lower())
            entities.append(ent)
    return entities, unmatched


def _heuristic_parse(domain, ql):
    """Keyword intent + token grounding, used when the LLM is unavailable."""
    intent = "neighborhood"
    for pattern, kind in _KEYWORDS:
        if pattern.search(ql):
            intent = kind
            break
    names = []
    for token in _tokens(ql):
        ent = _ground_one(domain, ql, token)
        if ent and ent["name"].lower() not in {n.lower() for n in names}:
            names.append(ent["name"])
        if len(names) >= 4:
            break
    return {"intent": intent, "entities": names}


def _neighborhood(domain, entities):
    facts = []
    for e in entities:
        try:
            queries.node(domain, e["name"])
        except LookupError:
            continue
        for link in queries.neighborhood_directed(domain, e["name"]):
            props = link.get("props") or {}
            if link.get("incoming"):
                facts.append({"from": link["name"], "rel": link["rel"],
                              "to": e["name"], "props": props})
            else:
                facts.append({"from": e["name"], "rel": link["rel"],
                              "to": link["name"], "props": props})
    return facts


def _retrieve(domain, meta, intent, entities, question):
    if intent == "portfolio" and meta.get("portfolio_rel") and entities:
        e = entities[0]
        facts = []
        for r in queries.portfolio(domain, e["name"]):
            props = {}
            if "amount" in r:
                props["amount_usd"] = r["amount"]
            if "round" in r:
                props["round"] = r["round"]
            if "year" in r:
                props["year"] = r["year"]
            facts.append({"from": r["investor"], "rel": meta["portfolio_rel"],
                          "to": e["name"], "props": props})
        return facts[:40]
    if intent == "pairs":
        return [{"from": r["left"], "rel": meta["pairs_rel"], "to": r["right"],
                 "props": {"shared": r["shared"]}}
                for r in queries.shared_pairs(domain, 8)][:40]
    if intent == "interlocks":
        return [{"from": r["person"], "rel": meta["interlock_rel"],
                 "to": r["org_b"], "props": {"also": r["org_a"]}}
                for r in queries.interlocks(domain, 8)][:40]
    if intent == "alumni":
        rows = queries.alumni_chains(domain, 12)
        if entities:
            insts = [e["name"].lower() for e in entities]
            rows = [g for g in rows
                    if any(i in g["institution"].lower() for i in insts)]
        facts = []
        for g in rows:
            for member in g["members"]:
                facts.append({"from": member, "rel": meta["study_rel"],
                              "to": g["institution"], "props": {}})
        return facts[:40]
    if intent == "reach" and meta.get("reach_rel") and entities:
        e = entities[0]
        return [{"from": r["investor"], "rel": meta["reach_rel"], "to": e["name"],
                 "props": {}}
                for r in queries.reachability(domain, e["name"])][:40]
    if intent == "hubs":
        return [{"from": r["name"], "rel": "HUB", "to": r["name"],
                 "props": {"degree": r["degree"]}}
                for r in queries.hubs(domain, 8)][:40]
    if intent == "path":
        if len(entities) >= 2:
            recs = queries.shortest_path(domain, entities[0]["name"],
                                         entities[1]["name"])
            if recs:
                return [dict(s) for s in recs[0]["steps"]][:40]
        return _neighborhood(domain, entities)[:40]
    return _neighborhood(domain, entities)[:40]


def _type_of(domain, name):
    key = (domain, name.lower())
    if key not in _type_cache:
        kind = ""
        for r in queries.search_ci(domain, name):
            if r["name"].lower() == key[1]:
                kind = r["type"]
                break
        _type_cache[key] = kind
    return _type_cache[key]


def _subgraph(domain, entities, facts):
    nodes, seen, edges, edge_seen = [], set(), [], set()
    for e in entities:
        key = e["name"].lower()
        if key in seen:
            continue
        seen.add(key)
        nodes.append({"name": e["name"], "type": e["type"], "hop": 0})
    for f in facts:
        ekey = (f["from"].lower(), f["to"].lower(), f["rel"])
        if ekey not in edge_seen:
            edge_seen.add(ekey)
            edges.append({"from": f["from"], "to": f["to"], "rel": f["rel"]})
        for name in (f["from"], f["to"]):
            key = name.lower()
            if key in seen:
                continue
            seen.add(key)
            nodes.append({"name": name, "type": _type_of(domain, name), "hop": 1})
            if len(nodes) >= 60:
                break
        if len(nodes) >= 60:
            break
    return {"nodes": nodes, "edges": edges}


def _props_suffix(props):
    if not props:
        return ""
    return " (%s)" % ", ".join("%s=%s" % (k, v)
                               for k, v in sorted(props.items()))


def _llm_answer(meta, question, facts):
    """Answer from the facts via Gemini; None on any failure."""
    if not facts:
        return None
    try:
        lines = ["%s --%s--> %s%s" % (f["from"], f["rel"], f["to"],
                                      _props_suffix(f.get("props") or {}))
                 for f in facts]
        verbs = ", ".join("%s=%s" % (k, v)
                          for k, v in sorted(meta.get("rel_labels", {}).items()))
        kinds = ", ".join(sorted(meta.get("node_labels", {})))
        resp = _client().models.generate_content(
            model=_MODEL,
            contents=(
                "You are answering questions about the %s network. "
                "Relationship verbs: %s. Node types: %s. "
                "Answer in 2-4 sentences using ONLY the facts below. Cite "
                "entity names. If the facts do not answer the question, say "
                "exactly: The graph doesn't contain that information.\n"
                "Facts:\n%s\nQuestion: %s\n"
                'Return ONLY strict JSON {"answer": "..."}.'
                % (meta["name"], verbs, kinds, "\n".join(lines), question)))
        text = (resp.text or "").strip()
        data = _extract_json(text)
        ans = data.get("answer") or text
        return ans or None
    except Exception:
        return None


def _retrieval_answer(meta, facts):
    if not facts:
        return "The graph doesn't contain that information."
    bits = ["%s --%s--> %s%s" % (f["from"], f["rel"], f["to"],
                                 _props_suffix(f.get("props") or {}))
            for f in facts[:5]]
    name = meta["name"] if "network" in meta["name"].lower() \
        else meta["name"] + " network"
    return "From the %s: %s." % (name, "; ".join(bits))


def _compose(meta, question, facts):
    text = _llm_answer(meta, question, facts)
    if text:
        return text, "llm"
    return _retrieval_answer(meta, facts), "retrieval"


def answer(domain_id, question):
    """Full pipeline: parse, retrieve, compose; returns the contract payload."""
    meta = queries.get_meta(domain_id)
    ql = question.strip().lower()
    parsed = _llm_parse(question) or _heuristic_parse(domain_id, ql)
    entities, unmatched = _ground(domain_id, ql, parsed["entities"])
    facts = _retrieve(domain_id, meta, parsed["intent"], entities, question)
    text, source = _compose(meta, question, facts)
    return {
        "question": question,
        "domain": meta["id"],
        "intent": parsed["intent"],
        "entities": entities,
        "unmatched": unmatched,
        "facts": facts,
        "subgraph": _subgraph(domain_id, entities, facts),
        "answer": text,
        "source": source,
    }
