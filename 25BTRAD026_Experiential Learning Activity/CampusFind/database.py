"""
CampusFind - Database Layer
SQLite database manager with full CRUD for all entities.
"""
import sqlite3
from datetime import datetime, date
from typing import Any, Optional

from config import DB_PATH


class DatabaseManager:
    """Central SQLite database manager for CampusFind."""

    # ------------------------------------------------------------------ #
    #  Initialisation                                                      #
    # ------------------------------------------------------------------ #

    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.execute("PRAGMA journal_mode = WAL")
        self.conn.commit()
        self.initialize_database()

    # ------------------------------------------------------------------ #
    #  Utility                                                             #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _row_to_dict(row, cursor=None) -> dict:
        """Convert a sqlite3.Row (or plain tuple) to a plain dict."""
        if row is None:
            return None
        if isinstance(row, sqlite3.Row):
            return dict(row)
        if cursor is not None:
            cols = [d[0] for d in cursor.description]
            return dict(zip(cols, row))
        return {}

    def _fetchone(self, sql: str, params=()) -> Optional[dict]:
        cur = self.conn.execute(sql, params)
        row = cur.fetchone()
        return self._row_to_dict(row) if row else None

    def _fetchall(self, sql: str, params=()) -> list:
        cur = self.conn.execute(sql, params)
        return [self._row_to_dict(r) for r in cur.fetchall()]

    # ------------------------------------------------------------------ #
    #  Schema                                                              #
    # ------------------------------------------------------------------ #

    def initialize_database(self):
        """Create all tables and indexes if they do not exist."""
        ddl = """
        CREATE TABLE IF NOT EXISTS users (
            user_id          INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name        TEXT NOT NULL,
            usn              TEXT UNIQUE NOT NULL,
            department       TEXT,
            email            TEXT UNIQUE NOT NULL,
            password_hash    TEXT NOT NULL,
            salt             TEXT NOT NULL,
            role             TEXT DEFAULT 'student',
            theme_preference TEXT DEFAULT 'light',
            created_at       DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS items (
            item_id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id                  INTEGER,
            item_type                TEXT NOT NULL,
            item_name                TEXT NOT NULL,
            category                 TEXT,
            location                 TEXT,
            item_date                DATE,
            description              TEXT,
            distinguishing_features  TEXT,
            image_path               TEXT,
            status                   TEXT DEFAULT 'open',
            contact_email            TEXT,
            created_at               DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS claims (
            claim_id        INTEGER PRIMARY KEY AUTOINCREMENT,
            lost_item_id    INTEGER,
            found_item_id   INTEGER,
            claimant_id     INTEGER,
            claim_details   TEXT,
            additional_info TEXT,
            contact_email   TEXT,
            admin_remarks   TEXT,
            claim_status    TEXT DEFAULT 'pending',
            created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(lost_item_id)  REFERENCES items(item_id),
            FOREIGN KEY(found_item_id) REFERENCES items(item_id),
            FOREIGN KEY(claimant_id)   REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS matches (
            match_id          INTEGER PRIMARY KEY AUTOINCREMENT,
            lost_item_id      INTEGER,
            found_item_id     INTEGER,
            similarity_score  REAL,
            name_score        REAL,
            category_score    REAL,
            location_score    REAL,
            date_score        REAL,
            description_score REAL,
            match_status      TEXT DEFAULT 'active',
            created_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(lost_item_id, found_item_id),
            FOREIGN KEY(lost_item_id)  REFERENCES items(item_id),
            FOREIGN KEY(found_item_id) REFERENCES items(item_id)
        );

        CREATE TABLE IF NOT EXISTS notifications (
            notification_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id           INTEGER,
            title             TEXT,
            message           TEXT,
            notification_type TEXT DEFAULT 'info',
            is_read           INTEGER DEFAULT 0,
            created_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS activity_log (
            log_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER,
            action     TEXT,
            details    TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS settings (
            setting_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            setting_key   TEXT UNIQUE NOT NULL,
            setting_value TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_items_item_type  ON items(item_type);
        CREATE INDEX IF NOT EXISTS idx_items_category   ON items(category);
        CREATE INDEX IF NOT EXISTS idx_items_status     ON items(status);
        CREATE INDEX IF NOT EXISTS idx_items_user_id    ON items(user_id);
        CREATE INDEX IF NOT EXISTS idx_claims_status    ON claims(claim_status);
        CREATE INDEX IF NOT EXISTS idx_matches_lost     ON matches(lost_item_id);
        CREATE INDEX IF NOT EXISTS idx_matches_found    ON matches(found_item_id);
        CREATE INDEX IF NOT EXISTS idx_notif_user       ON notifications(user_id);
        """
        self.conn.executescript(ddl)
        self.conn.commit()

    # ================================================================== #
    #  USERS                                                               #
    # ================================================================== #

    def create_user(self, full_name: str, usn: str, department: str,
                    email: str, password_hash: str, salt: str,
                    role: str = 'student') -> Optional[int]:
        """Insert a new user. Returns user_id or None on duplicate."""
        try:
            cur = self.conn.execute(
                """INSERT INTO users (full_name, usn, department, email,
                   password_hash, salt, role)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (full_name, usn, department, email, password_hash, salt, role)
            )
            self.conn.commit()
            return cur.lastrowid
        except sqlite3.IntegrityError:
            return None

    def get_user_by_email(self, email: str) -> Optional[dict]:
        return self._fetchone("SELECT * FROM users WHERE email = ?", (email,))

    def get_user_by_usn(self, usn: str) -> Optional[dict]:
        return self._fetchone("SELECT * FROM users WHERE usn = ?", (usn,))

    def get_user_by_id(self, user_id: int) -> Optional[dict]:
        return self._fetchone("SELECT * FROM users WHERE user_id = ?", (user_id,))

    def get_all_users(self) -> list:
        return self._fetchall("SELECT * FROM users ORDER BY created_at DESC")

    def update_user(self, user_id: int, **kwargs) -> bool:
        if not kwargs:
            return False
        allowed = {"full_name", "usn", "department", "email",
                   "password_hash", "salt", "role", "theme_preference"}
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if not fields:
            return False
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [user_id]
        cur = self.conn.execute(
            f"UPDATE users SET {set_clause} WHERE user_id = ?", values
        )
        self.conn.commit()
        return cur.rowcount > 0

    def delete_user(self, user_id: int) -> bool:
        cur = self.conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        self.conn.commit()
        return cur.rowcount > 0

    def update_theme(self, user_id: int, theme: str) -> None:
        self.conn.execute(
            "UPDATE users SET theme_preference = ? WHERE user_id = ?",
            (theme, user_id)
        )
        self.conn.commit()

    # ================================================================== #
    #  ITEMS                                                               #
    # ================================================================== #

    def create_item(self, user_id: int, item_type: str, item_name: str,
                    category: str, location: str, item_date,
                    description: str, distinguishing_features: str,
                    image_path: str, contact_email: str) -> int:
        cur = self.conn.execute(
            """INSERT INTO items (user_id, item_type, item_name, category,
               location, item_date, description, distinguishing_features,
               image_path, contact_email)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, item_type, item_name, category, location, item_date,
             description, distinguishing_features, image_path, contact_email)
        )
        self.conn.commit()
        return cur.lastrowid

    def get_item_by_id(self, item_id: int) -> Optional[dict]:
        return self._fetchone("SELECT * FROM items WHERE item_id = ?", (item_id,))

    def get_items_by_user(self, user_id: int, item_type: str = None) -> list:
        if item_type:
            return self._fetchall(
                "SELECT * FROM items WHERE user_id = ? AND item_type = ? ORDER BY created_at DESC",
                (user_id, item_type)
            )
        return self._fetchall(
            "SELECT * FROM items WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        )

    def get_all_items(self, item_type: str = None, status: str = None,
                      category: str = None, location: str = None,
                      date_from=None, date_to=None, keyword: str = None) -> list:
        conditions = []
        params = []

        if item_type:
            conditions.append("item_type = ?")
            params.append(item_type)
        if status:
            conditions.append("status = ?")
            params.append(status)
        if category:
            conditions.append("category = ?")
            params.append(category)
        if location:
            conditions.append("location = ?")
            params.append(location)
        if date_from:
            conditions.append("item_date >= ?")
            params.append(str(date_from))
        if date_to:
            conditions.append("item_date <= ?")
            params.append(str(date_to))
        if keyword:
            conditions.append(
                "(item_name LIKE ? OR description LIKE ? OR distinguishing_features LIKE ?)"
            )
            like = f"%{keyword}%"
            params.extend([like, like, like])

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        return self._fetchall(
            f"SELECT * FROM items {where} ORDER BY created_at DESC",
            params
        )

    def update_item_status(self, item_id: int, status: str) -> bool:
        cur = self.conn.execute(
            "UPDATE items SET status = ? WHERE item_id = ?", (status, item_id)
        )
        self.conn.commit()
        return cur.rowcount > 0

    def update_item(self, item_id: int, **kwargs) -> bool:
        if not kwargs:
            return False
        allowed = {"item_type", "item_name", "category", "location",
                   "item_date", "description", "distinguishing_features",
                   "image_path", "status", "contact_email"}
        fields = {k: v for k, v in kwargs.items() if k in allowed}
        if not fields:
            return False
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [item_id]
        cur = self.conn.execute(
            f"UPDATE items SET {set_clause} WHERE item_id = ?", values
        )
        self.conn.commit()
        return cur.rowcount > 0

    def delete_item(self, item_id: int) -> bool:
        cur = self.conn.execute("DELETE FROM items WHERE item_id = ?", (item_id,))
        self.conn.commit()
        return cur.rowcount > 0

    def get_item_counts(self) -> dict:
        row = self._fetchone(
            """SELECT
                COUNT(*) FILTER (WHERE item_type='lost') AS total_lost,
                COUNT(*) FILTER (WHERE item_type='found') AS total_found,
                COUNT(*) FILTER (WHERE item_type='lost' AND status='open') AS open_lost,
                COUNT(*) FILTER (WHERE item_type='found' AND status='open') AS open_found,
                COUNT(*) FILTER (WHERE status='closed') AS closed
               FROM items"""
        )
        if row:
            return dict(row)
        return {"total_lost": 0, "total_found": 0,
                "open_lost": 0, "open_found": 0, "closed": 0}

    # ================================================================== #
    #  CLAIMS                                                              #
    # ================================================================== #

    def create_claim(self, lost_item_id: int, found_item_id: int,
                     claimant_id: int, claim_details: str,
                     additional_info: str, contact_email: str) -> int:
        cur = self.conn.execute(
            """INSERT INTO claims (lost_item_id, found_item_id, claimant_id,
               claim_details, additional_info, contact_email)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (lost_item_id, found_item_id, claimant_id,
             claim_details, additional_info, contact_email)
        )
        self.conn.commit()
        return cur.lastrowid

    def get_claim_by_id(self, claim_id: int) -> Optional[dict]:
        return self._fetchone(
            "SELECT * FROM claims WHERE claim_id = ?", (claim_id,)
        )

    def get_claims_by_user(self, user_id: int) -> list:
        return self._fetchall(
            "SELECT * FROM claims WHERE claimant_id = ? ORDER BY created_at DESC",
            (user_id,)
        )

    def get_all_claims(self) -> list:
        sql = """
        SELECT c.*,
               li.item_name AS lost_item_name,
               fi.item_name AS found_item_name,
               u.full_name  AS claimant_name,
               u.email      AS claimant_email
        FROM claims c
        LEFT JOIN items li ON c.lost_item_id  = li.item_id
        LEFT JOIN items fi ON c.found_item_id = fi.item_id
        LEFT JOIN users u  ON c.claimant_id   = u.user_id
        ORDER BY c.created_at DESC
        """
        return self._fetchall(sql)

    def update_claim_status(self, claim_id: int, status: str,
                            admin_remarks: str = None) -> bool:
        if admin_remarks is not None:
            cur = self.conn.execute(
                """UPDATE claims
                   SET claim_status = ?, admin_remarks = ?,
                       updated_at = CURRENT_TIMESTAMP
                   WHERE claim_id = ?""",
                (status, admin_remarks, claim_id)
            )
        else:
            cur = self.conn.execute(
                """UPDATE claims
                   SET claim_status = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE claim_id = ?""",
                (status, claim_id)
            )
        self.conn.commit()
        return cur.rowcount > 0

    def get_claim_counts(self) -> dict:
        row = self._fetchone(
            """SELECT
                COUNT(*) FILTER (WHERE claim_status='pending')      AS pending,
                COUNT(*) FILTER (WHERE claim_status='under_review') AS under_review,
                COUNT(*) FILTER (WHERE claim_status='approved')     AS approved,
                COUNT(*) FILTER (WHERE claim_status='rejected')     AS rejected,
                COUNT(*) FILTER (WHERE claim_status='returned')     AS returned
               FROM claims"""
        )
        if row:
            return dict(row)
        return {"pending": 0, "under_review": 0,
                "approved": 0, "rejected": 0, "returned": 0}

    # ================================================================== #
    #  MATCHES                                                             #
    # ================================================================== #

    def create_or_update_match(self, lost_item_id: int, found_item_id: int,
                               similarity_score: float, name_score: float,
                               category_score: float, location_score: float,
                               date_score: float,
                               description_score: float) -> int:
        cur = self.conn.execute(
            """INSERT INTO matches
               (lost_item_id, found_item_id, similarity_score, name_score,
                category_score, location_score, date_score, description_score)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(lost_item_id, found_item_id) DO UPDATE SET
                 similarity_score  = excluded.similarity_score,
                 name_score        = excluded.name_score,
                 category_score    = excluded.category_score,
                 location_score    = excluded.location_score,
                 date_score        = excluded.date_score,
                 description_score = excluded.description_score,
                 match_status      = 'active',
                 created_at        = CURRENT_TIMESTAMP""",
            (lost_item_id, found_item_id, similarity_score, name_score,
             category_score, location_score, date_score, description_score)
        )
        self.conn.commit()
        return cur.lastrowid or self._fetchone(
            "SELECT match_id FROM matches WHERE lost_item_id=? AND found_item_id=?",
            (lost_item_id, found_item_id)
        )["match_id"]

    def get_matches_for_user(self, user_id: int, min_score: float = 60) -> list:
        sql = """
        SELECT m.*,
               li.item_name  AS lost_item_name,
               li.category   AS lost_category,
               li.location   AS lost_location,
               fi.item_name  AS found_item_name,
               fi.category   AS found_category,
               fi.location   AS found_location,
               lu.full_name  AS lost_owner_name,
               fu.full_name  AS found_owner_name
        FROM matches m
        JOIN items li ON m.lost_item_id  = li.item_id
        JOIN items fi ON m.found_item_id = fi.item_id
        JOIN users lu ON li.user_id = lu.user_id
        JOIN users fu ON fi.user_id = fu.user_id
        WHERE m.similarity_score >= ?
          AND m.match_status = 'active'
          AND (li.user_id = ? OR fi.user_id = ?)
        ORDER BY m.similarity_score DESC
        """
        return self._fetchall(sql, (min_score, user_id, user_id))

    def get_all_matches(self, min_score: float = 60) -> list:
        sql = """
        SELECT m.*,
               li.item_name  AS lost_item_name,
               li.category   AS lost_category,
               li.location   AS lost_location,
               fi.item_name  AS found_item_name,
               fi.category   AS found_category,
               fi.location   AS found_location
        FROM matches m
        JOIN items li ON m.lost_item_id  = li.item_id
        JOIN items fi ON m.found_item_id = fi.item_id
        WHERE m.similarity_score >= ?
          AND m.match_status = 'active'
        ORDER BY m.similarity_score DESC
        """
        return self._fetchall(sql, (min_score,))

    def deactivate_match(self, match_id: int) -> bool:
        cur = self.conn.execute(
            "UPDATE matches SET match_status = 'inactive' WHERE match_id = ?",
            (match_id,)
        )
        self.conn.commit()
        return cur.rowcount > 0

    # ================================================================== #
    #  NOTIFICATIONS                                                       #
    # ================================================================== #

    def create_notification(self, user_id: int, title: str, message: str,
                            notification_type: str = 'info') -> int:
        cur = self.conn.execute(
            """INSERT INTO notifications (user_id, title, message, notification_type)
               VALUES (?, ?, ?, ?)""",
            (user_id, title, message, notification_type)
        )
        self.conn.commit()
        return cur.lastrowid

    def get_notifications(self, user_id: int, unread_only: bool = False,
                          limit: int = 50) -> list:
        where = "WHERE user_id = ?"
        params = [user_id]
        if unread_only:
            where += " AND is_read = 0"
        return self._fetchall(
            f"SELECT * FROM notifications {where} ORDER BY created_at DESC LIMIT ?",
            params + [limit]
        )

    def mark_notification_read(self, notification_id: int) -> bool:
        cur = self.conn.execute(
            "UPDATE notifications SET is_read = 1 WHERE notification_id = ?",
            (notification_id,)
        )
        self.conn.commit()
        return cur.rowcount > 0

    def mark_all_read(self, user_id: int) -> bool:
        cur = self.conn.execute(
            "UPDATE notifications SET is_read = 1 WHERE user_id = ? AND is_read = 0",
            (user_id,)
        )
        self.conn.commit()
        return cur.rowcount > 0

    def get_unread_count(self, user_id: int) -> int:
        row = self._fetchone(
            "SELECT COUNT(*) AS cnt FROM notifications WHERE user_id = ? AND is_read = 0",
            (user_id,)
        )
        return row["cnt"] if row else 0

    # ================================================================== #
    #  ACTIVITY LOG                                                        #
    # ================================================================== #

    def log_activity(self, user_id: int, action: str, details: str = '') -> None:
        self.conn.execute(
            "INSERT INTO activity_log (user_id, action, details) VALUES (?, ?, ?)",
            (user_id, action, details)
        )
        self.conn.commit()

    # ================================================================== #
    #  SETTINGS                                                            #
    # ================================================================== #

    def get_setting(self, key: str, default=None) -> Optional[str]:
        row = self._fetchone(
            "SELECT setting_value FROM settings WHERE setting_key = ?", (key,)
        )
        return row["setting_value"] if row else default

    def set_setting(self, key: str, value: str) -> None:
        self.conn.execute(
            """INSERT INTO settings (setting_key, setting_value) VALUES (?, ?)
               ON CONFLICT(setting_key) DO UPDATE SET setting_value = excluded.setting_value""",
            (key, value)
        )
        self.conn.commit()

    # ================================================================== #
    #  ANALYTICS                                                           #
    # ================================================================== #

    def get_analytics_data(self) -> dict:
        # Monthly lost/found for the last 12 months
        monthly_lost = self._fetchall(
            """SELECT strftime('%Y-%m', item_date) AS month_str, COUNT(*) AS cnt
               FROM items
               WHERE item_type = 'lost'
                 AND item_date >= date('now', '-12 months')
               GROUP BY month_str
               ORDER BY month_str"""
        )
        monthly_found = self._fetchall(
            """SELECT strftime('%Y-%m', item_date) AS month_str, COUNT(*) AS cnt
               FROM items
               WHERE item_type = 'found'
                 AND item_date >= date('now', '-12 months')
               GROUP BY month_str
               ORDER BY month_str"""
        )

        by_category_lost = self._fetchall(
            """SELECT category, COUNT(*) AS cnt
               FROM items WHERE item_type='lost' GROUP BY category ORDER BY cnt DESC"""
        )
        by_category_found = self._fetchall(
            """SELECT category, COUNT(*) AS cnt
               FROM items WHERE item_type='found' GROUP BY category ORDER BY cnt DESC"""
        )
        by_location = self._fetchall(
            """SELECT location, COUNT(*) AS cnt
               FROM items GROUP BY location ORDER BY cnt DESC"""
        )

        claim_counts = self.get_claim_counts()
        total_claims = sum(claim_counts.values())
        returned = claim_counts.get("returned", 0)
        recovery_rate = (returned / total_claims * 100) if total_claims > 0 else 0.0

        return {
            "monthly_lost": [(r["month_str"], r["cnt"]) for r in monthly_lost],
            "monthly_found": [(r["month_str"], r["cnt"]) for r in monthly_found],
            "by_category_lost": [(r["category"], r["cnt"]) for r in by_category_lost],
            "by_category_found": [(r["category"], r["cnt"]) for r in by_category_found],
            "by_location": [(r["location"], r["cnt"]) for r in by_location],
            "claim_stats": claim_counts,
            "recovery_rate": round(recovery_rate, 2),
        }

    # ------------------------------------------------------------------ #
    #  Close                                                               #
    # ------------------------------------------------------------------ #

    def close(self) -> None:
        """Close the database connection."""
        try:
            self.conn.close()
        except Exception:
            pass


# Global singleton
db = DatabaseManager()
