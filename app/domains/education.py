"""The education domain - an alumni & mentorship network across Indian
campuses: 43 nodes, ~119 relationships.

Students (class of 2025-2027) study at six universities, land internships
and placements at eight companies, and take elective courses. Senior
engineers and PMs mentor students (many at their own alma mater) and advise
universities, which makes co-alumni pairs, alumni chains and mentor
interlocks visible in the queries:
  - co-alumni pairs: several students per university (STUDIED_AT)
  - alumni chains: placed/interned students connect campuses to companies
  - interlocks: four mentors advise two universities each (ADVISES_AT)
"""

META = {
    "id": "education",
    "name": "Alumni & Mentorship Network",
    "tagline": "Co-alumni, placements, and mentors across Indian campuses",
    "accent": "#0B6E4F",
    "node_labels": {
        "student": "Student",
        "mentor": "Mentor",
        "university": "University",
        "company": "Company",
        "course": "Course",
    },
    "rel_labels": {
        "STUDIED_AT": "studied at",
        "PLACED_AT": "placed at",
        "INTERNSHIP_AT": "interned at",
        "WORKS_AT": "works at",
        "MENTORED_BY": "mentored by",
        "ADVISES_AT": "advises at",
        "KNOWS": "knows",
        "TOOK": "took",
    },
    "person_type": "student",
    "institution_type": "university",
    "org_type": "company",
    "pairs_rel": "STUDIED_AT",
    "study_rel": "STUDIED_AT",
    "org_rels": ["PLACED_AT", "INTERNSHIP_AT", "WORKS_AT"],
    "interlock_rel": "ADVISES_AT",
    "portfolio_rel": None,
    "reach_rel": None,
    "sample_searches": ["Zoho", "Priya Sharma"],
}

UNIVERSITIES = [
    ("IIT Madras", "Chennai"),
    ("BITS Pilani", "Pilani"),
    ("NIT Trichy", "Trichy"),
    ("Anna University", "Chennai"),
    ("VIT Vellore", "Vellore"),
    ("SRM University", "Chennai"),
]

COMPANIES = [
    ("Zoho", "SaaS", "Chennai"),
    ("Swiggy", "Consumer Tech", "Bengaluru"),
    ("Razorpay", "FinTech", "Bengaluru"),
    ("Freshworks", "SaaS", "Chennai"),
    ("Infosys", "IT Services", "Bengaluru"),
    ("TCS", "IT Services", "Mumbai"),
    ("Zerodha", "FinTech", "Bengaluru"),
    ("Ather Energy", "EV", "Bengaluru"),
]

COURSES = ["MLOps", "Distributed Systems", "Product Analytics"]

# (name, university, degree, grad_year)
STUDENTS = [
    ("Priya Sharma", "BITS Pilani", "BTech", 2026),
    ("Arjun Mehta", "IIT Madras", "BTech", 2025),
    ("Sneha Patel", "Anna University", "BE", 2026),
    ("Rohan Verma", "NIT Trichy", "BTech", 2025),
    ("Kavya Nair", "VIT Vellore", "BTech", 2027),
    ("Aditya Kumar", "SRM University", "BTech", 2026),
    ("Ishita Gupta", "BITS Pilani", "BTech", 2025),
    ("Nikhil Reddy", "IIT Madras", "BTech", 2027),
    ("Meera Krishnan", "Anna University", "BE", 2025),
    ("Varun Iyer", "NIT Trichy", "MTech", 2026),
    ("Ananya Das", "VIT Vellore", "BTech", 2025),
    ("Harsha Rao", "SRM University", "BTech", 2027),
    ("Ritesh Singh", "BITS Pilani", "BTech", 2027),
    ("Divya Pillai", "Anna University", "BE", 2027),
    ("Karthik Menon", "IIT Madras", "BTech", 2026),
    ("Sahana Joshi", "NIT Trichy", "BTech", 2027),
    ("Pooja Hegde", "VIT Vellore", "BTech", 2026),
    ("Rakesh Tiwari", "SRM University", "BTech", 2025),
]

# (name, company, role, years_exp)
MENTORS = [
    ("Rahul Bhatia", "Razorpay", "Staff Engineer", 9),
    ("Priyanka Nair", "Swiggy", "Engineering Manager", 11),
    ("Amit Deshpande", "Zoho", "Principal Engineer", 13),
    ("Sneha Kulkarni", "Freshworks", "Product Manager", 8),
    ("Rajesh Menon", "Infosys", "Senior Architect", 15),
    ("Deepa Subramanian", "Ather Energy", "Director of Engineering", 12),
    ("Vivek Anand", "Zerodha", "Senior SDE", 7),
    ("Lakshmi Narayanan", "TCS", "Technical Program Manager", 10),
]

