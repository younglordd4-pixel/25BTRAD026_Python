# CampusFind – Smart College Lost and Found Management System

**CampusFind** is an enterprise-grade, university-level desktop application designed to streamline the reporting, tracking, matching, claiming, and recovery of lost belongings on a college campus. 

Developed with **Python 3**, **CustomTkinter**, and **SQLite**, it provides a fluid, responsive graphical interface supporting dynamic **Light and Dark mode** transitions, automatic weighted similarity matching, claim adjudication workflows, PDF export capabilities, and analytics visualization.

---

## 📸 Key Application Features

1. **Student & Administrator Portals**
   - **Role-Based Access Control**: Strict segregation between Student and Administrator capabilities.
   - **Personalized Dashboards**: Statistical cards, recent activity logs, and real-time system notifications.
   - **Profile & Notification Center**: Top navigation bar includes quick notification dismissals and profile details.

2. **Lost & Found Reporting Modules**
   - Multi-category categorization (*Electronics, Books & Stationery, Personal Belongings, Keys, ID Cards, etc.*).
   - Campus location tracking with custom specific-spot entries.
   - Image upload module with automatic thumbnail generation and proportional aspect ratio scaling.
   - Privacy safeguards for sensitive items (student ID cards, wallets, and government documentation).

3. **Automatic Item Matching System (Weighted Multi-Factor Algorithm)**
   - **Item Name Similarity (30 points)**: Utilizes sequence matching via `difflib.SequenceMatcher`.
   - **Category Match (20 points)**: Strict verification against taxonomy.
   - **Location Proximity (20 points)**: Exact and sub-zone matching.
   - **Date Proximity (15 points)**: Temporal proximity decay curve (0–3 days: 15 pts, 4–7 days: 10 pts, etc.).
   - **Description Keyword Overlap (15 points)**: Stopword-filtered token set intersection.
   - **Match Classification**:
     - 🟢 **80% – 100%**: Strong possible match.
     - 🟠 **60% – 79%**: Moderate possible match.
     - ⚪ **Below 60%**: Filtered out automatically.
   - Matches are recorded in SQLite with duplicate constraint protection.

4. **Claim Management & Adjudication**
   - Students can file ownership claims citing specific proof of ownership, private marks, and purchase receipts.
   - Status pipeline: `Pending` ➔ `Under Review` ➔ `Approved` / `Rejected` ➔ `Returned`.
   - Administrators review lost vs. found claims side-by-side with photo verification, input remarks, and finalize item return.

5. **Advanced Search & Filtering**
   - Search across title, description, features, and keywords.
   - Filter by Item Type (*Lost / Found*), Category, Campus Location, and Status.
   - Paginated grid layout with responsive item cards and detailed inspection modals.

6. **Interactive Visual Analytics (Matplotlib)**
   - Monthly Lost vs. Found comparison bar chart.
   - Category distribution charts for lost and found items.
   - Time-series monthly activity trend lines.
   - Claim resolution distribution pie chart.
   - High-activity campus location rankings.
   - Real-time recovery percentage tracking.

7. **Document Generation & QR Codes**
   - **PDF Reports (ReportLab)**: Lost item logs, found item registries, claim histories, student summaries, and campus-wide analytics reports.
   - **QR Code Tracking (qrcode)**: Non-sensitive reference QR codes generated per report for physical tags.

8. **Dynamic Light & Dark Theming**
   - Instant theme toggle via the sun/moon icon in the top navigation bar.
   - Updates backgrounds, cards, sidebar, table borders, text colors, and chart palettes without restarting.
   - Persists user preference across application sessions.

---

## 🛠 Technology Stack

- **Language**: Python 3.10+
- **GUI Framework**: CustomTkinter
- **Database**: SQLite (WAL mode, Foreign Key constraints enforced)
- **Image Processing**: Pillow (PIL)
- **Data Visualization**: Matplotlib
- **PDF Generation**: ReportLab
- **QR Code Engine**: qrcode
- **Password Security**: Salted PBKDF2-HMAC-SHA256 (310,000 iterations)
- **Email Service**: Python standard `smtplib` and `email.message`

---

## 📂 Project Structure

