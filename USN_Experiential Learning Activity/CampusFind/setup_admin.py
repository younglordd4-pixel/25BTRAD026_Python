"""
CampusFind - Administrator Setup Utility
Securely creates the initial administrator account or promotes an existing account.
"""

import sys
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(BASE_DIR))

from database import db
from authentication.security import (
    generate_salt, hash_password, validate_password,
    validate_email, validate_usn
)


def run_setup():
    print("=" * 65)
    print("  🎓 CampusFind – Smart College Lost and Found System")
    print("  Administrator Account Setup")
    print("=" * 65)

    all_users = db.get_all_users()
    admins = [u for u in all_users if u.get('role') == 'admin']

    if admins:
        print(f"\n[INFO] Active Administrator Accounts ({len(admins)} found):")
        for idx, a in enumerate(admins, 1):
            print(f"  {idx}. {a['full_name']} | Email: {a['email']} | USN: {a['usn']}")
        print("\nDo you wish to create an additional administrator? [y/N]: ", end="")
        choice = input().strip().lower()
        if choice != 'y':
            print("Setup aborted.")
            return

    print("\nPlease enter details for the administrator account:")

    # Full Name
    while True:
        full_name = input("  Full Name: ").strip()
        if len(full_name) >= 3:
            break
        print("  [!] Full name must be at least 3 characters.")

    # USN / Admin ID
    while True:
        usn = input("  Administrator ID / USN: ").strip().upper()
        if validate_usn(usn):
            break
        print("  [!] ID/USN must be at least 5 alphanumeric characters.")

    # Department
    dept = input("  Department (e.g. Campus Administration / IT): ").strip()
    if not dept:
        dept = "Campus Administration"

    # Email
    while True:
        email = input("  Email Address: ").strip().lower()
        if validate_email(email):
            break
        print("  [!] Please enter a valid email address.")

    # Password
    while True:
        password = input("  Password (min 8 chars, 1 uppercase, 1 lowercase, 1 digit): ").strip()
        valid, msg = validate_password(password)
        if valid:
            confirm = input("  Confirm Password: ").strip()
            if confirm == password:
                break
            else:
                print("  [!] Passwords do not match. Try again.")
        else:
            print(f"  [!] {msg}")

    # Check existing
    existing = db.get_user_by_email(email) or db.get_user_by_usn(usn)
    if existing:
        print(f"\n[INFO] An account with email {existing['email']} already exists.")
        print("Promoting existing account to Administrator...")
        db.update_user(existing['user_id'], role='admin')
        print("✅ Account successfully upgraded to Administrator!")
        return

    # Generate salt and hash
    salt = generate_salt()
    pw_hash = hash_password(password, salt)

    user_id = db.create_user(
        full_name=full_name,
        usn=usn,
        department=dept,
        email=email,
        password_hash=pw_hash,
        salt=salt,
        role='admin'
    )

    if user_id:
        db.log_activity(user_id, 'admin_setup', f"Administrator account created: {email}")
        print("\n" + "=" * 65)
        print("✅ SUCCESS: Administrator account created successfully!")
        print(f"  Name:   {full_name}")
        print(f"  Email:  {email}")
        print(f"  USN/ID: {usn}")
        print(f"  Role:   ADMINISTRATOR")
        print("=" * 65)
        print("You can now launch the application using:")
        print("  python main.py")
        print("and log in using the email/USN and password configured above.")
    else:
        print("❌ ERROR: Failed to create administrator account in database.")


if __name__ == "__main__":
    run_setup()
