"""The investors domain - the DealGraph dataset, a fictional but realistic
Indian startup funding network: 46 nodes, ~115 relationships.

Every entity has a `type` property (person / firm / company / university)
so the UI and queries can classify nodes without relying on labels().
The dataset is deliberately shaped so the demo queries return interesting
results:
  - PayKart is a deep portfolio (7+ distinct investors across rounds)
  - several firms co-invest in the same startups (co-investment pairs)
  - Ankita Bose sits on two boards in different sectors (interlocks)
  - IIT Delhi + BITS Pilani alumni have founded multiple companies
  - short, human-readable paths exist between well-known people
"""

META = {
    "id": "investors",
    "name": "Startup & Investor Network",
    "tagline": "Co-investors, board interlocks, alumni in Indian startups",
    "accent": "#E04F2F",
    "node_labels": {
        "company": "Company",
        "person": "Person",
        "firm": "Firm",
        "university": "University",
    },
    "rel_labels": {
        "FOUNDED": "founded",
        "INVESTED_IN": "invested in",
        "BOARD_MEMBER": "board member",
        "WORKS_AT": "works at",
        "STUDIED_AT": "studied at",
        "KNOWS": "knows",
    },
    "person_type": "person",
    "institution_type": "university",
    "org_type": "company",
    "pairs_rel": "INVESTED_IN",
    "study_rel": "STUDIED_AT",
    "org_rels": ["FOUNDED", "WORKS_AT", "BOARD_MEMBER"],
    "interlock_rel": "BOARD_MEMBER",
    "portfolio_rel": "INVESTED_IN",
    "reach_rel": "INVESTED_IN",
    "sample_searches": ["PayKart", "Ananya Rao"],
}

COMPANIES = [
    ("PayKart", "FinTech", "SERIES_C", 2016, "Bengaluru"),
    ("RupeeFlow", "FinTech", "SEED", 2021, "Jaipur"),
    ("CureNest", "HealthTech", "SERIES_A", 2019, "Mumbai"),
    ("MediSend", "HealthTech", "SEED", 2021, "Chennai"),
    ("LearnSphere", "EdTech", "SERIES_B", 2015, "Delhi"),
    ("SkillStreet", "EdTech", "SERIES_A", 2020, "Bengaluru"),
    ("GridMetrics", "SaaS", "SERIES_A", 2018, "Pune"),
    ("CodeCanvas", "AI DevTools", "SEED", 2022, "Bengaluru"),
    ("AutoSight", "AI", "SEED", 2020, "Hyderabad"),
    ("NutriBlend", "D2C F&B", "SEED", 2021, "Bengaluru"),
    ("FreightLoop", "LogiTech", "SERIES_B", 2017, "Gurugram"),
    ("RentRocket", "PropTech", "SERIES_C", 2014, "Mumbai"),
    ("Agrowatch", "AgriTech", "SERIES_A", 2019, "Nagpur"),
    ("InstaPharma", "PharmaTech", "SERIES_B", 2016, "Ahmedabad"),
]

FIRMS = [
    ("NorthLoop Ventures", "VC", "Bengaluru"),
    ("Ganga River Capital", "VC", "Delhi"),
    ("BluePeak Angel Fund", "Angel Network", "Mumbai"),
    ("ForgePoint Partners", "VC", "Pune"),
    ("Horizon Seed Lab", "Accelerator", "Hyderabad"),
    ("WestVista Capital", "VC", "Mumbai"),
    ("Sapphire Creek Ventures", "VC", "Chennai"),
    ("Indigo Orchards Capital", "PE", "Delhi"),
]

PEOPLE = [
    ("Ananya Rao", "Bengaluru", "Co-founder & CEO, PayKart"),
    ("Vikram Nair", "Bengaluru", "Co-founder & CTO, PayKart"),
    ("Rohit Mehta", "Pune", "Co-founder & CEO, GridMetrics"),
    ("Kavya Krishnan", "Hyderabad", "Co-founder & CEO, AutoSight"),
    ("Priya Iyer", "Mumbai", "Co-founder & CEO, CureNest"),
    ("Manish Agarwal", "Jaipur", "Co-founder & CEO, RupeeFlow"),
    ("Divya Menon", "Bengaluru", "Founder & CEO, CodeCanvas"),
    ("Pooja Reddy", "Bengaluru", "Co-founder & CEO, SkillStreet"),
    ("Aditya Kulkarni", "Nagpur", "Founder & CEO, Agrowatch"),
    ("Nikhil Bhat", "Ahmedabad", "Founder & CEO, InstaPharma"),
    ("Farhan Sheikh", "Chennai", "Co-founder & CEO, MediSend"),
    ("Ritu Chawla", "Bengaluru", "Founder & CEO, NutriBlend"),
    ("Latha Venkatesh", "Gurugram", "CEO, FreightLoop"),
    ("Kevin D'Souza", "Mumbai", "CEO, RentRocket"),
    ("Neha Sharma", "Bengaluru", "Partner, NorthLoop Ventures"),
    ("Sameer Joshi", "Delhi", "Partner, Ganga River Capital"),
    ("Siddharth Kapoor", "Mumbai", "Angel investor, ex-founder"),
    ("Ankita Bose", "Mumbai", "Independent board director"),
]

