"""Graph database access layer.

Talks to CognoDB over Bolt using the official Neo4j Python driver.
All queries in this project are parameterised - the only thing that is
ever interpolated into a query string is a relationship TYPE from a
hard-coded whitelist (relationship types cannot be parameters in Cypher).

Set MOCK_DB=1 (or omit credentials) to run against in-memory sample
datasets so the UI can be explored without a live database. The mock
builds the exact same dataset the seeder loads (per domain), so mock and
live behaviour stay provably identical.
"""
import os
import re
from collections import deque
from contextlib import contextmanager

from dotenv import load_dotenv

load_dotenv()

URI = os.environ.get("COGNODB_URI") or os.environ.get("NEO4J_URI", "")
USER = os.environ.get("COGNODB_USERNAME") or os.environ.get("NEO4J_USERNAME", "cognodb")
PASSWORD = os.environ.get("COGNODB_PASSWORD") or os.environ.get("NEO4J_PASSWORD", "")
MOCK = os.environ.get("MOCK_DB", "0") == "1" or not URI

_driver = None
_mock_drivers = {}


class DBError(Exception):
    """Raised when the graph database is unreachable."""


def mode():
    return "mock" if MOCK else "live"


def get_driver():
    global _driver
    if MOCK:
        raise DBError("mock mode: call run_domain()")
    if _driver is None:
        from neo4j import GraphDatabase
        _driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    return _driver


def db_up():
    try:
        if MOCK:
            return True
        get_driver().verify_connectivity()
        return True
    except Exception:
        return False


@contextmanager
def session():
    try:
        driver = get_driver()
    except Exception as e:
        raise DBError("graph database unreachable: %s" % e)
    yield driver


def run(query, params=None, default=None):
    """Execute a read query; return list of dict records. On DB failure return default."""
    try:
        with session() as driver:
            recs, _, _ = driver.execute_query(query, parameters_=params)
            return [dict(r) for r in recs]
    except DBError:
        return default if default is not None else []


def run_domain(domain_id, query, params=None, default=None):
    """Execute a read query against one domain (mock or live).

    In mock mode this runs against the in-memory dataset for the domain;
    live mode behaves exactly like run().
    """
    try:
        if MOCK:
            driver = _mock_drivers.get(domain_id)
            if driver is None:
                from .domains import get_dataset
                driver = MockDriver(get_dataset(domain_id))
                _mock_drivers[domain_id] = driver
            recs, _, _ = driver.execute_query(query, parameters_=params)
            return [dict(r) for r in recs]
        with session() as driver:
            recs, _, _ = driver.execute_query(query, parameters_=params)
            return [dict(r) for r in recs]
    except DBError:
        return default if default is not None else []


REL_TOKEN = re.compile(r"\[:([A-Z_|]+)\]")


def _rels_in(query):
    """Relationship types referenced in a query string (whitelisted tokens)."""
    toks = set()
    for m in REL_TOKEN.finditer(query):
        toks.update(m.group(1).split("|"))
    return toks


