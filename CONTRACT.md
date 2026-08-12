# CONTRACT.md — multi-domain refactor of the CognoDB assignment app

Single source of truth for the parallel refactor. **Do not deviate from these
interfaces.** All agents must read this file first.

## Goal

One graph app, three domains: `investors` (existing dataset, keep byte-for-byte
semantics), `education` (alumni/mentorship), `healthcare` (care networks).
Shared engine: FastAPI + `neo4j` driver (live CognoDB) + MockDriver (no DB).

## File ownership (NO file overlaps between agents)

- Agent A: `app/domains/investors.py`, `app/domains/education.py`,
  `app/domains/healthcare.py`, `app/seed.py`; DELETE `app/seed_data.py`.
- Agent B: `app/domains/__init__.py` (registry), `app/queries.py`, `app/db.py`.
- Agent C: `static/index.html`, `static/app.js`, `static/style.css`, `main.py`.
- Agent D: `README.md`, `Dockerfile`, `render.yaml`, `.env.example`,
  `scripts/screenshots.sh`, `SUBMISSION_EMAIL.md`.

## Dataset format (unchanged)

- Node: `{"name": str, "type": str, ...props}`
- Edge: `{"from": (type, name), "to": (type, name), "rel": str, ...props}`
- Every domain module exports `def build_dataset()` returning
  `{"nodes": [...], "edges": [...], "meta": <META>}`.

## META (per-domain config, exported as `META` dict in each domain module)

```python
META = {
  "id": "investors",                # url-safe slug
  "name": "Startup & Investor Network",
  "tagline": "Co-investors, board interlocks, alumni in Indian startups",
  "accent": "#E04F2F",              # UI accent color for this domain's tab
  "node_labels": {"company": "Company", "person": "Person", ...},  # type -> display
  "rel_labels": {"FOUNDED": "founded", ...},                       # rel  -> verb
  "person_type": "person",
  "institution_type": "university", # the 'school' node type
  "org_type": "company",
  "pairs_rel": "INVESTED_IN",       # shared-target rel for top co-<x> pairs
  "study_rel": "STUDIED_AT",        # person -> institution rel
  "org_rels": ["FOUNDED", "WORKS_AT", "BOARD_MEMBER"],  # person -> org rels
  "interlock_rel": "BOARD_MEMBER",  # person connected to 2+ orgs of this rel
  "portfolio_rel": "INVESTED_IN",   # org -> org rel, or None
  "reach_rel": "INVESTED_IN",       # multi-hop rel, or None
  "sample_searches": ["PayKart", "Ananya Rao"],   # for UI placeholder
}
```

Domain key mappings (used in the alumni-chain and pairs queries):
- investors:    pairs=INVESTED_IN, study=STUDIED_AT, org_rels=[FOUNDED, WORKS_AT,
  BOARD_MEMBER], interlock=BOARD_MEMBER, portfolio=INVESTED_IN, reach=INVESTED_IN,
  person=person, institution=university, org=company
- education:    pairs=STUDIED_AT (co-alumni of a university), study=STUDIED_AT,
  org_rels=[PLACED_AT, INTERNSHIP_AT, WORKS_AT], interlock=ADVISES_AT (mentor
  advises 2+ colleges; rel target = institution), portfolio=None, reach=None,
  person=student, institution=university, org=company
- healthcare:   pairs=ATTENDED_BY (doctors sharing a patient), study=SPECIALIZES_IN
  (doctor -> department), org_rels=[WORKS_AT], interlock=WORKS_AT (doctor works at
  2+ hospitals), portfolio=None, reach=None, person=doctor, institution=department,
  org=hospital

Education extra node types: student, mentor, university, company, course.
Rel types: STUDIED_AT (student->university), PLACED_AT (student->company),
INTERNSHIP_AT (student->company), WORKS_AT (mentor->company), MENTORED_BY
(mentor->student, to=student), ADVISES_AT (mentor->university), KNOWS (student->student).

Healthcare node types: doctor, patient, hospital, department, condition.
Rel types: WORKS_AT (doctor->hospital), SPECIALIZES_IN (doctor->department),
TREATS (doctor->patient), DIAGNOSED_WITH (patient->condition), ATTENDED_BY
(patient->doctor), REFERRED_TO (doctor->doctor), VISITED (patient->hospital).