UNIVERSITIES = [
    ("IIT Bombay", "Mumbai"),
    ("IIT Delhi", "Delhi"),
    ("BITS Pilani", "Pilani"),
    ("NIT Trichy", "Trichy"),
    ("IIIT Hyderabad", "Hyderabad"),
    ("IIM Ahmedabad", "Ahmedabad"),
]

# (person, company, role, year)
FOUNDED = [
    ("Ananya Rao", "PayKart", "Co-founder & CEO", 2016),
    ("Vikram Nair", "PayKart", "Co-founder & CTO", 2016),
    ("Rohit Mehta", "GridMetrics", "Co-founder & CEO", 2018),
    ("Kavya Krishnan", "AutoSight", "Co-founder & CEO", 2020),
    ("Priya Iyer", "CureNest", "Co-founder & CEO", 2019),
    ("Manish Agarwal", "RupeeFlow", "Co-founder & CEO", 2021),
    ("Divya Menon", "CodeCanvas", "Founder & CEO", 2022),
    ("Pooja Reddy", "SkillStreet", "Co-founder & CEO", 2020),
    ("Aditya Kulkarni", "Agrowatch", "Founder & CEO", 2019),
    ("Nikhil Bhat", "InstaPharma", "Founder & CEO", 2016),
    ("Farhan Sheikh", "MediSend", "Co-founder & CEO", 2021),
    ("Ritu Chawla", "NutriBlend", "Founder & CEO", 2021),
]

# (person, company, amount_usd, round, year) - angel / personal investments
PERSON_INVESTMENTS = [
    ("Neha Sharma", "PayKart", 2000000, "SERIES_A", 2018),
    ("Neha Sharma", "RupeeFlow", 400000, "SEED", 2021),
    ("Neha Sharma", "CodeCanvas", 250000, "SEED", 2022),
    ("Sameer Joshi", "PayKart", 1000000, "SEED", 2017),
    ("Sameer Joshi", "LearnSphere", 5000000, "SERIES_B", 2020),
    ("Siddharth Kapoor", "PayKart", 1500000, "SERIES_A", 2018),
    ("Siddharth Kapoor", "NutriBlend", 300000, "SEED", 2021),
    ("Siddharth Kapoor", "AutoSight", 350000, "SEED", 2020),
    ("Ankita Bose", "PayKart", 200000, "ANGEL", 2016),
    ("Ankita Bose", "RentRocket", 800000, "SERIES_B", 2018),
]

# (firm, company, amount_usd, round, year)
FIRM_INVESTMENTS = [
    ("NorthLoop Ventures", "PayKart", 8000000, "SERIES_C", 2024),
    ("NorthLoop Ventures", "CodeCanvas", 500000, "SEED", 2022),
    ("NorthLoop Ventures", "GridMetrics", 3000000, "SERIES_A", 2019),
    ("NorthLoop Ventures", "AutoSight", 1200000, "SEED", 2021),
    ("Ganga River Capital", "PayKart", 4000000, "SERIES_B", 2022),
    ("Ganga River Capital", "LearnSphere", 5000000, "SERIES_B", 2020),
    ("BluePeak Angel Fund", "PayKart", 1000000, "SEED", 2017),
    ("BluePeak Angel Fund", "CureNest", 2000000, "SERIES_A", 2020),
    ("ForgePoint Partners", "GridMetrics", 3000000, "SERIES_A", 2019),
    ("ForgePoint Partners", "InstaPharma", 4500000, "SERIES_B", 2021),
    ("Horizon Seed Lab", "AutoSight", 500000, "SEED", 2020),
    ("Horizon Seed Lab", "Agrowatch", 400000, "SEED", 2019),
    ("WestVista Capital", "RentRocket", 6000000, "SERIES_C", 2021),
    ("WestVista Capital", "CureNest", 3000000, "SERIES_B", 2022),
    ("Sapphire Creek Ventures", "FreightLoop", 3500000, "SERIES_B", 2020),
    ("Sapphire Creek Ventures", "MediSend", 800000, "SEED", 2021),
    ("Indigo Orchards Capital", "FreightLoop", 8000000, "SERIES_C", 2023),
    ("Indigo Orchards Capital", "InstaPharma", 5000000, "SERIES_B", 2021),
]