class MockDriver:
    """In-memory graph for one domain dataset.

    Routes on query shape (shortestPath, search, node lookup, stats, hubs)
    and on the relationship types extracted from the query for the
    domain-specific shapes (pairs, pathways, interlocks, portfolio,
    reachability). No relationship name is hardcoded here - every role is
    looked up in the dataset's META.
    """

    def __init__(self, dataset):
        self.meta = dataset["meta"]
        self.nodes = {v["name"].lower(): dict(v) for v in dataset["nodes"]}
        self.edges = [dict(e) for e in dataset["edges"]]
        self.person_type = self.meta["person_type"]
        self.org_type = self.meta["org_type"]

    def _node(self, name):
        return self.nodes.get((name or "").strip().lower())

    def _link(self, r):
        props = {k: v for k, v in r.items() if k not in ("from", "to", "rel")}
        return {"name": r["to"][1], "type": r["to"][0], "rel": r["rel"], "props": props}

    def execute_query(self, query, parameters_=None, database_=None):
        q = " ".join(query.split())
        ql = q.lower()
        p = parameters_ or {}
        n = self._node(p.get("name", ""))
        rels = _rels_in(query)

        if "count(r) as edges" in ql:
            return ([{"edges": len(self.edges)}], None, None)
        if "return n.type as type, count(n)" in ql:
            counts = {}
            for v in self.nodes.values():
                counts[v["type"]] = counts.get(v["type"], 0) + 1
            return ([{"type": k, "count": v} for k, v in counts.items()], None, None)
        if "return n as node" in ql:
            node = self._node(p.get("name", ""))
            return ([{"node": dict(node)}] if node else [], None, None)
        if "contains" in ql:
            needle = (p.get("q") or "").lower()
            out = [{"name": v["name"], "type": v["type"], "city": v.get("city", "")}
                   for v in self.nodes.values() if needle in v["name"].lower()]
            return (out[:25], None, None)
        if "shortestpath" in ql:
            a, b = (p.get("from") or "").lower(), (p.get("to") or "").lower()
            if a not in self.nodes or b not in self.nodes:
                return ([], None, None)
            prev = {a: None}
            dq = deque([a])
            while dq:
                cur = dq.popleft()
                if cur == b:
                    break
                for r in self.edges:
                    for src, dst in ((r["from"][1].lower(), r["to"][1].lower()),
                                     (r["to"][1].lower(), r["from"][1].lower())):
                        if src == cur and dst not in prev:
                            prev[dst] = (cur, r)
                            dq.append(dst)
            if b not in prev:
                return ([], None, None)
            steps, cur = [], b
            while prev[cur] is not None:
                came, r = prev[cur]
                if r["from"][1].lower() == came:
                    steps.append({"from": r["from"][1], "rel": r["rel"],
                                  "to": r["to"][1],
                                  "props": {k: v for k, v in r.items()
                                            if k not in ("from", "to", "rel")}})
                else:
                    steps.append({"from": r["to"][1], "rel": r["rel"],
                                  "to": r["from"][1],
                                  "props": {k: v for k, v in r.items()
                                            if k not in ("from", "to", "rel")}})
                cur = came
            steps.reverse()
            return ([{"steps": steps, "hops": len(steps)}], None, None)
        if "count(distinct shared)" in ql:  # shared-target pairs
            rel = next(iter(rels), self.meta["pairs_rel"])
            pairs = {}
            for r1 in self.edges:
                if r1["rel"] != rel:
                    continue
                for r2 in self.edges:
                    if r2["rel"] != rel:
                        continue
                    if r1["to"] == r2["to"] and r1["from"] != r2["from"]:
                        key = tuple(sorted([r1["from"][1], r2["from"][1]]))
                        pairs[key] = pairs.get(key, 0) + 1
            out = [{"left": a, "left_kind": self._node(a)["type"],
                    "right": b, "right_kind": self._node(b)["type"], "shared": c}
                   for (a, b), c in sorted(pairs.items(), key=lambda x: -x[1])
                   [: p.get("limit", 8)]]
            return (out, None, None)
        if "as institution" in ql:  # alumni pathways: person->institution + person->org
            study, orgs = self.meta["study_rel"], set(self.meta["org_rels"])
            out = []
            for r1 in self.edges:
                if r1["rel"] != study:
                    continue
                person = r1["from"][1].lower()
                for r2 in self.edges:
                    if r2["rel"] not in orgs or r2["from"][1].lower() != person:
                        continue
                    out.append({"person": r1["from"][1], "role": r2["rel"],
                                "org": r2["to"][1], "institution": r1["to"][1]})
            out.sort(key=lambda x: (x["institution"], x["person"]))
            return (out[: p.get("limit", 8)], None, None)
        if "as org_b" in ql:  # interlocks: person linked to two different orgs
            rel = self.meta["interlock_rel"]
            seen, out = set(), []
            for r1 in self.edges:
                if r1["rel"] != rel:
                    continue
                for r2 in self.edges:
                    if r2["rel"] != rel or r2["from"] != r1["from"] or r2["to"] == r1["to"]:
                        continue
                    lo, hi = sorted([r1["to"][1], r2["to"][1]])
                    key = (r1["from"][1], lo, hi)
                    if key in seen:
                        continue
                    seen.add(key)
                    out.append({"person": r1["from"][1], "org_a": lo, "org_b": hi})
            return (out[: p.get("limit", 8)], None, None)
        if "as investor" in ql:  # portfolio: everyone attached to this org
            rel = self.meta["portfolio_rel"] or self.meta["pairs_rel"]
            org = (p.get("company") or "").lower()
            out = []
            for r in self.edges:
                if r["rel"] != rel or r["to"][1].lower() != org:
                    continue
                props = {k: v for k, v in r.items() if k not in ("from", "to", "rel")}
                out.append({"investor": r["from"][1], "kind": r["from"][0], **props})
            out.sort(key=lambda x: (-x.get("year", 0)))
            return (out, None, None)
        if "*1..2]" in ql:  # reachability: within two hops of an org
            rel = self.meta["reach_rel"] or self.meta["pairs_rel"]
            org = (p.get("company") or "").lower()
            out, seen, frontier = [], set(), {org}
            for _ in range(2):
                nxt = set()
                for cur in frontier:
                    for r in self.edges:
                        if r["rel"] != rel:
                            continue
                        if r["to"][1].lower() == cur and r["from"][1].lower() not in seen:
                            seen.add(r["from"][1].lower())
                            out.append({"investor": r["from"][1], "kind": r["from"][0]})
                            nxt.add(r["from"][1].lower())
                frontier = nxt
            return (out, None, None)
        if "order by degree desc" in ql:
            deg = {}
            for r in self.edges:
                for name in (r["from"][1].lower(), r["to"][1].lower()):
                    v = self.nodes[name]
                    deg.setdefault(v["name"], {"name": v["name"], "type": v["type"], "degree": 0})
                    deg[v["name"]]["degree"] += 1
            out = sorted(deg.values(), key=lambda x: -x["degree"])[: p.get("limit", 5)]
            return (out, None, None)
        if "-[r" in ql:  # generic 1-hop links (outgoing + incoming)
            incoming = "<-[r]" in ql
            out = []
            for r in self.edges:
                if r["from"][1].lower() == p.get("name", "").lower():
                    if not incoming:
                        link = self._link(r)
                        link["incoming"] = False
                        out.append(link)
                elif r["to"][1].lower() == p.get("name", "").lower():
                    if incoming:
                        out.append({"name": r["from"][1], "type": r["from"][0],
                                    "rel": r["rel"], "incoming": True,
                                    "props": {k: v for k, v in r.items()
                                              if k not in ("from", "to", "rel")}})
            return (out, None, None)
        raise ValueError("mock: unhandled query: %s" % q[:80])
