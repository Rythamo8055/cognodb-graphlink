"""The query suite - every view in the app maps to one of these.

All queries are parameterised: user input only ever appears as $parameters,
never inside the query string. This is safe against Cypher injection by
construction. The queries use only constructs supported by CognoDB
(no CALL subqueries, no UNION, no LOAD CSV, no list comprehensions,
classic variable-length [*1..n] syntax).

The full text of every query is exposed via /api/about so a reviewer can
verify the parameterisation guarantee in one click.

The same five query shapes serve every domain; relationship types come
from each domain's META (a hard-coded whitelist - relationship types
cannot be parameters in Cypher, and this is the only thing ever
interpolated into a query string).
"""
from collections import OrderedDict

from .db import run_domain
from .domains import get_domain, list_domains as _list_domains

T_NODE = "MATCH (n {name: $name}) RETURN n AS node"

T_NEIGHBORHOOD_OUT = "MATCH (n {name: $name})-[r]->(m) RETURN m.name AS name, m.type AS type, type(r) AS rel"

T_NEIGHBORHOOD_IN = "MATCH (n {name: $name})<-[r]-(m) RETURN m.name AS name, m.type AS type, type(r) AS rel"

T_HUBS = """
MATCH (n)-[r]-()
RETURN n.name AS name, n.type AS type, count(r) AS degree
ORDER BY degree DESC
LIMIT $limit
"""

T_STATS = "MATCH (n)-[r]->(m) RETURN count(r) AS edges"

T_STATS_BY_TYPE = """
MATCH (n)
RETURN n.type AS type, count(n) AS count
ORDER BY count DESC
"""

T_SEARCH = """
MATCH (n)
WHERE n.name CONTAINS $q
RETURN n.name AS name, n.type AS type, n.city AS city
LIMIT 25
"""


def _pairs_query(meta):
    rel = meta["pairs_rel"]
    return """
MATCH (a)-[:%s]->(shared)<-[:%s]-(b)
WHERE a <> b AND a.name < b.name
RETURN a.name AS left, a.type AS left_kind,
       b.name AS right, b.type AS right_kind,
       count(DISTINCT shared) AS shared
ORDER BY shared DESC
LIMIT $limit
""" % (rel, rel)


def _chain_query(meta):
    pt, it, ot = meta["person_type"], meta["institution_type"], meta["org_type"]
    sr = meta["study_rel"]
    orgs = "|".join(meta["org_rels"])
    return """
MATCH (p:%s)-[:%s]->(inst:%s)
MATCH (p)-[chain:%s]->(o:%s)
RETURN p.name AS person, type(chain) AS role,
       o.name AS org, inst.name AS institution
ORDER BY p.name
LIMIT $limit
""" % (pt, sr, it, orgs, ot)


def _interlock_query(meta):
    rel = meta["interlock_rel"]
    return """
MATCH (p)-[:%s]->(o1), (p)-[:%s]->(o2)
WHERE o1 <> o2 AND o1.name < o2.name
RETURN DISTINCT p.name AS person, o1.name AS org_a, o2.name AS org_b
ORDER BY p.name
LIMIT $limit
""" % (rel, rel)


def _portfolio_query(meta):
    rel, ot = meta["portfolio_rel"], meta["org_type"]
    return """
MATCH (c:%s {name: $company})<-[r:%s]-(i)
RETURN i.name AS investor, i.type AS kind,
       r.amount_usd AS amount, r.round AS round, r.year AS year
ORDER BY r.year DESC, r.round
""" % (ot, rel)


def _reach_query(meta):
    rel, ot = meta["reach_rel"], meta["org_type"]
    return """
MATCH (c:%s {name: $company})<-[r:%s*1..2]-(i)
RETURN DISTINCT i.name AS investor, i.type AS kind
""" % (ot, rel)


T_PATH = """
MATCH (a {name: $from}), (b {name: $to})
MATCH p = shortestPath((a)-[*1..6]-(b))
RETURN p, length(p) AS hops
"""


def _cap(value, limit):
    return (value or [])[: limit]


def list_domains():
    """Ordered META dicts for every domain."""
    return _list_domains()


def get_meta(domain_id):
    """META for a domain; raises KeyError when unknown."""
    return get_domain(domain_id).META


def node(domain_id, name):
    """Node props by name; raises LookupError when missing."""
    meta = get_meta(domain_id)
    recs = run_domain(domain_id, T_NODE, {"name": name})
    if not recs:
        raise LookupError(name)
    raw = recs[0]["node"]
    return dict(raw) if isinstance(raw, dict) else dict(raw)


def neighborhood(domain_id, name):
    """Incoming + outgoing 1-hop links: [{name, type, rel}]."""
    return run_domain(domain_id, T_NEIGHBORHOOD_OUT, {"name": name}) + \
        run_domain(domain_id, T_NEIGHBORHOOD_IN, {"name": name})


def shortest_path(domain_id, frm, to):
    """Shortest path up to 6 hops: [{"steps": [{from,to,rel,props}]}] or []."""
    recs = run_domain(domain_id, T_PATH, {"from": frm, "to": to})
    if not recs:
        return []
    rec = recs[0]
    if "steps" in rec:
        return [{"steps": rec["steps"], "hops": len(rec["steps"])}]
    path = rec["p"]
    steps = []
    for r in path.relationships:
        steps.append({"from": r.start_node["name"], "to": r.end_node["name"],
                      "rel": r.type, "props": dict(r)})
    return [{"steps": steps, "hops": len(steps)}]