# (student, company, role, ctc_lpa, year)
PLACED_AT = [
    ("Arjun Mehta", "Razorpay", "SDE-1", 26, 2024),
    ("Rohan Verma", "Swiggy", "SDE-1", 22, 2024),
    ("Ishita Gupta", "Zoho", "Software Engineer", 18, 2024),
    ("Meera Krishnan", "TCS", "Systems Engineer", 7.5, 2024),
    ("Ananya Das", "Infosys", "Software Engineer", 9, 2024),
    ("Rakesh Tiwari", "Zerodha", "Platform Engineer", 24, 2024),
    ("Priya Sharma", "Zoho", "Software Engineer", 18.5, 2025),
    ("Sneha Patel", "TCS", "Systems Engineer", 7.5, 2025),
    ("Varun Iyer", "Razorpay", "Backend Engineer", 28, 2025),
    ("Aditya Kumar", "Freshworks", "Software Engineer", 15, 2025),
    ("Karthik Menon", "Ather Energy", "Embedded Engineer", 20, 2025),
    ("Pooja Hegde", "Swiggy", "SDE-1", 21, 2025),
]

# (student, company, role, year)
INTERNSHIP_AT = [
    ("Priya Sharma", "Razorpay", "SDE Intern", 2024),
    ("Arjun Mehta", "Zoho", "Engineering Intern", 2023),
    ("Kavya Nair", "Zoho", "Software Intern", 2026),
    ("Nikhil Reddy", "Ather Energy", "R&D Intern", 2026),
    ("Harsha Rao", "Infosys", "Systems Intern", 2026),
    ("Ritesh Singh", "Swiggy", "SDE Intern", 2026),
    ("Divya Pillai", "TCS", "Engineering Intern", 2026),
    ("Sahana Joshi", "Freshworks", "Product Intern", 2026),
]

# (mentor, university, role, since)
ADVISES_AT = [
    ("Rahul Bhatia", "IIT Madras", "Guest Mentor", 2021),
    ("Rahul Bhatia", "NIT Trichy", "Industry Panelist", 2023),
    ("Priyanka Nair", "BITS Pilani", "Alumni Mentor", 2019),
    ("Priyanka Nair", "Anna University", "Guest Lecture", 2022),
    ("Amit Deshpande", "NIT Trichy", "Advisory Board", 2018),
    ("Amit Deshpande", "VIT Vellore", "Guest Mentor", 2021),
    ("Sneha Kulkarni", "Anna University", "Career Counselor", 2020),
    ("Rajesh Menon", "VIT Vellore", "Mentor", 2017),
    ("Deepa Subramanian", "SRM University", "Industry Mentor", 2019),
    ("Deepa Subramanian", "BITS Pilani", "Guest Mentor", 2022),
    ("Vivek Anand", "IIT Madras", "Alumni Mentor", 2020),
    ("Lakshmi Narayanan", "BITS Pilani", "Guest Lecture", 2018),
]

# (mentor, student, since)
MENTORED_BY = [
    ("Rahul Bhatia", "Arjun Mehta", 2023),
    ("Rahul Bhatia", "Karthik Menon", 2024),
    ("Rahul Bhatia", "Nikhil Reddy", 2025),
    ("Priyanka Nair", "Priya Sharma", 2024),
    ("Amit Deshpande", "Rohan Verma", 2023),
    ("Amit Deshpande", "Sahana Joshi", 2025),
    ("Sneha Kulkarni", "Meera Krishnan", 2024),
    ("Sneha Kulkarni", "Divya Pillai", 2025),
    ("Rajesh Menon", "Ananya Das", 2023),
    ("Rajesh Menon", "Pooja Hegde", 2024),
    ("Deepa Subramanian", "Aditya Kumar", 2024),
    ("Deepa Subramanian", "Harsha Rao", 2025),
    ("Vivek Anand", "Varun Iyer", 2024),
    ("Vivek Anand", "Rakesh Tiwari", 2023),
    ("Lakshmi Narayanan", "Sneha Patel", 2024),
]

