"""The healthcare domain - a care-network graph with realistic Indian data:
46 nodes, ~129 relationships.

Fourteen doctors across six hospitals treat fifteen patients, specialize in
departments, and refer patients to each other along multi-hop chains.
The graph is shaped so the queries return interesting results:
  - shared patients: many patients are attended by two or three doctors
  - referral chains: three chains of three doctors (REFERRED_TO)
  - staff interlocks: seven doctors work at two hospitals (WORKS_AT)
  - patient stories: diagnoses, hospital visits and chronic conditions
"""

META = {
    "id": "healthcare",
    "name": "Care Network Graph",
    "tagline": "Shared patients, referral chains, and hospital staff networks",
    "accent": "#2563EB",
    "node_labels": {
        "doctor": "Doctor",
        "patient": "Patient",
        "hospital": "Hospital",
        "department": "Department",
        "condition": "Condition",
    },
    "rel_labels": {
        "WORKS_AT": "works at",
        "SPECIALIZES_IN": "specializes in",
        "TREATS": "treats",
        "DIAGNOSED_WITH": "diagnosed with",
        "ATTENDED_BY": "attended by",
        "REFERRED_TO": "referred to",
        "VISITED": "visited",
    },
    "person_type": "doctor",
    "institution_type": "department",
    "org_type": "hospital",
    "pairs_rel": "TREATS",
    "study_rel": "SPECIALIZES_IN",
    "org_rels": ["WORKS_AT"],
    "interlock_rel": "WORKS_AT",
    "portfolio_rel": None,
    "reach_rel": None,
    "sample_searches": ["Dr. Meera Iyer", "Apollo Hospitals"],
}

HOSPITALS = [
    ("Apollo Hospitals", "Mumbai"),
    ("Fortis", "Delhi"),
    ("AIIMS Delhi", "Delhi"),
    ("Manipal", "Bengaluru"),
    ("Narayana Health", "Bengaluru"),
    ("KIMS", "Hyderabad"),
]

DEPARTMENTS = ["Cardiology", "Neurology", "Oncology", "Orthopedics", "Pediatrics", "General Medicine"]

CONDITIONS = ["Diabetes", "Hypertension", "Asthma", "Epilepsy", "Heart Disease"]

# (name, speciality, city)
DOCTORS = [
    ("Dr. Meera Iyer", "Cardiology", "Mumbai"),
    ("Dr. Ravi Desai", "Neurology", "Delhi"),
    ("Dr. Sunita Rao", "Oncology", "Bengaluru"),
    ("Dr. Arvind Menon", "Orthopedics", "Chennai"),
    ("Dr. Kavita Reddy", "Pediatrics", "Delhi"),
    ("Dr. Sanjay Gupta", "General Medicine", "Delhi"),
    ("Dr. Priya Krishnan", "Cardiology", "Bengaluru"),
    ("Dr. Vikram Singh", "Neurology", "Delhi"),
    ("Dr. Anjali Nair", "Oncology", "Mumbai"),
    ("Dr. Rajesh Kumar", "Orthopedics", "Bengaluru"),
    ("Dr. Deepika Sharma", "Pediatrics", "Hyderabad"),
    ("Dr. Mohan Iyer", "General Medicine", "Hyderabad"),
    ("Dr. Farah Khan", "Cardiology", "Delhi"),
    ("Dr. Naresh Patel", "General Medicine", "Mumbai"),
]

# (name, age, city)
PATIENTS = [
    ("Ramesh Gupta", 58, "Delhi"),
    ("Lakshmi Bai", 62, "Bengaluru"),
    ("Arun Pillai", 45, "Chennai"),
    ("Sunita Devi", 34, "Mumbai"),
    ("Karthik Raja", 28, "Chennai"),
    ("Meenakshi Iyer", 52, "Hyderabad"),
    ("Gopal Rao", 67, "Hyderabad"),
    ("Farida Begum", 41, "Delhi"),
    ("Suresh Nair", 55, "Kochi"),
    ("Anita Joshi", 39, "Pune"),
    ("Devraj Singh", 49, "Jaipur"),
    ("Padma Venkatesh", 71, "Chennai"),
    ("Rohan Mishra", 23, "Bengaluru"),
    ("Aarav Reddy", 6, "Hyderabad"),
    ("Isha Sharma", 9, "Mumbai"),
]