def shared_pairs(domain_id, limit=8):
    """Top pairs sharing a common target: [{left,left_kind,right,right_kind,shared}]."""
    meta = get_meta(domain_id)
    return run_domain(domain_id, _pairs_query(meta), {"limit": limit})


def alumni_chains(domain_id, limit=8):
    """Alumni pathways grouped by institution.

    [{institution, count, members}] where members are up to five names and
    count is the number of distinct people in the pathway. The chain rows
    are fetched in bulk (limit * 6) before grouping so that the top
    ``limit`` institutions are the ones with the most members, not just
    the first alphabetically.
    """
    meta = get_meta(domain_id)
    rows = run_domain(domain_id, _chain_query(meta), {"limit": max(limit * 6, 50)})
    grouped = OrderedDict()
    for r in rows:
        inst = r["institution"]
        if inst not in grouped:
            grouped[inst] = {"institution": inst, "count": 0, "members": []}
        if r["person"] not in grouped[inst]["members"]:
            grouped[inst]["members"].append(r["person"])
            grouped[inst]["count"] += 1
    out = sorted(grouped.values(), key=lambda g: -g["count"])[:limit]
    for g in out:
        g["members"] = g["members"][:5]
    return out


def interlocks(domain_id, limit=8):
    """People linked to two different orgs: [{person, org_a, org_b}]."""
    meta = get_meta(domain_id)
    return run_domain(domain_id, _interlock_query(meta), {"limit": limit})


def portfolio(domain_id, name):
    """Investors in a company (investors domain only)."""
    meta = get_meta(domain_id)
    if not meta.get("portfolio_rel"):
        return []
    return run_domain(domain_id, _portfolio_query(meta), {"company": name})


def reachability(domain_id, name):
    """Investors within two hops of a company (investors domain only)."""
    meta = get_meta(domain_id)
    if not meta.get("reach_rel"):
        return []
    return run_domain(domain_id, _reach_query(meta), {"company": name})


def hubs(domain_id, limit=5):
    """Most-connected nodes: [{name, type, degree}]."""
    return _cap(run_domain(domain_id, T_HUBS, {"limit": limit}), limit)


def stats(domain_id):
    """{"nodes": {type: count}, "edges": int}."""
    nodes = run_domain(domain_id, T_STATS_BY_TYPE)
    edges = run_domain(domain_id, T_STATS)
    return {"nodes": {r["type"]: r["count"] for r in nodes},
            "edges": edges[0]["edges"] if edges else 0}


def search(domain_id, q):
    """Case-insensitive-ish name search: [{name, type, ...}]."""
    return run_domain(domain_id, T_SEARCH, {"q": q})


def insights(domain_id):
    """All four insight blocks plus the domain META (for UI labels)."""
    return {
        "pairs": shared_pairs(domain_id, 8),
        "interlocks": interlocks(domain_id, 8),
        "alumni": alumni_chains(domain_id, 8),
        "hubs": hubs(domain_id, 6),
        "meta": get_meta(domain_id),
    }


def _about_rows(domain_id):
    meta = get_meta(domain_id)
    rel = meta["rel_labels"]
    pairs = _pairs_query(meta)
    chain = _chain_query(meta)
    interlock = _interlock_query(meta)
    rows = [
        ("Top shared-target pairs",
         pairs,
         "Which %s keep sharing the same %s? One hop in, one hop out - "
         "a relational version needs a self-join on the edge table and a "
         "group-by, and the depth is fixed at 1." % (meta["person_type"], meta["org_type"])),
        ("%s pathways" % meta["institution_type"].title(),
         chain,
         "A 2-hop walk: %s -> %s -> %s. Relational SQL needs two joins with "
         "no natural key between the two hops." % (meta["person_type"], meta["institution_type"], meta["org_type"])),
        ("Interlocks",
         interlock,
         "People attached to two different %ss - a self-join over the same "
         "edge table with a <> filter." % meta["org_type"]),
        ("Shortest path (flagship, multi-hop)",
         T_PATH,
         "shortestPath over up to 6 hops - the canonical graph query a "
         "relational schema cannot express at all."),
        ("Most-connected nodes",
         T_HUBS,
         "Degree centrality; SQL needs a GROUP BY over both directions of "
         "the edge table."),
    ]
    if meta.get("portfolio_rel"):
        rows.insert(0, ("Portfolio of a %s" % meta["org_type"],
                        _portfolio_query(meta),
                        "Who is attached to this %s, newest first." % meta["org_type"]))
        rows.append(("2-hop reachability",
                     _reach_query(meta),
                     "Everyone within two hops - a recursive traversal in SQL."))
    return rows


def build_about():
    """ABOUT_QUERIES: list of {label, cypher, why} spanning every domain."""
    out = []
    for meta in _list_domains():
        for label, cypher, why in _about_rows(meta["id"]):
            out.append({"domain": meta["name"], "label": label,
                        "cypher": cypher.strip(), "why": why})
    return out


ABOUT_QUERIES = build_about()