Dataset sizes: each domain 35-55 nodes, 70-120 edges, realistic Indian names,
varied props (degrees/years for education; specializations/salary bands for
healthcare; existing investor data unchanged).

## queries.py public API (Agent B must export these)

All functions take `domain_id` first. Field names are FIXED - Agent C depends on them.

- `list_domains()` -> [META, ...] (ordered investors, education, healthcare)
- `get_meta(domain_id)` -> META
- `node(domain_id, name)` -> dict props (raises LookupError if missing)
- `neighborhood(domain_id, name)` -> [{"name","type","rel","props"}]
- `shortest_path(domain_id, frm, to)` -> [{"steps": [{"from","to","rel","props"}]}]
  or [] when no path (<=6 hops)
- `stats(domain_id)` -> {"nodes": {type: count}, "edges": int}
- `search(domain_id, q)` -> [{"name","type","...first props"}]
- `hubs(domain_id, limit)` -> [{"name","type","degree"}]
- `shared_pairs(domain_id, limit)` -> [{"left","left_kind","right","right_kind","shared"}]
- `alumni_chains(domain_id, limit)` -> [{"person","role","org","institution"}]
- `interlocks(domain_id, limit)` -> [{"person","org_a","org_b"}]
- `portfolio(domain_id, name)` -> [{"investor","kind","...edge props"}] (investors only)
- `reachability(domain_id, name)` -> [{"investor","kind"}] (investors only)
- `insights(domain_id)` -> {"pairs", "interlocks", "alumni": [{"institution","count","members":[...]}], "hubs"}
- `ABOUT_QUERIES` -> [{"label","cypher","why"}...] (3+ per domain, incl. >=1 multi-hop, >=1 relational-awkward)

Cypher templates: SAME aliases across domains (a/b for pairs, p for chain person,
o1/o2 for interlocks). Rel names come from META (whitelist - never from user input).
All values via $params. Use `RETURN a.name AS left` (lowercase aliases) so the
MockDriver's shape routing stays stable.

## db.py MockDriver (Agent B)

Constructor: `MockDriver(dataset)` where dataset = {"nodes": [...], "edges": [...], "meta": META}.
Keep existing shape routing; make rel-specific handlers read the rel names from the
QUERY ITSELF (regex `\[:([A-Z_|]+)\]`) and the roles from `dataset["meta"]`. Do NOT
hardcode rel names inside the mock. Keep `run()`, `execute_query()`, DBError, mode(),
db_up() signatures. Live driver path unchanged. `seed.py` seeds ALL domains.

## main.py API (Agent C)

Every data endpoint gains optional `domain: str = Query("investors")` validated
against `queries.list_domains()` (400 on unknown). New endpoint `GET /api/domains`
-> {"domains": [META...]}. `/api/insights` takes `?domain=`. `/api/portfolio` and
`/api/reach` return `{"supported": false, "detail": "..."}` when the domain's
portfolio_rel/reach_rel is None. `/health` unchanged. 404 JSON `{"detail": "node not found"}`,
503 JSON on DBError, keep the same JSON error envelope everywhere.
REL_SUMMARY replaced by domain rel_labels from META (step_caption uses them).

## static/ UI (Agent C)

Keep the existing design system (navy #1B2A4A / vermilion accent / hairline cards,
no emoji, system font stack). Add a domain tab bar (3 tabs from /api/domains, accent
color per domain). All copy rendered from META labels. Views (same as today): search,
node card, neighborhood SVG (2 hops), path search, insights blocks (pairs, interlocks,
alumni, hubs), stats. Explicit loading spinners, empty states, and error banner when
an API call fails (503 -> "Database unreachable" banner). No hardcoded "PayKart"/"IIT
Delhi" strings - use meta.sample_searches and insights payloads.

## Verification

`python -m compileall app` then run with `MOCK_DB=1` and exercise every endpoint for
every domain via curl. All 3 domains must return realistic data.

## Git / commit

One commit per logical change, conventional messages, repo-local git identity
`Vishnu Vardhan <vishnuvardhanthe8055@gmail.com>`. Do NOT commit .env, .venv,
__pycache__, screenshots/, uvicorn.log.