# (doctor, hospital, since, full_time)
WORKS_AT = [
    ("Dr. Meera Iyer", "Apollo Hospitals", 2010, True),
    ("Dr. Meera Iyer", "Fortis", 2015, False),
    ("Dr. Ravi Desai", "AIIMS Delhi", 2012, True),
    ("Dr. Sunita Rao", "Manipal", 2014, True),
    ("Dr. Arvind Menon", "Apollo Hospitals", 2013, True),
    ("Dr. Arvind Menon", "KIMS", 2018, False),
    ("Dr. Kavita Reddy", "Fortis", 2011, True),
    ("Dr. Kavita Reddy", "Manipal", 2017, False),
    ("Dr. Sanjay Gupta", "AIIMS Delhi", 2008, True),
    ("Dr. Sanjay Gupta", "Narayana Health", 2020, False),
    ("Dr. Priya Krishnan", "Narayana Health", 2016, True),
    ("Dr. Vikram Singh", "Fortis", 2015, True),
    ("Dr. Vikram Singh", "AIIMS Delhi", 2019, False),
    ("Dr. Anjali Nair", "Narayana Health", 2017, True),
    ("Dr. Anjali Nair", "Apollo Hospitals", 2021, False),
    ("Dr. Rajesh Kumar", "Manipal", 2012, True),
    ("Dr. Deepika Sharma", "KIMS", 2019, True),
    ("Dr. Mohan Iyer", "KIMS", 2015, True),
    ("Dr. Mohan Iyer", "Fortis", 2022, False),
    ("Dr. Farah Khan", "AIIMS Delhi", 2018, True),
    ("Dr. Naresh Patel", "Apollo Hospitals", 2016, True),
]

# (doctor, patient, since)
TREATS = [
    ("Dr. Meera Iyer", "Lakshmi Bai", 2015),
    ("Dr. Meera Iyer", "Gopal Rao", 2016),
    ("Dr. Meera Iyer", "Devraj Singh", 2020),
    ("Dr. Meera Iyer", "Padma Venkatesh", 2019),
    ("Dr. Ravi Desai", "Karthik Raja", 2022),
    ("Dr. Ravi Desai", "Rohan Mishra", 2023),
    ("Dr. Sunita Rao", "Arun Pillai", 2021),
    ("Dr. Arvind Menon", "Padma Venkatesh", 2019),
    ("Dr. Arvind Menon", "Suresh Nair", 2020),
    ("Dr. Kavita Reddy", "Aarav Reddy", 2022),
    ("Dr. Kavita Reddy", "Isha Sharma", 2021),
    ("Dr. Sanjay Gupta", "Ramesh Gupta", 2018),
    ("Dr. Sanjay Gupta", "Anita Joshi", 2014),
    ("Dr. Priya Krishnan", "Lakshmi Bai", 2021),
    ("Dr. Priya Krishnan", "Meenakshi Iyer", 2019),
    ("Dr. Vikram Singh", "Karthik Raja", 2022),
    ("Dr. Vikram Singh", "Rohan Mishra", 2023),
    ("Dr. Anjali Nair", "Farida Begum", 2020),
    ("Dr. Anjali Nair", "Gopal Rao", 2021),
    ("Dr. Rajesh Kumar", "Suresh Nair", 2018),
    ("Dr. Rajesh Kumar", "Padma Venkatesh", 2022),
    ("Dr. Deepika Sharma", "Aarav Reddy", 2023),
    ("Dr. Deepika Sharma", "Isha Sharma", 2022),
    ("Dr. Mohan Iyer", "Ramesh Gupta", 2015),
    ("Dr. Mohan Iyer", "Sunita Devi", 2019),
    ("Dr. Farah Khan", "Devraj Singh", 2023),
    ("Dr. Naresh Patel", "Meenakshi Iyer", 2022),
    ("Dr. Naresh Patel", "Rohan Mishra", 2023),
]

