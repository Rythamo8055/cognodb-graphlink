"""GraphLink - three networks, one graph engine.

FastAPI app backed by CognoDB (openCypher over Bolt) serving three domains
(investors, education, healthcare) from a single query layer in
app/queries.py. Every data view maps to a fixed, parameterised query -
there is no free-form query input, so no query injection surface. If the
database is unreachable the API returns 503 JSON and the UI shows a
friendly banner instead of crashing.

Every data endpoint accepts ?domain= and validates it against the domain
registry in app/queries.py; unknown domains get a 400. Domains whose META
has no portfolio or reach relationship report {"supported": false} instead
of failing. /api/insights returns the domain META alongside the blocks so
the UI can label every block from the API payloads.

Run locally:
  pip install -r requirements.txt
  python -m app.seed             # once, after creating a CognoDB instance
  uvicorn main:app --port 8000   # or: MOCK_DB=1 to explore without a DB
                                 # (MOCK_DB=1 uses an in-memory dataset)
"""
import json
import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from app import db, graphrag, queries

load_dotenv()

app = FastAPI(title="GraphLink", version="2.0.0")

HERE = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(HERE, "static")

app.mount("/static", StaticFiles(directory=STATIC), name="static")


def get_meta(domain: str) -> dict:
    """Validate a domain id against the registry, 400 on unknown."""
    try:
        return queries.get_meta(domain)
    except KeyError:
        raise HTTPException(status_code=400, detail="unknown domain")


def money(v):
    """Format a USD amount: 1.5M, 250K, or the raw value."""
    try:
        v = int(v)
    except (TypeError, ValueError):
        return str(v)
    if v >= 1_000_000:
        return "$%.1fM" % (v / 1_000_000)
    if v >= 1_000:
        return "$%.0fK" % (v / 1_000)
    return "$%d" % v


def step_caption(step, rel_labels):
    """Render one path step as 'From verb To (props)' using META verbs."""
    props = step.get("props") or {}
    bits = []
    if "role" in props:
        bits.append(str(props["role"]))
    if "title" in props:
        bits.append(str(props["title"]))
    if "degree" in props:
        bits.append(str(props["degree"]))
    if "amount_usd" in props:
        bits.append(money(props["amount_usd"]))
    if "round" in props:
        bits.append(str(props["round"]).replace("_", " ").title())
    if "year" in props:
        bits.append(str(props["year"]))
    rel = step["rel"]
    verb = rel_labels.get(rel, rel.lower().replace("_", " "))
    caption = "%s %s %s" % (step["from"], verb, step["to"])
    if bits:
        caption += " (%s)" % ", ".join(bits)
    return caption


@app.get("/")
def index():
    return FileResponse(os.path.join(STATIC, "index.html"))


def _hood(name, hops, domain):
    """BFS neighborhood of a node, mirroring /api/neighborhood."""
    nodes = {name: {"name": name, "type": "", "hop": 0}}
    edges = []
    frontier = [name]
    for hop in range(1, hops + 1):
        nxt = []
        for cur in frontier:
            for link in queries.neighborhood(domain, cur):
                tgt = link["name"]
                if tgt not in nodes:
                    nodes[tgt] = {"name": tgt, "type": link["type"], "hop": hop}
                    nxt.append(tgt)
                edges.append({"from": cur, "to": tgt, "rel": link["rel"]})
        frontier = nxt
        if len(nodes) >= 100:
            break
    nodes[name]["type"] = queries.node(domain, name).get("type", "")
    return {"nodes": list(nodes.values()), "edges": edges}


@app.get("/snap", include_in_schema=False)
def snap(domain: str = Query("investors"), view: str = Query("home"),
         node: str = Query(""), frm: str = Query(None, alias="from"),
         to: str = Query(None), q: str = Query("")):
    """Server-rendered page snapshot for deterministic screenshots.

    Serves the same UI with all data inlined as window.__SNAP__ so the
    page is fully rendered by the time the load event fires. Used by
    scripts/screenshots.sh; harmless for regular browsing.
    """
    try:
        meta = queries.get_meta(domain)
        payload = {"domains": queries.list_domains(),
                   "view": {"kind": "home", "domain": domain}}
        if view == "node" and node:
            props = queries.node(domain, node)
            links = queries.neighborhood(domain, node)
            payload["view"] = {"kind": "node", "domain": domain, "node": node,
                               "props": props, "links": links,
                               "hood": _hood(node, 2, domain)}
        elif view == "path" and frm and to:
            recs = queries.shortest_path(domain, frm, to)
            payload["view"] = {"kind": "path", "domain": domain, "from": frm,
                               "to": to, "found": bool(recs),
                               "steps": recs[0]["steps"] if recs else []}
        elif view == "ask" and q:
            res = graphrag.answer(domain, q)
            payload["view"] = {"kind": "ask", "question": q, **res}
        else:
            payload["view"]["stats"] = queries.stats(domain)
            payload["view"]["insights"] = queries.insights(domain)
        snap_script = "<script>window.__SNAP__ = %s;</script>" % json.dumps(payload)
        html = open(os.path.join(STATIC, "index.html")).read()
        html = html.replace('<script src="/static/app.js">',
                            snap_script + '<script src="/static/app.js">')
        return HTMLResponse(html)
    except LookupError:
        raise HTTPException(status_code=404, detail="node not found")
    except db.DBError as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/health")