# (person, company, title, since)
BOARD_MEMBERS = [
    ("Ankita Bose", "PayKart", "Independent Director", 2020),
    ("Ankita Bose", "RentRocket", "Independent Director", 2019),
    ("Neha Sharma", "PayKart", "Board Observer", 2022),
    ("Sameer Joshi", "LearnSphere", "Board Observer", 2020),
    ("Latha Venkatesh", "FreightLoop", "Independent Director", 2021),
]

# (person, company, title, since)
WORKS_AT = [
    ("Divya Menon", "GridMetrics", "Senior Engineer", 2019),
    ("Vikram Nair", "PayKart", "Co-founder & CTO", 2016),
    ("Kevin D'Souza", "RentRocket", "CEO", 2019),
    ("Latha Venkatesh", "FreightLoop", "CEO", 2019),
]

# (person, university, degree, year)
STUDIED_AT = [
    ("Ananya Rao", "IIT Bombay", "BTech", 2012),
    ("Vikram Nair", "IIT Bombay", "BTech", 2012),
    ("Rohit Mehta", "NIT Trichy", "BTech", 2010),
    ("Kavya Krishnan", "IIIT Hyderabad", "BTech", 2014),
    ("Priya Iyer", "BITS Pilani", "MBA", 2009),
    ("Manish Agarwal", "BITS Pilani", "BTech", 2015),
    ("Divya Menon", "IIT Delhi", "BTech", 2015),
    ("Pooja Reddy", "IIIT Hyderabad", "BTech", 2014),
    ("Aditya Kulkarni", "NIT Trichy", "BTech", 2011),
    ("Nikhil Bhat", "NIT Trichy", "BTech", 2008),
    ("Farhan Sheikh", "IIT Delhi", "BTech", 2015),
    ("Ritu Chawla", "IIM Ahmedabad", "MBA", 2016),
    ("Latha Venkatesh", "IIT Delhi", "BTech", 2010),
    ("Kevin D'Souza", "BITS Pilani", "MBA", 2012),
    ("Neha Sharma", "IIM Ahmedabad", "MBA", 2010),
    ("Sameer Joshi", "IIT Delhi", "BTech", 2008),
]

# (person_a, person_b) - mutual, close ties
KNOWS = [
    ("Ananya Rao", "Neha Sharma"),
    ("Vikram Nair", "Ananya Rao"),
    ("Neha Sharma", "Sameer Joshi"),
    ("Siddharth Kapoor", "Ananya Rao"),
    ("Divya Menon", "Pooja Reddy"),
    ("Priya Iyer", "Ankita Bose"),
]


def build_dataset():
    """Return the investors dataset as {"nodes", "edges", "meta"}."""
    nodes = []
    edges = []

    def add_node(name, type_, **props):
        nodes.append({"name": name, "type": type_, **props})

    def add_edge(src, stype, rel, dst, dtype, **props):
        edges.append({"from": (stype, src), "rel": rel, "to": (dtype, dst), **props})

    for name, sector, stage, year, city in COMPANIES:
        add_node(name, "company", sector=sector, stage=stage, founded_year=year, city=city)
    for name, ftype, city in FIRMS:
        add_node(name, "firm", firm_type=ftype, city=city)
    for name, city, headline in PEOPLE:
        add_node(name, "person", city=city, headline=headline)
    for name, city in UNIVERSITIES:
        add_node(name, "university", city=city)

    for p, c, role, year in FOUNDED:
        add_edge(p, "person", "FOUNDED", c, "company", role=role, year=year)
    for p, c, amt, rnd, year in PERSON_INVESTMENTS:
        add_edge(p, "person", "INVESTED_IN", c, "company", amount_usd=amt, round=rnd, year=year)
    for f, c, amt, rnd, year in FIRM_INVESTMENTS:
        add_edge(f, "firm", "INVESTED_IN", c, "company", amount_usd=amt, round=rnd, year=year)
    for p, c, title, since in BOARD_MEMBERS:
        add_edge(p, "person", "BOARD_MEMBER", c, "company", title=title, since=since)
    for p, c, title, since in WORKS_AT:
        add_edge(p, "person", "WORKS_AT", c, "company", title=title, since=since)
    for p, u, degree, year in STUDIED_AT:
        add_edge(p, "person", "STUDIED_AT", u, "university", degree=degree, year=year)
    for a, b in KNOWS:
        add_edge(a, "person", "KNOWS", b, "person")

    return {"nodes": nodes, "edges": edges, "meta": META}
