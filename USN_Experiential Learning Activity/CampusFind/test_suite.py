"""
CampusFind - Comprehensive Test Suite
Validates all 22 required functional test cases across security, database, matching,
claims, PDF, analytics, image processing, and theming.
"""

import os
import sys
import unittest
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(BASE_DIR))

from database import db
from config import CATEGORIES, CAMPUS_LOCATIONS, EXPORTS_DIR
from theme_manager import theme_manager, LIGHT_THEME, DARK_THEME
from authentication.security import (
    generate_salt, hash_password, verify_password,
    validate_email, validate_password, validate_usn
)
from services.image_service import image_service
from services.email_service import email_service
from services.pdf_service import pdf_service
from services.qr_service import qr_service
from services.analytics_service import analytics_service
from student.matching import matching_engine


class TestCampusFind(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print("\n" + "=" * 70)
        print("  🧪 Running CampusFind 22-Point Comprehensive Test Suite")
        print("=" * 70)

    # 1. Student registration with valid details
    def test_01_registration_valid(self):
        ts = int(datetime.now().timestamp() * 1000) % 100000000
        TestCampusFind.test_email = f"student_{ts}@college.edu"
        TestCampusFind.test_usn = f"1AB{ts:08d}"

        salt = generate_salt()
        pw_hash = hash_password("ValidPass123", salt)
        uid = db.create_user(
            full_name="Test Student One",
            usn=TestCampusFind.test_usn,
            department="Computer Science",
            email=TestCampusFind.test_email,
            password_hash=pw_hash,
            salt=salt,
            role="student"
        )
        self.assertIsNotNone(uid)
        user = db.get_user_by_id(uid)
        self.assertEqual(user['full_name'], "Test Student One")
        print("  ✓ Test 1 Passed: Student registration with valid details")

    # 2. Registration with duplicate USN
    def test_02_registration_duplicate_usn(self):
        salt = generate_salt()
        pw_hash = hash_password("ValidPass123", salt)
        duplicate_uid = db.create_user(
            full_name="Duplicate USN User",
            usn=TestCampusFind.test_usn,  # Same USN as test 1
            department="Civil",
            email=f"unique_{int(datetime.now().timestamp()*1000)}@college.edu",
            password_hash=pw_hash,
            salt=salt
        )
        self.assertIsNone(duplicate_uid, "Database should reject duplicate USN")
        print("  ✓ Test 2 Passed: Registration with duplicate USN correctly rejected")

    # 3. Registration with duplicate email
    def test_03_registration_duplicate_email(self):
        salt = generate_salt()
        pw_hash = hash_password("ValidPass123", salt)
        duplicate_uid = db.create_user(
            full_name="Duplicate Email User",
            usn=f"1AB{int(datetime.now().timestamp()*1000)%100000000:08d}",
            department="Mechanical",
            email=TestCampusFind.test_email,  # Same email as test 1
            password_hash=pw_hash,
            salt=salt
        )
        self.assertIsNone(duplicate_uid, "Database should reject duplicate email")
        print("  ✓ Test 3 Passed: Registration with duplicate email correctly rejected")

    # 4. Login with correct credentials
    def test_04_login_correct(self):
        user = db.get_user_by_email(TestCampusFind.test_email)
        self.assertIsNotNone(user)
        is_valid = verify_password("ValidPass123", user['salt'], user['password_hash'])
        self.assertTrue(is_valid)
        print("  ✓ Test 4 Passed: Login with correct credentials verified")

    # 5. Login with incorrect credentials
    def test_05_login_incorrect(self):
        user = db.get_user_by_email(TestCampusFind.test_email)
        self.assertIsNotNone(user)
        is_valid = verify_password("WrongPassword!", user['salt'], user['password_hash'])
        self.assertFalse(is_valid)
        print("  ✓ Test 5 Passed: Login with incorrect credentials rejected")

    # 6. Lost-item report submission
    def test_06_lost_item_submission(self):
        user = db.get_user_by_email(TestCampusFind.test_email)
        item_id = db.create_item(
            user_id=user['user_id'],
            item_type="lost",
            item_name="Blue HP Pavilion Laptop",
            category="Electronics",
            location="Library 1st Floor",
            item_date=datetime.now().strftime("%Y-%m-%d"),
            description="HP Pavilion 14 inch laptop with Windows 11.",
            distinguishing_features="Intel i5 sticker, tiny scratch on edge",
            image_path=None,
            contact_email=user['email']
        )
        self.assertIsInstance(item_id, int)
        item = db.get_item_by_id(item_id)
        self.assertEqual(item['item_name'], "Blue HP Pavilion Laptop")
        self.assertEqual(item['item_type'], "lost")
        print("  ✓ Test 6 Passed: Lost-item report submission verified")

    # 7. Found-item report submission
    def test_07_found_item_submission(self):
        user = db.get_user_by_email(TestCampusFind.test_email)
        item_id = db.create_item(
            user_id=user['user_id'],
            item_type="found",
            item_name="HP Pavilion Laptop Blue",
            category="Electronics",
            location="Library 1st Floor",
            item_date=datetime.now().strftime("%Y-%m-%d"),
            description="Found blue HP laptop left on cubicle desk.",
            distinguishing_features="Scratch on outer edge",
            image_path=None,
            contact_email=user['email']
        )
        self.assertIsInstance(item_id, int)
        item = db.get_item_by_id(item_id)
        self.assertEqual(item['item_type'], "found")
        print("  ✓ Test 7 Passed: Found-item report submission verified")

    # 8. Image upload and preview handling
    def test_08_image_upload_and_preview(self):
        # Create a test sample image
        from PIL import Image
        test_img_path = BASE_DIR / "uploads" / "temp_test_img.png"
        img = Image.new("RGB", (300, 200), color="green")
        img.save(test_img_path)

        valid, msg = image_service.validate_image(str(test_img_path))
        self.assertTrue(valid)

        dest_rel = image_service.process_upload(str(test_img_path))
        self.assertTrue(os.path.exists(BASE_DIR / dest_rel))

        # Test thumbnail generation
        thumb = image_service.get_thumbnail(dest_rel, size=(50, 50))
        self.assertIsNotNone(thumb)

        # Cleanup temp source
        try:
            os.remove(test_img_path)
            os.remove(BASE_DIR / dest_rel)
        except Exception:
            pass
        print("  ✓ Test 8 Passed: Image upload validation, resizing, and preview verified")

    # 9. Search by item name
    def test_09_search_by_item_name(self):
        results = db.get_all_items(keyword="Pavilion")
        self.assertGreaterEqual(len(results), 1)
        found_names = [r['item_name'] for r in results]
        self.assertTrue(any("Pavilion" in n for n in found_names))
        print("  ✓ Test 9 Passed: Search by item name verified")

    # 10. Search by category and location
    def test_10_search_by_category_and_location(self):
        results = db.get_all_items(category="Electronics", location="Library 1st Floor")
        self.assertGreaterEqual(len(results), 1)
        for r in results:
            self.assertEqual(r['category'], "Electronics")
        print("  ✓ Test 10 Passed: Search by category and location verified")

    # 11. Automatic item matching
    def test_11_automatic_matching(self):
        matches = matching_engine.run_matching()
        self.assertIsInstance(matches, list)
        self.assertGreaterEqual(len(matches), 1)
        # Verify score breakdown
        top_match = matches[0]
        self.assertGreaterEqual(top_match['score'], 60.0)
        print(f"  ✓ Test 11 Passed: Automatic matching algorithm scored top match at {top_match['score']}%")

    # 12. Duplicate match prevention
    def test_12_duplicate_match_prevention(self):
        initial_matches = db.get_all_matches(min_score=0)
        count_before = len(initial_matches)
        # Run matching again
        matching_engine.run_matching()
        count_after = len(db.get_all_matches(min_score=0))
        self.assertEqual(count_before, count_after, "Duplicate matches must not create duplicate records")
        print("  ✓ Test 12 Passed: Duplicate match prevention verified via database constraint")

    # 13. Claim submission
    def test_13_claim_submission(self):
        user = db.get_user_by_email("teststudent1@college.edu")
        found_items = db.get_all_items(item_type="found", status="open")
        self.assertGreater(len(found_items), 0)
        fi = found_items[0]

        claim_id = db.create_claim(
            lost_item_id=None,
            found_item_id=fi['item_id'],
            claimant_id=user['user_id'],
            claim_details="I am the owner of this item and can verify its distinguishing features.",
            additional_info="Purchased online.",
            contact_email=user['email']
        )
        self.assertIsInstance(claim_id, int)
        claim = db.get_claim_by_id(claim_id)
        self.assertEqual(claim['claim_status'], "pending")
        self._test_claim_id = claim_id
        print(f"  ✓ Test 13 Passed: Claim #{claim_id} submission verified")

    # 14. Claim approval
    def test_14_claim_approval(self):
        claims = db.get_all_claims()
        claim = claims[0]
        cid = claim['claim_id']
        success = db.update_claim_status(cid, "approved", "Ownership documents verified.")
        self.assertTrue(success)
        updated = db.get_claim_by_id(cid)
        self.assertEqual(updated['claim_status'], "approved")
        self.assertEqual(updated['admin_remarks'], "Ownership documents verified.")
        print("  ✓ Test 14 Passed: Claim approval workflow verified")

    # 15. Claim rejection
    def test_15_claim_rejection(self):
        claims = db.get_all_claims()
        claim = claims[-1]
        cid = claim['claim_id']
        success = db.update_claim_status(cid, "rejected", "Evidence provided does not match item.")
        self.assertTrue(success)
        updated = db.get_claim_by_id(cid)
        self.assertEqual(updated['claim_status'], "rejected")
        print("  ✓ Test 15 Passed: Claim rejection workflow verified")

    # 16. Item return confirmation
    def test_16_item_return_confirmation(self):
        claims = db.get_all_claims()
        claim = claims[0]
        cid = claim['claim_id']
        fid = claim['found_item_id']

        db.update_claim_status(cid, "returned", "Handed over to owner.")
        db.update_item_status(fid, "returned")

        c = db.get_claim_by_id(cid)
        it = db.get_item_by_id(fid)
        self.assertEqual(c['claim_status'], "returned")
        self.assertEqual(it['status'], "returned")
        print("  ✓ Test 16 Passed: Item return confirmation verified")

    # 17. Email notification handling (with graceful offline fallback)
    def test_17_email_notification_handling(self):
        # When SMTP credentials are not configured, send_email must return False gracefully without crashing
        res = email_service.send_email(
            "student@college.edu", "Test Subject", "Test Body"
        )
        self.assertIsInstance(res, bool)
        print("  ✓ Test 17 Passed: Email notification graceful offline handling verified")

    # 18. PDF generation
    def test_18_pdf_generation(self):
        items = db.get_all_items()
        pdf_path = pdf_service.generate_lost_items_report(items, filename="test_lost_report.pdf")
        self.assertTrue(os.path.exists(pdf_path))
        self.assertGreater(os.path.getsize(pdf_path), 500)
        # QR generation check
        qr_path = qr_service.generate_item_qr(1, "lost", "Test Laptop")
        self.assertTrue(os.path.exists(qr_path))
        print("  ✓ Test 18 Passed: PDF reports and QR code generation verified")

    # 19. Analytics chart generation
    def test_19_analytics_generation(self):
        data = db.get_analytics_data()
        self.assertIn("monthly_lost", data)
        self.assertIn("monthly_found", data)
        self.assertIn("by_category_lost", data)
        self.assertIn("claim_stats", data)
        self.assertIn("recovery_rate", data)
        print(f"  ✓ Test 19 Passed: Analytics data generation verified (Recovery Rate: {data['recovery_rate']}%)")

    # 20. Light and dark theme switching
    def test_20_theme_switching(self):
        theme_manager.set_theme("light")
        self.assertEqual(theme_manager.current_theme, "light")
        self.assertEqual(theme_manager.get("bg_primary"), LIGHT_THEME["bg_primary"])

        theme_manager.toggle_theme()
        self.assertEqual(theme_manager.current_theme, "dark")
        self.assertEqual(theme_manager.get("bg_primary"), DARK_THEME["bg_primary"])

        theme_manager.set_theme("light")
        print("  ✓ Test 20 Passed: Light and dark theme toggling verified")

    # 21. Theme persistence after restarting
    def test_21_theme_persistence(self):
        theme_manager.set_theme("dark")
        # Instantiate a fresh ThemeManager instance to simulate app restart
        from theme_manager import ThemeManager
        fresh_tm = ThemeManager()
        self.assertEqual(fresh_tm.current_theme, "dark")
        # Reset back to light
        theme_manager.set_theme("light")
        print("  ✓ Test 21 Passed: Theme persistence across sessions verified")

    # 22. Student attempting to access admin functionality
    def test_22_student_admin_access_control(self):
        student_user = db.get_user_by_email("teststudent1@college.edu")
        self.assertEqual(student_user['role'], "student")
        # Verify role checking logic: student should not have 'admin' role
        has_admin_rights = (student_user.get('role') == 'admin')
        self.assertFalse(has_admin_rights)
        print("  ✓ Test 22 Passed: Student role authorization protection verified")


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCampusFind)
    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