# (patient, condition, year)
DIAGNOSED_WITH = [
    ("Ramesh Gupta", "Diabetes", 2018),
    ("Ramesh Gupta", "Hypertension", 2015),
    ("Lakshmi Bai", "Heart Disease", 2020),
    ("Arun Pillai", "Diabetes", 2021),
    ("Sunita Devi", "Asthma", 2019),
    ("Karthik Raja", "Epilepsy", 2022),
    ("Meenakshi Iyer", "Hypertension", 2017),
    ("Gopal Rao", "Heart Disease", 2016),
    ("Farida Begum", "Asthma", 2020),
    ("Suresh Nair", "Diabetes", 2015),
    ("Suresh Nair", "Hypertension", 2019),
    ("Anita Joshi", "Asthma", 2014),
    ("Devraj Singh", "Hypertension", 2018),
    ("Devraj Singh", "Heart Disease", 2023),
    ("Padma Venkatesh", "Heart Disease", 2019),
    ("Rohan Mishra", "Epilepsy", 2023),
    ("Aarav Reddy", "Asthma", 2022),
    ("Isha Sharma", "Epilepsy", 2021),
]

# (from_doctor, to_doctor, year)
REFERRED_TO = [
    ("Dr. Sanjay Gupta", "Dr. Meera Iyer", 2019),
    ("Dr. Meera Iyer", "Dr. Farah Khan", 2021),
    ("Dr. Ravi Desai", "Dr. Vikram Singh", 2020),
    ("Dr. Vikram Singh", "Dr. Sunita Rao", 2022),
    ("Dr. Mohan Iyer", "Dr. Arvind Menon", 2021),
    ("Dr. Arvind Menon", "Dr. Rajesh Kumar", 2023),
    ("Dr. Naresh Patel", "Dr. Priya Krishnan", 2022),
]

# (patient, hospital, year)
VISITED = [
    ("Ramesh Gupta", "AIIMS Delhi", 2023),
    ("Lakshmi Bai", "Apollo Hospitals", 2024),
    ("Arun Pillai", "Manipal", 2023),
    ("Sunita Devi", "KIMS", 2022),
    ("Karthik Raja", "Fortis", 2023),
    ("Meenakshi Iyer", "Narayana Health", 2024),
    ("Gopal Rao", "Apollo Hospitals", 2022),
    ("Farida Begum", "Narayana Health", 2023),
    ("Suresh Nair", "Apollo Hospitals", 2021),
    ("Anita Joshi", "KIMS", 2023),
    ("Devraj Singh", "Fortis", 2024),
    ("Padma Venkatesh", "Apollo Hospitals", 2022),
    ("Rohan Mishra", "AIIMS Delhi", 2023),
]


def build_dataset():
    """Return the healthcare dataset as {"nodes", "edges", "meta"}."""
    nodes = []
    edges = []

    def add_node(name, type_, **props):
        nodes.append({"name": name, "type": type_, **props})

    def add_edge(src, stype, rel, dst, dtype, **props):
        edges.append({"from": (stype, src), "rel": rel, "to": (dtype, dst), **props})

    for name, city in HOSPITALS:
        add_node(name, "hospital", city=city)
    for name in DEPARTMENTS:
        add_node(name, "department")
    for name in CONDITIONS:
        add_node(name, "condition")
    for name, speciality, city in DOCTORS:
        add_node(name, "doctor", speciality=speciality, city=city)
        add_edge(name, "doctor", "SPECIALIZES_IN", speciality, "department")
    for name, age, city in PATIENTS:
        add_node(name, "patient", age=age, city=city)

    for d, h, since, full_time in WORKS_AT:
        add_edge(d, "doctor", "WORKS_AT", h, "hospital",
                 since=since, full_time=full_time)
    for d, p, since in TREATS:
        add_edge(d, "doctor", "TREATS", p, "patient", since=since)
        add_edge(p, "patient", "ATTENDED_BY", d, "doctor", since=since)
    for p, c, year in DIAGNOSED_WITH:
        add_edge(p, "patient", "DIAGNOSED_WITH", c, "condition", year=year)
    for a, b, year in REFERRED_TO:
        add_edge(a, "doctor", "REFERRED_TO", b, "doctor", year=year)
    for p, h, year in VISITED:
        add_edge(p, "patient", "VISITED", h, "hospital", year=year)

    return {"nodes": nodes, "edges": edges, "meta": META}
