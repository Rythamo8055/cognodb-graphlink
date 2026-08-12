"""Seed the graph database - constraints, then nodes, then relationships,
for all three domains (investors, education, healthcare).

Nodes MERGE on their (name, type) pair and relationships MERGE on their
(from, to, rel) triple, so repeated runs are safe and cross-domain name
repeats collapse onto the same node. Relationship types come from each
domain's rel_labels whitelist - never from user input.

Every statement ends in an explicit RETURN. CognoDB sends result records
even for writes that do not name a RETURN column, and the Bolt driver
rejects records whose keys and values differ in length - so write
statements must always project what they wrote.

Refuses to run when MOCK_DB is set or no COGNODB_URI is configured.

Usage:
  python -m app.seed
"""
import os

from dotenv import load_dotenv
from neo4j import GraphDatabase

from .domains.education import build_dataset as build_education_dataset
from .domains.healthcare import build_dataset as build_healthcare_dataset
from .domains.investors import build_dataset as build_investors_dataset

load_dotenv()

URI = os.environ.get("COGNODB_URI") or os.environ.get("NEO4J_URI", "")
USER = os.environ.get("COGNODB_USERNAME") or os.environ.get("NEO4J_USERNAME", "cognodb")
PASSWORD = os.environ.get("COGNODB_PASSWORD") or os.environ.get("NEO4J_PASSWORD", "")
MOCK = os.environ.get("MOCK_DB", "0") == "1" or not URI

DOMAIN_BUILDERS = [
    ("investors", build_investors_dataset),
    ("education", build_education_dataset),
    ("healthcare", build_healthcare_dataset),
]


def create_constraints(driver):
    seen = set()
    for _, builder in DOMAIN_BUILDERS:
        for label in builder()["meta"]["node_labels"].values():
            if label in seen:
                continue
            seen.add(label)
            constraint = "constraint_%s_name" % label.lower()
            query = (
                "CREATE CONSTRAINT %s IF NOT EXISTS "
                "FOR (n:%s) REQUIRE n.name IS UNIQUE" % (constraint, label)
            )
            driver.execute_query(query)
    print("constraints ensured")


def seed_domain(driver, name, dataset):
    nodes = dataset["nodes"]
    edges = dataset["edges"]
    meta = dataset["meta"]

    by_label = {}
    for n in nodes:
        by_label.setdefault(meta["node_labels"][n["type"]], []).append(n)
    for label, rows in by_label.items():
        query = (
            "UNWIND $rows AS row "
            "MERGE (n:%s {name: row.name, type: row.type}) "
            "ON CREATE SET n += row "
            "ON MATCH SET n += row "
            "RETURN n.name AS name" % label
        )
        driver.execute_query(query, rows=rows)
        print("  nodes: %s -> %d" % (label, len(rows)))

    for e in edges:
        rel = e["rel"]
        if rel not in meta["rel_labels"]:
            raise ValueError("refusing non-whitelisted relationship type: %r" % rel)
        src_label = meta["node_labels"][e["from"][0]]
        dst_label = meta["node_labels"][e["to"][0]]
        query = (
            "MATCH (a:%s {name: $src}), (b:%s {name: $dst}) "
            "MERGE (a)-[r:%s]->(b) "
            "ON CREATE SET r += $props "
            "ON MATCH SET r += $props "
            "RETURN r" % (src_label, dst_label, rel)
        )
        props = {k: v for k, v in e.items() if k not in ("from", "to", "rel")}
        driver.execute_query(query, src=e["from"][1], dst=e["to"][1], props=props)
    print("  %s: %d nodes, %d relationships" % (name, len(nodes), len(edges)))


def main():
    if MOCK:
        raise SystemExit("MOCK_DB is set / no COGNODB_URI - refusing to seed a mock. "
                         "Set COGNODB_URI and COGNODB_PASSWORD first.")
    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    try:
        create_constraints(driver)
        print("seeding...")
        for name, builder in DOMAIN_BUILDERS:
            print("domain: %s" % name)
            seed_domain(driver, name, builder())
    finally:
        driver.close()
    print("done")


if __name__ == "__main__":
    main()
