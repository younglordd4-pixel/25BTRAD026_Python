"""
Student Dashboard Module - CampusFind
Displays stats, quick actions, recent activity, and notifications for students.
"""

import customtkinter as ctk
from datetime import datetime


class StudentDashboard(ctk.CTkFrame):
    """Main dashboard shown to students after login."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.theme = None

        # Stat card references for updating
        self._stat_labels = {}

        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # ── Top greeting bar ──────────────────────────────────────────
        self.top_frame = ctk.CTkFrame(self, corner_radius=0)
        self.top_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 0))
        self.top_frame.grid_columnconfigure(0, weight=1)

        self.greeting_label = ctk.CTkLabel(
            self.top_frame,
            text="Welcome back! 👋",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        self.greeting_label.grid(row=0, column=0, sticky="w", padx=15, pady=(10, 2))

        self.date_label = ctk.CTkLabel(
            self.top_frame,
            text=datetime.now().strftime("%A, %B %d, %Y"),
            font=ctk.CTkFont(size=13),
        )
        self.date_label.grid(row=1, column=0, sticky="w", padx=15, pady=(0, 10))

        # ── Stats cards row ───────────────────────────────────────────
        self.stats_frame = ctk.CTkFrame(self, corner_radius=0)
        self.stats_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        for i in range(5):
            self.stats_frame.grid_columnconfigure(i, weight=1)

        stat_defs = [
            ("Lost Items\nReported", "lost_reported", "#2196F3", "📋"),
            ("Found Items\nReported", "found_reported", "#4CAF50", "📦"),
            ("Possible\nMatches", "possible_matches", "#FF9800", "🔗"),
            ("Pending\nClaims", "pending_claims", "#FFC107", "⏳"),
            ("Items\nRecovered", "items_recovered", "#009688", "✅"),
        ]

        for col, (title, key, color, icon) in enumerate(stat_defs):
            card = self._make_stat_card(self.stats_frame, title, "0", color, icon)
            card.grid(row=0, column=col, padx=6, pady=6, sticky="ew")
            self._stat_labels[key] = card

        # ── Main content area ─────────────────────────────────────────
        self.content_frame = ctk.CTkFrame(self, corner_radius=0)
        self.content_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.content_frame.grid_columnconfigure(0, weight=3)
        self.content_frame.grid_columnconfigure(1, weight=1)
        self.content_frame.grid_rowconfigure(1, weight=1)

        # Quick actions
        self.actions_frame = ctk.CTkFrame(self.content_frame)
        self.actions_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=10)

        actions = [
            ("📋 Report Lost Item", "report_lost"),
            ("📦 Report Found Item", "report_found"),
            ("🔍 Search Items", "search"),
            ("📄 My Reports", "my_reports"),
            ("📝 My Claims", "my_claims"),
        ]

        self.action_buttons = []
        for i, (label, frame_name) in enumerate(actions):
            btn = ctk.CTkButton(
                self.actions_frame,
                text=label,
                width=160,
                height=40,
                command=lambda fn=frame_name: self.controller.show_frame(fn),
            )
            btn.grid(row=0, column=i, padx=8, pady=10)
            self.action_buttons.append(btn)

        # Recent activity table (left)
        self.activity_frame = ctk.CTkFrame(self.content_frame)
        self.activity_frame.grid(row=1, column=0, sticky="nsew", padx=(10, 5), pady=(0, 10))
        self.activity_frame.grid_columnconfigure(0, weight=1)
        self.activity_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            self.activity_frame,
            text="Recent Activity",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=12, pady=(10, 4))

        self.activity_scroll = ctk.CTkScrollableFrame(self.activity_frame)
        self.activity_scroll.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        self.activity_scroll.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        # Table header
        headers = ["Type", "Item", "Category", "Date", "Status"]
        for col, h in enumerate(headers):
            ctk.CTkLabel(
                self.activity_scroll,
                text=h,
                font=ctk.CTkFont(size=12, weight="bold"),
            ).grid(row=0, column=col, padx=6, pady=4, sticky="w")

        self._activity_rows = []

        # Notifications panel (right)
        self.notif_frame = ctk.CTkFrame(self.content_frame)
        self.notif_frame.grid(row=1, column=1, sticky="nsew", padx=(5, 10), pady=(0, 10))
        self.notif_frame.grid_columnconfigure(0, weight=1)
        self.notif_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            self.notif_frame,
            text="🔔 Notifications",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=12, pady=(10, 4))

        self.notif_scroll = ctk.CTkScrollableFrame(self.notif_frame)
        self.notif_scroll.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        self.notif_scroll.grid_columnconfigure(0, weight=1)

        self._notif_widgets = []

    # ------------------------------------------------------------------
    # Stat card helper
    # ------------------------------------------------------------------

    def _make_stat_card(self, parent, title, value, color, icon):
        """Create a coloured stat card widget and return the frame."""
        card = ctk.CTkFrame(parent, corner_radius=10)

        inner = ctk.CTkFrame(card, corner_radius=0, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=12, pady=12)

        icon_lbl = ctk.CTkLabel(inner, text=icon, font=ctk.CTkFont(size=28))
        icon_lbl.pack()

        val_lbl = ctk.CTkLabel(
            inner,
            text=value,
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color=color,
        )
        val_lbl.pack()

        title_lbl = ctk.CTkLabel(
            inner,
            text=title,
            font=ctk.CTkFont(size=11),
            justify="center",
        )
        title_lbl.pack()

        # Attach references for later updates
        card._value_label = val_lbl
        card._color = color
        return card

    # ------------------------------------------------------------------
    # Data refresh
    # ------------------------------------------------------------------

    def refresh_data(self):
        """Re-fetch stats, activity and notifications from the database."""
        try:
            user = self.controller.current_user
            if not user:
                return
            user_id = user.get("id") or user.get("user_id")
            name = user.get("full_name") or user.get("name") or "Student"
            self.greeting_label.configure(text=f"Welcome back, {name}! 👋")
            self.date_label.configure(text=datetime.now().strftime("%A, %B %d, %Y"))

            db = self.controller.db

            # --- stats ---
            try:
                lost_count = db.count_items(user_id=user_id, item_type="lost")
            except Exception:
                lost_count = 0
            try:
                found_count = db.count_items(user_id=user_id, item_type="found")
            except Exception:
                found_count = 0
            try:
                match_count = db.count_matches_for_user(user_id=user_id)
            except Exception:
                match_count = 0
            try:
                pending_count = db.count_claims(user_id=user_id, status="pending")
            except Exception:
                pending_count = 0
            try:
                recovered_count = db.count_items(user_id=user_id, status="returned")
            except Exception:
                recovered_count = 0

            stat_values = {
                "lost_reported": str(lost_count),
                "found_reported": str(found_count),
                "possible_matches": str(match_count),
                "pending_claims": str(pending_count),
                "items_recovered": str(recovered_count),
            }
            for key, card in self._stat_labels.items():
                card._value_label.configure(text=stat_values.get(key, "0"))

            # --- recent activity ---
            for w in self._activity_rows:
                w.destroy()
            self._activity_rows.clear()

            try:
                items = db.get_items_by_user(user_id=user_id, limit=5)
            except Exception:
                items = []

            if items:
                for row_idx, item in enumerate(items, start=1):
                    row_data = [
                        item.get("item_type", "").capitalize(),
                        item.get("item_name", ""),
                        item.get("category", ""),
                        str(item.get("date_reported") or item.get("lost_date") or ""),
                        item.get("status", "open").capitalize(),
                    ]
                    for col_idx, text in enumerate(row_data):
                        lbl = ctk.CTkLabel(self.activity_scroll, text=text, font=ctk.CTkFont(size=11))
                        lbl.grid(row=row_idx, column=col_idx, padx=6, pady=2, sticky="w")
                        self._activity_rows.append(lbl)
            else:
                empty = ctk.CTkLabel(
                    self.activity_scroll,
                    text="No recent activity.",
                    font=ctk.CTkFont(size=12),
                )
                empty.grid(row=1, column=0, columnspan=5, padx=10, pady=10)
                self._activity_rows.append(empty)

            # --- notifications ---
            for w in self._notif_widgets:
                w.destroy()
            self._notif_widgets.clear()

            try:
                notifs = db.get_notifications(user_id=user_id, unread_only=True, limit=5)
            except Exception:
                notifs = []

            if notifs:
                for notif in notifs:
                    nf = ctk.CTkFrame(self.notif_scroll, corner_radius=6)
                    nf.pack(fill="x", padx=4, pady=3)
                    ctk.CTkLabel(
                        nf,
                        text=notif.get("message", ""),
                        font=ctk.CTkFont(size=11),
                        wraplength=200,
                        justify="left",
                    ).pack(anchor="w", padx=8, pady=4)
                    self._notif_widgets.append(nf)
            else:
                empty = ctk.CTkLabel(
                    self.notif_scroll,
                    text="No new notifications.",
                    font=ctk.CTkFont(size=12),
                )
                empty.pack(padx=10, pady=10)
                self._notif_widgets.append(empty)

        except Exception as exc:
            print(f"[StudentDashboard] refresh_data error: {exc}")

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------

    def apply_theme(self, theme):
        """Apply color theme dictionary to all widgets."""
        self.theme = theme
        try:
            self.configure(fg_color=theme["bg_primary"])
            self.top_frame.configure(fg_color=theme["bg_card"])
            self.stats_frame.configure(fg_color=theme["bg_primary"])
            self.content_frame.configure(fg_color=theme["bg_primary"])
            self.actions_frame.configure(fg_color=theme["bg_card"])
            self.activity_frame.configure(fg_color=theme["bg_card"])
            self.notif_frame.configure(fg_color=theme["bg_card"])

            self.greeting_label.configure(text_color=theme["text_primary"])
            self.date_label.configure(text_color=theme["text_secondary"])

            for btn in self.action_buttons:
                btn.configure(
                    fg_color=theme["btn_primary_bg"],
                    text_color=theme["btn_primary_fg"],
                    hover_color=theme["accent_hover"],
                )

            for key, card in self._stat_labels.items():
                card.configure(fg_color=theme["bg_card"], border_color=theme["card_border"], border_width=1)
                card._value_label.configure(text_color=card._color)
        except Exception as exc:
            print(f"[StudentDashboard] apply_theme error: {exc}")