def health():
    return {"status": "ok", "db": db.db_up(), "mode": db.mode()}


@app.get("/api/domains")
def api_domains():
    try:
        return {"domains": queries.list_domains()}
    except db.DBError as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/api/stats")
def api_stats(domain: str = Query("investors")):
    get_meta(domain)
    try:
        return queries.stats(domain)
    except db.DBError as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/api/search")
def api_search(q: str = Query(..., min_length=1), domain: str = Query("investors")):
    get_meta(domain)
    try:
        return {"results": queries.search(domain, q.strip())}
    except db.DBError as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/api/ask")
def api_ask(q: str = Query(..., min_length=1), domain: str = Query("investors")):
    get_meta(domain)
    q = q.strip()
    if not q:
        raise HTTPException(status_code=400, detail="empty question")
    try:
        return graphrag.answer(domain, q)
    except LookupError:
        raise HTTPException(status_code=404, detail="node not found")
    except db.DBError as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/api/node")
def api_node(name: str, domain: str = Query("investors")):
    get_meta(domain)
    try:
        props = queries.node(domain, name)
    except LookupError:
        raise HTTPException(status_code=404, detail="node not found")
    except db.DBError as e:
        raise HTTPException(status_code=503, detail=str(e))
    try:
        links = queries.neighborhood(domain, name)
    except db.DBError as e:
        raise HTTPException(status_code=503, detail=str(e))
    return {"props": props, "links": links}


@app.get("/api/neighborhood")
def api_neighborhood(name: str, hops: int = Query(2, ge=1, le=4),
                     domain: str = Query("investors")):
    get_meta(domain)
    try:
        start = queries.node(domain, name)
    except LookupError:
        raise HTTPException(status_code=404, detail="node not found")
    except db.DBError as e:
        raise HTTPException(status_code=503, detail=str(e))
    try:
        nodes = {name: {"name": name, "type": start.get("type", ""), "hop": 0}}
        edges = []
        frontier = [name]
        for hop in range(1, hops + 1):
            nxt = []
            for cur in frontier:
                for link in queries.neighborhood(domain, cur):
                    tgt = link["name"]
                    if tgt not in nodes:
                        nodes[tgt] = {"name": tgt, "type": link["type"], "hop": hop}
                        nxt.append(tgt)
                    edges.append({"from": cur, "to": tgt, "rel": link["rel"]})
            frontier = nxt
            if len(nodes) >= 100:
                break
        return {"nodes": list(nodes.values()), "edges": edges}
    except db.DBError as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/api/path")
def api_path(frm: str = Query(..., alias="from"), to: str = Query(...),
             domain: str = Query("investors")):
    meta = get_meta(domain)
    rel_labels = meta.get("rel_labels", {})
    try:
        recs = queries.shortest_path(domain, frm, to)
        if not recs:
            return {"found": False, "error": "no path up to 6 hops"}
        rec = recs[0]
        if "steps" in rec:
            steps = rec["steps"]
        else:
            path = rec["p"]
            steps = []
            for r in path.relationships:
                s, e = r.start_node["name"], r.end_node["name"]
                steps.append({"from": s, "to": e, "rel": r.type, "props": dict(r)})
        return {"found": True, "hops": len(steps),
                "steps": steps, "captions": [step_caption(s, rel_labels) for s in steps]}
    except db.DBError as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/api/insights")
def api_insights(domain: str = Query("investors")):
    meta = get_meta(domain)
    try:
        return {
            "pairs": queries.shared_pairs(domain, 8),
            "interlocks": queries.interlocks(domain, 8),
            "alumni": queries.alumni_chains(domain, 8),
            "hubs": queries.hubs(domain, 6),
            "meta": meta,
        }
    except db.DBError as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/api/portfolio")
def api_portfolio(name: str, domain: str = Query("investors")):
    meta = get_meta(domain)
    if not meta.get("portfolio_rel"):
        return {"supported": False, "detail": "not available for this domain"}
    try:
        return queries.portfolio(domain, name)
    except db.DBError as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/api/reach")
def api_reach(name: str, domain: str = Query("investors")):
    meta = get_meta(domain)
    if not meta.get("reach_rel"):
        return {"supported": False, "detail": "not available for this domain"}
    try:
        return queries.reachability(domain, name)
    except db.DBError as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/api/about")
def api_about(domain: str = Query("investors")):
    get_meta(domain)
    try:
        return {"queries": queries.ABOUT_QUERIES}
    except db.DBError as e:
        raise HTTPException(status_code=503, detail=str(e))
