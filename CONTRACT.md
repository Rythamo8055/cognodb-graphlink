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

## GraphRAG layer (phase 2) - "Ask" view

Single source of truth for the GraphRAG upgrade. Do not deviate.

### Contract: GET /api/ask?q=<question>&domain=<id>

200 OK:
```json
{
  "question": "Who invested in PayKart?",
  "domain": "investors",
  "intent": "portfolio",                  // one of: portfolio pairs interlocks alumni reach path hubs neighborhood
  "entities": [{"name": "PayKart", "type": "company"}],  // grounded in graph, max 4
  "unmatched": [],                        // entity names found by LLM parse but absent from graph
  "facts": [{"from": "Acme Capital", "rel": "INVESTED_IN", "to": "PayKart", "props": {"amount_usd": 1200000, "round": "SERIES_A", "year": 2021}}],
  "subgraph": {"nodes": [{"name": "PayKart", "type": "company", "hop": 0}],
               "edges": [{"from": "Acme Capital", "to": "PayKart", "rel": "INVESTED_IN"}]},
  "answer": "PayKart raised its Series A led by Acme Capital in 2021...",
  "source": "llm"                         // "llm" | "retrieval"
}
```
- 400 on unknown domain or empty/short q; 503 on db.DBError (existing patterns).
- `facts[].rel` is the RAW relationship type (e.g. INVESTED_IN); the UI renders verbs
  via the existing meta.rel_labels map (app.js `verb()`).
- `subgraph` has the same shape as /api/neighborhood so the existing SVG renderer
  can paint it unchanged.

### Pipeline (app/graphrag.py, pure Python, no new deps beyond google-genai)

1. Parse: LLM returns strict JSON {"intent": str, "entities": [str]} - intent MUST be
   from the whitelist above. No key / bad JSON / network error -> heuristic fallback:
   intent keyword rules + entity grounding via queries.search() exact/substring match.
2. Retrieve: SWITCH on intent, run ONLY existing parameterised functions from
   app/queries.py (portfolio, shared_pairs, interlocks, alumni_chains, reachability,
   hubs, shortest_path, node, neighborhood, search). NEVER generate Cypher from the
   question. Unsupported intent for a domain (portfolio/reach only exist on
   investors) -> neighborhood fallback. Facts capped at 40, subgraph nodes at ~60.
3. Answer: LLM (google-genai, model gemini-2.5-flash, env GEMINI_API_KEY/GOOGLE_API_KEY)
   prompted: answer ONLY from the given facts, 2-4 sentences, cite entity names,
   else say exactly "The graph doesn't contain that information." Fallback (no key):
   template from top 5 facts, source="retrieval".

### main.py
- Add GET /api/ask (validates domain + q).
- Extend /snap with view=ask&q=... inlining the same payload as window.__SNAP__
  with view {"kind": "ask", ...} so screenshots are deterministic.

### UI (static files, Ask view)
- Third button in .view-toggle: "Ask" (id btn-ask), switchView("ask") follows the
  exact existing pattern (btn-explore/btn-path at app.js:589).
- Layout: question input + submit + example chips; below: answer card with source
  badge ("graph-grounded LLM" / "retrieval"), entity chips, collapsible "Evidence"
  details (fact rows "A --verb--> B (props)" reusing verb()/money() helpers), and
  the subgraph painted with the existing neighborhood SVG renderer.
- States: initial hint text, loading spinner, inline error, 503 handled by the
  existing global banner. Empty facts -> "The graph doesn't contain that information."
- Example questions (investors): "Who invested in PayKart?", "How is Divya Menon
  connected to Ananya Rao?", "Which two investors co-invest?", "Who sits on two
  boards?", "Who is the most connected investor?"

### Deliverables after merge
- requirements.txt: add google-genai>=1.0.0
- screenshots.sh: add shot screenshot-ask "/snap?domain=investors&view=ask&q=Who%20invested%20in%20PayKart%3F"
  and update the video concat to 6 inputs.
- README: GraphRAG section (pipeline, why grounded answers, GEMINI_API_KEY optional),
  /api/ask row in the API table, new screenshot, update recording section.
- SUBMISSION_EMAIL.md: mention the GraphRAG Ask view.
