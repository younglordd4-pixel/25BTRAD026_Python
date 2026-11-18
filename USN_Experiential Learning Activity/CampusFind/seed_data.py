"""
CampusFind - Realistic Sample Data Seeder
Populates the SQLite database with students, items, claims, matches, and activity records for demonstration.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

BASE_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(BASE_DIR))

from database import db
from authentication.security import generate_salt, hash_password
from student.matching import matching_engine


def seed_database():
    print("=" * 60)
    print("  🌱 Seeding CampusFind Database with Test & Demo Data")
    print("=" * 60)

    # 1. Admin Account
    admin_salt = generate_salt()
    admin_hash = hash_password("Admin@1234", admin_salt)
    admin_id = db.create_user(
        full_name="Prof. Robert Sterling",
        usn="ADMIN001",
        department="Campus Administration",
        email="admin@campusfind.edu",
        password_hash=admin_hash,
        salt=admin_salt,
        role="admin"
    )
    if not admin_id:
        existing = db.get_user_by_email("admin@campusfind.edu")
        admin_id = existing['user_id']
    print(f"  [+] Administrator: admin@campusfind.edu (Password: Admin@1234)")

    # 2. Student Accounts
    students_data = [
        ("Aarav Sharma", "1AB22CS014", "Computer Science", "aarav.sharma@college.edu", "Student@123"),
        ("Priya Nair", "1AB22EC045", "Electronics & Communication", "priya.nair@college.edu", "Student@123"),
        ("Rahul Verma", "1AB21ME078", "Mechanical Engineering", "rahul.verma@college.edu", "Student@123"),
        ("Sneha Patil", "1AB23IS032", "Information Science", "sneha.patil@college.edu", "Student@123"),
    ]

    student_ids = []
    for name, usn, dept, email, pw in students_data:
        salt = generate_salt()
        pw_h = hash_password(pw, salt)
        uid = db.create_user(
            full_name=name, usn=usn, department=dept,
            email=email, password_hash=pw_h, salt=salt, role="student"
        )
        if not uid:
            uid = db.get_user_by_email(email)['user_id']
        student_ids.append(uid)
        print(f"  [+] Student: {name} ({email}) (Password: {pw})")

    today = datetime.now()
    d1 = (today - timedelta(days=2)).strftime("%Y-%m-%d")
    d2 = (today - timedelta(days=3)).strftime("%Y-%m-%d")
    d3 = (today - timedelta(days=5)).strftime("%Y-%m-%d")
    d4 = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    d5 = (today - timedelta(days=10)).strftime("%Y-%m-%d")

    # 3. Lost Items
    lost_items = [
        (student_ids[0], "Dell XPS 15 Silver Laptop", "Electronics", "Library (2nd Floor Reading Room)", d1,
         "Silver Dell XPS 15 laptop with Intel i7 processor. Has minor scratch on left palm rest.",
         "GitHub sticker on lid, serial ending in 9842", "aarav.sharma@college.edu"),

        (student_ids[1], "Blue Casio Scientific Calculator FX-991EX", "Books & Stationery", "Science Block", d2,
         "Blue Casio scientific calculator used during engineering mathematics test.",
         "Name 'Priya N' written in permanent marker on inside of battery cover", "priya.nair@college.edu"),

        (student_ids[2], "Black Leather Fossil Wallet", "Personal Belongings", "Cafeteria", d3,
         "Dark brown/black leather trifold wallet containing some cash and bus pass.",
         "Embossed Fossil logo on bottom right, college bus pass inside", "rahul.verma@college.edu"),

        (student_ids[3], "Set of 3 Yale Keys on Red Keychain", "Keys", "Hostel", d4,
         "Two brass Yale door keys and one small padlock key on a red fabric lanyard.",
         "Red embroidered keychain saying 'REMOVE BEFORE FLIGHT'", "sneha.patil@college.edu"),

        (student_ids[0], "Sony WH-1000XM4 Black Headphones", "Electronics", "Auditorium", d5,
         "Black over-ear noise cancelling wireless headphones with black carrying case.",
         "Small tear on left earcup cushion padding", "aarav.sharma@college.edu"),
    ]

    lost_ids = []
    for uid, name, cat, loc, dt, desc, feat, em in lost_items:
        iid = db.create_item(uid, "lost", name, cat, loc, dt, desc, feat, None, em)
        lost_ids.append(iid)

    print(f"  [+] Inserted {len(lost_ids)} lost item reports")

    # 4. Found Items (Engineered to match several lost items)
    found_items = [
        (student_ids[1], "Dell XPS Laptop 15-inch", "Electronics", "Library (2nd Floor)", d1,
         "Found silver Dell laptop left on study desk 14 near the windows in the library reading room.",
         "Has software developer stickers on top lid", "priya.nair@college.edu"),

        (student_ids[2], "Casio FX Scientific Calculator Blue", "Books & Stationery", "Science Block", d2,
         "Blue Casio FX calculator found on bench in hallway outside Physics Lab 2.",
         "Marking on battery cover", "rahul.verma@college.edu"),

        (student_ids[0], "Brown Leather Wallet", "Personal Belongings", "Cafeteria", d3,
         "Leather wallet found under table 8 in the main cafeteria area.",
         "Contains identification card and travel pass", "aarav.sharma@college.edu"),

        (student_ids[3], "Keys on Red Lanyard", "Keys", "Hostel", d4,
         "Set of 3 keys found near Hostel Block B entrance pathway.",
         "Red cloth strap attached", "sneha.patil@college.edu"),

        (admin_id, "Campus College ID Card", "Documents & ID Cards", "Main Block", d1,
         "Student identity card found near main admin enquiry desk.",
         "Student photo and barcode intact", "admin@campusfind.edu"),
    ]

    found_ids = []
    for uid, name, cat, loc, dt, desc, feat, em in found_items:
        iid = db.create_item(uid, "found", name, cat, loc, dt, desc, feat, None, em)
        found_ids.append(iid)

    print(f"  [+] Inserted {len(found_ids)} found item reports")

    # 5. Execute automatic matching
    matches = matching_engine.run_matching()
    print(f"  [+] Automatic Matching generated {len(matches)} potential match records")

    # 6. Sample Claims
    # Claim 1: Aarav claiming the Dell Laptop (lost_ids[0] vs found_ids[0]) -> Approved
    c1 = db.create_claim(
        lost_item_id=lost_ids[0],
        found_item_id=found_ids[0],
        claimant_id=student_ids[0],
        claim_details="This is my Dell XPS 15 laptop. I can unlock it with my student fingerprint and provide the original invoice showing service tag #DL-9842.",
        additional_info="Wallpaper is a picture of the Golden Gate bridge.",
        contact_email="aarav.sharma@college.edu"
    )
    db.update_claim_status(c1, "approved", "Serial number matches student invoice. Verified with fingerprint unlock.")

    # Claim 2: Priya claiming the Calculator (lost_ids[1] vs found_ids[1]) -> Under Review
    c2 = db.create_claim(
        lost_item_id=lost_ids[1],
        found_item_id=found_ids[1],
        claimant_id=student_ids[1],
        claim_details="This is my calculator from Maths class. It has 'Priya N' written inside the battery lid in permanent black ink.",
        additional_info="Purchased at the campus bookstore last month.",
        contact_email="priya.nair@college.edu"
    )
    db.update_claim_status(c2, "under_review", "Pending physical inspection of name under battery lid.")

    # Claim 3: Rahul claiming the Wallet (lost_ids[2] vs found_ids[2]) -> Returned
    c3 = db.create_claim(
        lost_item_id=lost_ids[2],
        found_item_id=found_ids[2],
        claimant_id=student_ids[2],
        claim_details="My Fossil wallet with my bus pass in my name Rahul Verma and 500 rupees cash.",
        additional_info="Student ID photo matches the bus pass card inside.",
        contact_email="rahul.verma@college.edu"
    )
    db.update_claim_status(c3, "returned", "Item returned in person to claimant at the security desk.")
    db.update_item_status(found_ids[2], "returned")
    db.update_item_status(lost_ids[2], "closed")

    # Claim 4: Sneha claiming the Keys (lost_ids[3] vs found_ids[3]) -> Pending
    c4 = db.create_claim(
        lost_item_id=lost_ids[3],
        found_item_id=found_ids[3],
        claimant_id=student_ids[3],
        claim_details="Keys to my hostel room 302 and my locker. Red lanyard says REMOVE BEFORE FLIGHT.",
        additional_info="Can demonstrate that the key fits hostel door 302.",
        contact_email="sneha.patil@college.edu"
    )

    print("  [+] Inserted 4 sample ownership claims (Approved, Under Review, Returned, Pending)")

    # 7. Sample Activity Log
    activities = [
        (student_ids[0], "login", "Student Aarav Sharma logged in"),
        (student_ids[0], "report_lost", f"Reported lost item: Dell XPS 15 (ID: #{lost_ids[0]})"),
        (student_ids[1], "report_found", f"Reported found item: Dell XPS Laptop (ID: #{found_ids[0]})"),
        (student_ids[0], "submit_claim", f"Submitted claim #{c1} on Dell XPS Laptop"),
        (admin_id, "adjudicate_claim", f"Approved claim #{c1} after physical serial verification"),
        (admin_id, "adjudicate_claim", f"Marked claim #{c3} as returned to Rahul Verma"),
    ]
    for uid, act, det in activities:
        db.log_activity(uid, act, det)

    print("  [+] Inserted activity log records")

    # 8. Sample Notifications
    notifications = [
        (student_ids[0], "Match Found!", "A 92% match has been found for your lost Dell laptop.", "match_found"),
        (student_ids[0], "Claim #1 Approved", "Your claim for Dell XPS Laptop has been APPROVED by the administrator.", "claim_status"),
        (student_ids[1], "Claim #2 Under Review", "Your claim for Casio Calculator is currently being reviewed.", "claim_status"),
        (student_ids[2], "Item Returned Confirmation", "Your Brown Leather Wallet has been marked as RETURNED. Thank you!", "claim_status"),
    ]
    for uid, title, msg, ntype in notifications:
        db.create_notification(uid, title, msg, ntype)

    print("  [+] Inserted student notifications")
    print("=" * 60)
    print("✅ Seed completed successfully! Database is primed and ready.")
    print("=" * 60)


if __name__ == "__main__":
    seed_database()