# (student_a, student_b)
KNOWS = [
    ("Arjun Mehta", "Rohan Verma"),
    ("Priya Sharma", "Ishita Gupta"),
    ("Kavya Nair", "Ananya Das"),
    ("Nikhil Reddy", "Karthik Menon"),
    ("Sneha Patel", "Meera Krishnan"),
    ("Varun Iyer", "Rohan Verma"),
    ("Pooja Hegde", "Aditya Kumar"),
    ("Harsha Rao", "Sahana Joshi"),
    ("Rakesh Tiwari", "Aditya Kumar"),
    ("Divya Pillai", "Meera Krishnan"),
]

# (student, course, grade)
TOOK = [
    ("Priya Sharma", "MLOps", "A+"),
    ("Priya Sharma", "Product Analytics", "A"),
    ("Arjun Mehta", "Distributed Systems", "A"),
    ("Arjun Mehta", "MLOps", "B+"),
    ("Sneha Patel", "Product Analytics", "B+"),
    ("Sneha Patel", "Distributed Systems", "B"),
    ("Rohan Verma", "Distributed Systems", "A"),
    ("Rohan Verma", "MLOps", "B"),
    ("Kavya Nair", "MLOps", "B"),
    ("Kavya Nair", "Product Analytics", "B+"),
    ("Aditya Kumar", "MLOps", "A"),
    ("Aditya Kumar", "Distributed Systems", "B+"),
    ("Ishita Gupta", "Product Analytics", "A"),
    ("Ishita Gupta", "MLOps", "A-"),
    ("Nikhil Reddy", "Distributed Systems", "A-"),
    ("Nikhil Reddy", "MLOps", "A"),
    ("Meera Krishnan", "Product Analytics", "B"),
    ("Meera Krishnan", "Distributed Systems", "B+"),
    ("Varun Iyer", "Distributed Systems", "A"),
    ("Varun Iyer", "MLOps", "A-"),
    ("Ananya Das", "Product Analytics", "A"),
    ("Ananya Das", "MLOps", "B+"),
    ("Harsha Rao", "MLOps", "B+"),
    ("Harsha Rao", "Distributed Systems", "B"),
    ("Ritesh Singh", "MLOps", "A-"),
    ("Ritesh Singh", "Product Analytics", "B+"),
    ("Divya Pillai", "Distributed Systems", "B+"),
    ("Divya Pillai", "Product Analytics", "B"),
    ("Karthik Menon", "Distributed Systems", "A"),
    ("Karthik Menon", "MLOps", "A"),
    ("Sahana Joshi", "MLOps", "B+"),
    ("Sahana Joshi", "Product Analytics", "A-"),
    ("Pooja Hegde", "Product Analytics", "A"),
    ("Pooja Hegde", "MLOps", "A-"),
    ("Rakesh Tiwari", "Distributed Systems", "A-"),
]


def build_dataset():
    """Return the education dataset as {"nodes", "edges", "meta"}."""
    nodes = []
    edges = []

    def add_node(name, type_, **props):
        nodes.append({"name": name, "type": type_, **props})

    def add_edge(src, stype, rel, dst, dtype, **props):
        edges.append({"from": (stype, src), "rel": rel, "to": (dtype, dst), **props})

    for name, city in UNIVERSITIES:
        add_node(name, "university", city=city)
    for name, sector, city in COMPANIES:
        add_node(name, "company", sector=sector, city=city)
    for name in COURSES:
        add_node(name, "course")
    for name, uni, degree, year in STUDENTS:
        add_node(name, "student")
        add_edge(name, "student", "STUDIED_AT", uni, "university",
                 degree=degree, grad_year=year)
    for name, company, role, exp in MENTORS:
        add_node(name, "mentor")
        add_edge(name, "mentor", "WORKS_AT", company, "company",
                 role=role, years_exp=exp)

    for s, c, role, ctc, year in PLACED_AT:
        add_edge(s, "student", "PLACED_AT", c, "company",
                 role=role, ctc_lpa=ctc, year=year)
    for s, c, role, year in INTERNSHIP_AT:
        add_edge(s, "student", "INTERNSHIP_AT", c, "company",
                 role=role, year=year)
    for m, u, role, since in ADVISES_AT:
        add_edge(m, "mentor", "ADVISES_AT", u, "university",
                 role=role, since=since)
    for m, s, since in MENTORED_BY:
        add_edge(m, "mentor", "MENTORED_BY", s, "student", since=since)
    for a, b in KNOWS:
        add_edge(a, "student", "KNOWS", b, "student")
    for s, course, grade in TOOK:
        add_edge(s, "student", "TOOK", course, "course",
                 course=course, grade=grade)

    return {"nodes": nodes, "edges": edges, "meta": META}