```
CampusFind/
│
├── main.py                      # Application entry point & screen coordinator
├── config.py                    # Global configuration & environment constants
├── database.py                  # SQLite database manager & CRUD operations
├── theme_manager.py             # Central theme system (Light & Dark palettes)
├── setup_admin.py               # First-run secure administrator creation CLI
├── seed_data.py                 # Realistic sample data generator for demos
├── test_suite.py                # 22-point automated verification suite
├── requirements.txt             # Project dependencies
├── README.md                    # System documentation
│
├── authentication/
│   ├── __init__.py
│   ├── login.py                 # Student/Admin login frame
│   ├── registration.py          # Student self-registration frame
│   └── security.py              # Password hashing & regex validators
│
├── student/
│   ├── __init__.py
│   ├── dashboard.py             # Student dashboard with stats & quick actions
│   ├── lost_items.py            # Lost item report form & My Reports view
│   ├── found_items.py           # Found item registration form
│   ├── search.py                # Dedicated item search with pagination
│   ├── matching.py              # Automatic matching engine & match cards
│   └── claims.py                # Claim submission dialog & claims tracker
│
├── admin/
│   ├── __init__.py
│   ├── dashboard.py             # Administrator dashboard & KPI overview
│   ├── users.py                 # User account management & role promotions
│   ├── reports.py               # All item reports management & status editor
│   ├── claim_review.py          # Claim review modal, remarks & approval
│   └── analytics.py             # Matplotlib charts dashboard
│
├── services/
│   ├── __init__.py
│   ├── image_service.py         # Image upload, thumbnailing & validation
│   ├── email_service.py         # SMTP email dispatcher with offline fallback
│   ├── pdf_service.py           # ReportLab PDF report generation
│   ├── qr_service.py            # QR code creation & display
│   └── analytics_service.py     # Matplotlib figure builder
│
├── database/
│   └── campusfind.db            # SQLite database file
│
├── uploads/                     # Uploaded item photographs
├── exports/                     # Generated PDF reports and QR code PNGs
└── assets/                      # Icons and UI resources
```

---

## 🚀 Installation & Running

### 1. Prerequisites
Ensure Python 3.10 or higher is installed on your system.

### 2. Install Dependencies
Open a terminal in the `CampusFind` project directory and run:

```bash
pip install -r requirements.txt
```

### 3. Initialize Demo & Test Data (Optional but Recommended)
To populate realistic college demonstration data (students, reports, matching pairs, and claims):

```bash
python seed_data.py
```

### 4. Create an Administrator Account
You can launch the secure interactive CLI setup tool to create an admin account:

```bash
python setup_admin.py
```

*Or use the pre-seeded demo accounts below.*

### 5. Launch the Application
Run the main script:

```bash
python main.py
```

---

## 🔑 Demo Login Credentials

If you ran `seed_data.py`, the following demo accounts are ready for use:

| Role | Email / USN | Password | Purpose |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin@campusfind.edu` / `ADMIN001` | `Admin@1234` | Full access to moderation, claims adjudication, user accounts, and analytics |
| **Student 1** | `aarav.sharma@college.edu` / `1AB22CS014` | `Student@123` | Reported lost Dell laptop; approved claim demo |
| **Student 2** | `priya.nair@college.edu` / `1AB22EC045` | `Student@123` | Reported found laptop; lost calculator under review |
| **Student 3** | `rahul.verma@college.edu` / `1AB21ME078` | `Student@123` | Reported lost wallet; returned item demo |
| **Student 4** | `sneha.patil@college.edu` / `1AB23IS032` | `Student@123` | Reported lost keys; pending claim demo |

---

## 📧 Email Notification Setup (Optional)

CampusFind operates completely offline by default. If you wish to enable real email notifications via SMTP (e.g. Gmail, Outlook, or institutional SMTP), configure the following environment variables:

```bash
# Windows PowerShell
$env:SMTP_HOST = "smtp.gmail.com"
$env:SMTP_PORT = "587"
$env:SMTP_USER = "your_email@gmail.com"
$env:SMTP_PASSWORD = "your_app_password"
$env:SMTP_FROM = "CampusFind Notifications <your_email@gmail.com>"
```

*If SMTP environment variables are not supplied, CampusFind safely suppresses email failures and logs notifications to the user's in-app notification center.*

---

## 🧪 Automated Test Suite

A complete 22-point unit test suite is included to verify all operational requirements:

```bash
python test_suite.py
```

### Verification Checklist:
- [x] Test 1: Student registration with valid details
- [x] Test 2: Registration with duplicate USN rejection
- [x] Test 3: Registration with duplicate email rejection
- [x] Test 4: Login with correct credentials
- [x] Test 5: Login with incorrect credentials rejection
- [x] Test 6: Lost-item report submission
- [x] Test 7: Found-item report submission
- [x] Test 8: Image upload validation, aspect ratio preservation, and preview
- [x] Test 9: Multi-keyword search across item names
- [x] Test 10: Multi-factor search by category and campus location
- [x] Test 11: Automatic item matching algorithm (100-point weighted score)
- [x] Test 12: Duplicate match prevention via SQL uniqueness constraints
- [x] Test 13: Student claim submission with ownership proof
- [x] Test 14: Administrator claim approval workflow
- [x] Test 15: Administrator claim rejection workflow
- [x] Test 16: Final item return status confirmation
- [x] Test 17: Email notification handling and graceful offline fallback
- [x] Test 18: PDF export generation and reference QR code generation
- [x] Test 19: Real-time analytics and recovery rate calculation
- [x] Test 20: Light and dark theme switching
- [x] Test 21: Theme persistence across application restarts
- [x] Test 22: Role-based access control protecting admin endpoints
