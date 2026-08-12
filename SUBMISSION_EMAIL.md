Subject: CognoDB Assignment 2 - Vishnu Vardhan

Hi Wexa AI team,

I am applying for the role and am submitting my CognoDB assignment. The
repository is live at https://github.com/Rythamo8055/cognodb-graphlink.

What I built: GraphLink - three networks on one graph engine. A single
FastAPI application backed by a CognoDB instance covers three domains:
a startup and investor network (co-investor pairs, board interlocks, alumni
pipelines), an alumni and mentorship network, and a healthcare care network
(shared-patient doctor pairs, referrals). All three share one query engine,
one parameterised Cypher suite, and one clean web UI that a non-technical
person can use.

Why a graph: every question the app answers is about connections and
multi-hop traversals (shared pairs, alumni chains, shortest paths,
reachability) - queries that become recursive CTEs and repeated self-joins
in relational SQL. The data model, setup steps, query reference, and
screenshots are all documented in the README.

How to run it:
- Live demo: <DEMO_URL - hosted on Render, link sent once the instance is
  created and the database is seeded>
- Screen recording: https://github.com/Rythamo8055/cognodb-graphlink/blob/main/out.mp4
  (also included in the repository root)
- Local setup is documented in the README (create a free c0 instance at
  console.cognodb.com, cp .env.example .env, python -m app.seed, then
  uvicorn main:app --port 8000). The app also runs without a database via
  MOCK_DB=1.

The CognoDB instance is live and seeded with realistic data for all three
domains, and I will keep it running so you can explore the demo. I am happy
to walk through the code or the deployment setup in a call.

Thanks for your time.

Best regards,
Vishnu Vardhan
