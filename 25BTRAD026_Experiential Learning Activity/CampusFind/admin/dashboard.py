"""
CampusFind – Admin Dashboard
Admin-facing overview: stats cards, recent claims, recent activity, quick actions.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import customtkinter as ctk
from tkinter import messagebox
import tkinter as tk
from datetime import datetime

from database import db
from services.pdf_service import pdf_service


# ── helpers ────────────────────────────────────────────────────────────────────

def _status_color(status: str, theme: dict) -> str:
    mapping = {
        "pending":      "#f57c00",
        "under_review": "#0277bd",
        "approved":     "#2d7a2d",
        "rejected":     "#c62828",
        "returned":     "#6b8f6b",
    }
    return mapping.get(str(status).lower(), theme.get("text_muted", "#6b8f6b"))


# ── Stats Card ─────────────────────────────────────────────────────────────────

class _StatCard(ctk.CTkFrame):
    def __init__(self, parent, label: str, value: str, icon: str,
                 accent: str, theme: dict, **kwargs):
        super().__init__(parent, corner_radius=12,
                         fg_color=theme.get("bg_card", "#ffffff"),
                         border_width=1,
                         border_color=theme.get("card_border", "#d4edd4"),
                         **kwargs)
        self._theme = theme

        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text=icon, font=("Segoe UI Emoji", 26),
                     text_color=accent).grid(row=0, column=0, pady=(14, 2))

        self._val_lbl = ctk.CTkLabel(
            self, text=str(value),
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=accent)
        self._val_lbl.grid(row=1, column=0, padx=14)

        ctk.CTkLabel(self, text=label,
                     font=ctk.CTkFont(size=11),
                     text_color=theme.get("text_muted", "#6b8f6b"),
                     wraplength=120).grid(row=2, column=0, padx=10, pady=(2, 14))

    def update_value(self, v):
        self._val_lbl.configure(text=str(v))


# ── Admin Dashboard ────────────────────────────────────────────────────────────

class AdminDashboard(ctk.CTkFrame):
    """Main admin landing frame."""

    # column spec for recent-claims mini-table
    _CLAIM_COLS = ("ID", "Lost Item", "Found Item", "Claimant", "Status", "Date")
    _CLAIM_WIDTHS = (40, 150, 150, 120, 110, 90)

    # column spec for activity log
    _ACT_COLS = ("Time", "User", "Action", "Details")
    _ACT_WIDTHS = (80, 100, 120, 220)

    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self._theme: dict = {}
        self._stat_cards: dict = {}

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)   # tables row expands

        self._build_header()
        self._build_stat_cards()
        self._build_tables_row()
        self._build_quick_actions()

        self.refresh_data()

    # ── build ──────────────────────────────────────────────────────────────────

    def _build_header(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 8))
        hdr.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(hdr, text="Admin Dashboard",
                     font=ctk.CTkFont(size=26, weight="bold"),
                     text_color=self._theme.get("text_primary", "#1a3a1a")
                     ).grid(row=0, column=0, sticky="w")

        self._subtitle = ctk.CTkLabel(hdr, text="Welcome, Admin",
                                      font=ctk.CTkFont(size=13),
                                      text_color=self._theme.get("text_muted", "#6b8f6b"))
        self._subtitle.grid(row=1, column=0, sticky="w")

        ctk.CTkButton(hdr, text="🔄 Refresh", width=110, height=32,
                      command=self.refresh_data,
                      font=ctk.CTkFont(size=12)).grid(row=0, column=1, sticky="e")

    def _build_stat_cards(self):
        sc = ctk.CTkFrame(self, fg_color="transparent")
        sc.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 10))
        for i in range(6):
            sc.grid_columnconfigure(i, weight=1, uniform="card")

        theme = self._theme
        specs = [
            ("total_students",  "👥", "Total Students",    "#0277bd"),
            ("total_lost",      "📋", "Total Lost Reports",  "#f57c00"),
            ("total_found",     "🔍", "Total Found Reports", "#2d7a2d"),
            ("pending",         "⏳", "Pending Claims",      "#f57c00"),
            ("approved",        "✅", "Approved Claims",     "#2d7a2d"),
            ("returned",        "📦", "Returned Items",      "#6b8f6b"),
        ]

        self._stat_frames = sc
        for col, (key, icon, label, accent) in enumerate(specs):
            card = _StatCard(sc, label=label, value="–", icon=icon,
                             accent=accent, theme=theme)
            card.grid(row=0, column=col, padx=6, pady=4, sticky="ew")
            self._stat_cards[key] = card

    def _build_tables_row(self):
        row_frame = ctk.CTkFrame(self, fg_color="transparent")
        row_frame.grid(row=2, column=0, sticky="nsew", padx=24, pady=4)
        row_frame.grid_columnconfigure(0, weight=1)
        row_frame.grid_columnconfigure(1, weight=1)
        row_frame.grid_rowconfigure(1, weight=1)

        # ── Left: recent claims ───────────────────────────────────────────────
        ctk.CTkLabel(row_frame, text="Recent Claims",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=self._theme.get("text_primary", "#1a3a1a")
                     ).grid(row=0, column=0, sticky="w", padx=4, pady=(4, 2))

        self._claims_frame = self._make_scroll_table(
            row_frame, self._CLAIM_COLS, self._CLAIM_WIDTHS,
            row=1, column=0)

        # ── Right: activity log ───────────────────────────────────────────────
        ctk.CTkLabel(row_frame, text="Recent Activity",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=self._theme.get("text_primary", "#1a3a1a")
                     ).grid(row=0, column=1, sticky="w", padx=(12, 4), pady=(4, 2))

        self._activity_frame = self._make_scroll_table(
            row_frame, self._ACT_COLS, self._ACT_WIDTHS,
            row=1, column=1, padx=(12, 0))

    def _make_scroll_table(self, parent, cols, widths, row, column, padx=(0, 0)):
        outer = ctk.CTkFrame(parent,
                             fg_color=self._theme.get("bg_card", "#ffffff"),
                             corner_radius=10,
                             border_width=1,
                             border_color=self._theme.get("card_border", "#d4edd4"))
        outer.grid(row=row, column=column, sticky="nsew", padx=padx, pady=2)
        outer.grid_columnconfigure(0, weight=1)
        outer.grid_rowconfigure(1, weight=1)

        # header row
        hdr = ctk.CTkFrame(outer,
                            fg_color=self._theme.get("table_header_bg", "#e8f5e8"),
                            corner_radius=0)
        hdr.grid(row=0, column=0, sticky="ew")
        for c, (col_name, w) in enumerate(zip(cols, widths)):
            ctk.CTkLabel(hdr, text=col_name, width=w,
                         font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=self._theme.get("text_primary", "#1a3a1a"),
                         anchor="w").grid(row=0, column=c, padx=(8, 2), pady=4, sticky="w")

        # scrollable body
        body = ctk.CTkScrollableFrame(outer,
                                      fg_color=self._theme.get("table_bg", "#ffffff"),
                                      corner_radius=0)
        body.grid(row=1, column=0, sticky="nsew")
        for c in range(len(cols)):
            body.grid_columnconfigure(c, weight=0)
        return body

    def _build_quick_actions(self):
        qa = ctk.CTkFrame(self, fg_color="transparent")
        qa.grid(row=3, column=0, sticky="ew", padx=24, pady=(8, 20))

        ctk.CTkLabel(qa, text="Quick Actions",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=self._theme.get("text_muted", "#6b8f6b")
                     ).grid(row=0, column=0, columnspan=5, sticky="w", pady=(0, 6))

        buttons = [
            ("👥 Manage Users",  lambda: self.controller.show_frame("admin_users")),
            ("📋 All Reports",   lambda: self.controller.show_frame("admin_reports")),
            ("⚖ Review Claims",  lambda: self.controller.show_frame("admin_claims")),
            ("📊 Analytics",     lambda: self.controller.show_frame("admin_analytics")),
            ("📄 Export Reports", self._export_pdf_dialog),
        ]

        for col, (text, cmd) in enumerate(buttons):
            ctk.CTkButton(qa, text=text, command=cmd,
                          height=38, corner_radius=8,
                          font=ctk.CTkFont(size=12)).grid(
                row=1, column=col, padx=6, sticky="ew")
            qa.grid_columnconfigure(col, weight=1)

    # ── data refresh ──────────────────────────────────────────────────────────

    def refresh_data(self):
        """Re-fetch all stats and repopulate tables."""
        self._refresh_stats()
        self._refresh_claims_table()
        self._refresh_activity_table()
        self._refresh_subtitle()

    def _refresh_subtitle(self):
        try:
            user = getattr(self.controller, "current_user", None)
            name = user.get("full_name", "Admin") if user else "Admin"
            self._subtitle.configure(text=f"Welcome, {name}")
        except Exception:
            pass

    def _refresh_stats(self):
        try:
            users = db.get_all_users()
            total_students = len([u for u in users if u.get("role") == "student"])

            item_counts = db.get_item_counts()
            claim_counts = db.get_claim_counts()

            self._stat_cards["total_students"].update_value(total_students)
            self._stat_cards["total_lost"].update_value(item_counts.get("total_lost", 0))
            self._stat_cards["total_found"].update_value(item_counts.get("total_found", 0))
            self._stat_cards["pending"].update_value(claim_counts.get("pending", 0))
            self._stat_cards["approved"].update_value(claim_counts.get("approved", 0))
            self._stat_cards["returned"].update_value(claim_counts.get("returned", 0))
        except Exception as e:
            print(f"[AdminDashboard] stats error: {e}")

    def _refresh_claims_table(self):
        # clear
        for w in self._claims_frame.winfo_children():
            w.destroy()

        try:
            claims = db.get_all_claims()[:10]
        except Exception:
            claims = []

        theme = self._theme
        for row_idx, c in enumerate(claims):
            bg = theme.get("table_row_alt", "#f5fdf5") if row_idx % 2 else theme.get("table_bg", "#ffffff")
            status = c.get("claim_status", "")
            status_color = _status_color(status, theme)

            row_data = [
                str(c.get("claim_id", "")),
                str(c.get("lost_item_name", ""))[:20],
                str(c.get("found_item_name", ""))[:20],
                str(c.get("claimant_name", ""))[:18],
                status.upper(),
                str(c.get("created_at", ""))[:10],
            ]

            for col_idx, (val, w) in enumerate(zip(row_data, self._CLAIM_WIDTHS)):
                txt_color = status_color if col_idx == 4 else theme.get("table_fg", "#1a3a1a")
                lbl = ctk.CTkLabel(self._claims_frame, text=val, width=w,
                                   anchor="w", font=ctk.CTkFont(size=11),
                                   text_color=txt_color,
                                   fg_color=bg)
                lbl.grid(row=row_idx, column=col_idx, padx=(8, 2), pady=2, sticky="w")

        if not claims:
            ctk.CTkLabel(self._claims_frame, text="No claims yet.",
                         text_color=self._theme.get("text_muted", "#6b8f6b"),
                         font=ctk.CTkFont(size=12)).grid(row=0, column=0,
                                                         columnspan=len(self._CLAIM_COLS),
                                                         padx=16, pady=20)

    def _refresh_activity_table(self):
        for w in self._activity_frame.winfo_children():
            w.destroy()

        try:
            rows = db._fetchall(
                "SELECT al.*, u.full_name FROM activity_log al "
                "LEFT JOIN users u ON al.user_id = u.user_id "
                "ORDER BY al.created_at DESC LIMIT 10"
            )
        except Exception:
            rows = []

        theme = self._theme
        for row_idx, entry in enumerate(rows):
            bg = theme.get("table_row_alt", "#f5fdf5") if row_idx % 2 else theme.get("table_bg", "#ffffff")
            ts = str(entry.get("created_at", ""))[:16]
            row_data = [
                ts,
                str(entry.get("full_name", "System"))[:14],
                str(entry.get("action", ""))[:18],
                str(entry.get("details", ""))[:30],
            ]
            for col_idx, (val, w) in enumerate(zip(row_data, self._ACT_WIDTHS)):
                lbl = ctk.CTkLabel(self._activity_frame, text=val, width=w,
                                   anchor="w", font=ctk.CTkFont(size=11),
                                   text_color=theme.get("table_fg", "#1a3a1a"),
                                   fg_color=bg)
                lbl.grid(row=row_idx, column=col_idx, padx=(8, 2), pady=2, sticky="w")

        if not rows:
            ctk.CTkLabel(self._activity_frame, text="No activity yet.",
                         text_color=self._theme.get("text_muted", "#6b8f6b"),
                         font=ctk.CTkFont(size=12)).grid(row=0, column=0,
                                                         columnspan=len(self._ACT_COLS),
                                                         padx=16, pady=20)

    # ── PDF export dialog ─────────────────────────────────────────────────────

    def _export_pdf_dialog(self):
        dlg = ctk.CTkToplevel(self)
        dlg.title("Export Reports")
        dlg.geometry("340x240")
        dlg.grab_set()
        dlg.resizable(False, False)

        ctk.CTkLabel(dlg, text="Choose Report to Export",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(18, 8))

        def _export(kind):
            try:
                if kind == "lost":
                    items = db.get_all_items(item_type="lost")
                    path = pdf_service.generate_lost_items_report(items)
                elif kind == "found":
                    items = db.get_all_items(item_type="found")
                    path = pdf_service.generate_found_items_report(items)
                elif kind == "claims":
                    claims = db.get_all_claims()
                    path = pdf_service.generate_claim_history(claims)
                elif kind == "analytics":
                    data = db.get_analytics_data()
                    path = pdf_service.generate_analytics_report(data)
                dlg.destroy()
                messagebox.showinfo("Export Complete", f"Saved:\n{path}")
            except Exception as e:
                messagebox.showerror("Export Error", str(e))

        for text, kind in [
            ("📋 Lost Items Report", "lost"),
            ("🔍 Found Items Report", "found"),
            ("⚖ Claims Report", "claims"),
            ("📊 Analytics Report", "analytics"),
        ]:
            ctk.CTkButton(dlg, text=text, height=34,
                          command=lambda k=kind: _export(k)).pack(
                fill="x", padx=30, pady=4)

    # ── theme ─────────────────────────────────────────────────────────────────

    def apply_theme(self, theme: dict):
        self._theme = theme
        self.configure(fg_color="transparent")

        # rebuild stats area background
        self._stat_frames.configure(fg_color="transparent")

        # update existing stat cards
        for card in self._stat_cards.values():
            card.configure(fg_color=theme.get("bg_card", "#ffffff"),
                           border_color=theme.get("card_border", "#d4edd4"))

        self.refresh_data()
