"""
CampusFind - Administrator User Management Module
Allows administrators to view all accounts, search/filter, inspect student activity, change roles, and export user summaries.
"""

from datetime import datetime
import customtkinter as ctk
from tkinter import messagebox

from database import db
from services.pdf_service import pdf_service


class AdminUsersFrame(ctk.CTkFrame):
    """User management screen for administrators."""

    USERS_PER_PAGE = 15

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.theme = None
        self._all_users = []
        self._current_page = 0

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_ui()

    def _build_ui(self):
        # 1. Header & Search
        top_f = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        top_f.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 10))
        top_f.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            top_f, text="👥  Student & User Management",
            font=ctk.CTkFont(size=22, weight="bold")
        ).grid(row=0, column=0, sticky="w")

        btn_box = ctk.CTkFrame(top_f, fg_color="transparent")
        btn_box.grid(row=0, column=1, sticky="e")

        self.export_pdf_btn = ctk.CTkButton(
            btn_box, text="📄 Export PDF", width=120, height=34,
            command=self._export_users_pdf
        )
        self.export_pdf_btn.pack(side="right", padx=(6, 0))

        self.refresh_btn = ctk.CTkButton(
            btn_box, text="🔄 Refresh", width=90, height=34,
            command=self.refresh_data
        )
        self.refresh_btn.pack(side="right")

        # 2. Search & Role Filter Bar
        filter_bar = ctk.CTkFrame(self, corner_radius=10)
        filter_bar.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 10))

        self.search_entry = ctk.CTkEntry(
            filter_bar,
            placeholder_text="Search by name, USN, email, or department...",
            width=360, height=36
        )
        self.search_entry.pack(side="left", padx=12, pady=10)
        self.search_entry.bind("<Return>", lambda _: self._filter_users())

        ctk.CTkButton(
            filter_bar, text="Search", width=80, height=36,
            command=self._filter_users
        ).pack(side="left", padx=(0, 10))

        ctk.CTkLabel(filter_bar, text="Role:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(10, 4))
        self.role_var = ctk.StringVar(value="All Roles")
        self.role_menu = ctk.CTkOptionMenu(
            filter_bar, variable=self.role_var,
            values=["All Roles", "student", "admin"],
            width=110, height=34,
            command=lambda _: self._filter_users()
        )
        self.role_menu.pack(side="left", padx=(0, 10))

        self.user_count_lbl = ctk.CTkLabel(
            filter_bar, text="0 users", font=ctk.CTkFont(size=12, weight="bold")
        )
        self.user_count_lbl.pack(side="right", padx=16)

        # 3. Users Table (Scrollable)
        self.scroll = ctk.CTkScrollableFrame(self, corner_radius=10)
        self.scroll.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 10))
        self.scroll.grid_columnconfigure(0, weight=1)

        # 4. Pagination Footer
        page_box = ctk.CTkFrame(self, height=40, corner_radius=0, fg_color="transparent")
        page_box.grid(row=3, column=0, sticky="ew", padx=24, pady=(0, 14))

        self.prev_btn = ctk.CTkButton(
            page_box, text="◀ Prev", width=80, height=30,
            command=self._prev_page
        )
        self.prev_btn.pack(side="left")

        self.page_lbl = ctk.CTkLabel(
            page_box, text="Page 1 of 1", font=ctk.CTkFont(size=12, weight="bold")
        )
        self.page_lbl.pack(side="left", padx=14)

        self.next_btn = ctk.CTkButton(
            page_box, text="Next ▶", width=80, height=30,
            command=self._next_page
        )
        self.next_btn.pack(side="left")

    def refresh_data(self):
        self._all_users = db.get_all_users()
        self._filter_users()

    def _filter_users(self):
        query = self.search_entry.get().strip().lower()
        role_filter = self.role_var.get()

        filtered = []
        for u in self._all_users:
            if role_filter != "All Roles" and u.get('role') != role_filter:
                continue
            if query:
                match = (
                    query in str(u.get('full_name', '')).lower() or
                    query in str(u.get('usn', '')).lower() or
                    query in str(u.get('email', '')).lower() or
                    query in str(u.get('department', '')).lower()
                )
                if not match:
                    continue
            filtered.append(u)

        self._filtered_users = filtered
        self._current_page = 0
        self._render_table()

    def _render_table(self):
        for w in self.scroll.winfo_children():
            w.destroy()

        total = len(self._filtered_users)
        self.user_count_lbl.configure(text=f"{total} user(s)")

        total_pages = max(1, (total + self.USERS_PER_PAGE - 1) // self.USERS_PER_PAGE)
        self.page_lbl.configure(text=f"Page {self._current_page + 1} of {total_pages}")
        self.prev_btn.configure(state="normal" if self._current_page > 0 else "disabled")
        self.next_btn.configure(state="normal" if self._current_page < total_pages - 1 else "disabled")

        # Table Header
        hdr = ctk.CTkFrame(self.scroll, height=36, corner_radius=6)
        hdr.pack(fill="x", pady=(0, 6))
        hdr.grid_columnconfigure(1, weight=1)
        hdr.grid_columnconfigure(4, weight=1)

        cols = [
            ("ID", 50, 0),
            ("Full Name", 140, 1),
            ("USN", 110, 2),
            ("Department", 130, 3),
            ("Email", 180, 4),
            ("Role", 80, 5),
            ("Actions", 160, 6)
        ]
        for name, w, col in cols:
            lbl = ctk.CTkLabel(hdr, text=name, font=ctk.CTkFont(size=11, weight="bold"), anchor="w")
            lbl.grid(row=0, column=col, padx=8, pady=6, sticky="w")

        start = self._current_page * self.USERS_PER_PAGE
        page_users = self._filtered_users[start:start + self.USERS_PER_PAGE]

        if not page_users:
            ctk.CTkLabel(
                self.scroll, text="No users found.", font=ctk.CTkFont(size=13), text_color="gray"
            ).pack(pady=40)
            return

        for user in page_users:
            self._render_row(user)

    def _render_row(self, user: dict):
        row = ctk.CTkFrame(self.scroll, corner_radius=6)
        row.pack(fill="x", pady=2)
        row.grid_columnconfigure(1, weight=1)
        row.grid_columnconfigure(4, weight=1)

        # ID
        ctk.CTkLabel(row, text=str(user.get('user_id')), width=50, anchor="w").grid(row=0, column=0, padx=8, pady=6, sticky="w")

        # Name
        ctk.CTkLabel(row, text=user.get('full_name', '-'), width=140, font=ctk.CTkFont(weight="bold"), anchor="w").grid(row=0, column=1, padx=8, sticky="w")

        # USN
        ctk.CTkLabel(row, text=user.get('usn', '-'), width=110, anchor="w").grid(row=0, column=2, padx=8, sticky="w")

        # Dept
        ctk.CTkLabel(row, text=user.get('department', '-'), width=130, anchor="w").grid(row=0, column=3, padx=8, sticky="w")

        # Email
        ctk.CTkLabel(row, text=user.get('email', '-'), width=180, anchor="w").grid(row=0, column=4, padx=8, sticky="w")

        # Role badge
        role = user.get('role', 'student')
        role_color = "#0277bd" if role == 'admin' else "#2d7a2d"
        ctk.CTkLabel(
            row, text=f" {role.upper()} ", fg_color=role_color, text_color="white",
            corner_radius=4, font=ctk.CTkFont(size=10, weight="bold")
        ).grid(row=0, column=5, padx=8, sticky="w")

        # Actions
        act_box = ctk.CTkFrame(row, fg_color="transparent")
        act_box.grid(row=0, column=6, padx=8, pady=4, sticky="e")

        ctk.CTkButton(
            act_box, text="View", width=46, height=26,
            command=lambda u=user: self._view_user_modal(u)
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            act_box, text="Role", width=46, height=26, fg_color="#f57c00",
            command=lambda u=user: self._toggle_role(u)
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            act_box, text="Del", width=42, height=26, fg_color="#c62828",
            command=lambda u=user: self._delete_user(u)
        ).pack(side="left", padx=2)

    def _toggle_role(self, user: dict):
        cur_user = getattr(self.controller, 'current_user', None)
        if cur_user and cur_user['user_id'] == user['user_id']:
            messagebox.showerror("Operation Prohibited", "You cannot modify your own administrative role.")
            return

        current_role = user.get('role', 'student')
        new_role = 'student' if current_role == 'admin' else 'admin'

        if messagebox.askyesno("Confirm Role Change", f"Change role of {user['full_name']} from '{current_role}' to '{new_role}'?"):
            db.update_user(user['user_id'], role=new_role)
            db.log_activity(
                cur_user['user_id'] if cur_user else 0,
                'change_role',
                f"Changed role of user #{user['user_id']} ({user['email']}) to {new_role}"
            )
            self.refresh_data()
            messagebox.showinfo("Role Updated", f"User is now a {new_role}.")

    def _delete_user(self, user: dict):
        cur_user = getattr(self.controller, 'current_user', None)
        if cur_user and cur_user['user_id'] == user['user_id']:
            messagebox.showerror("Operation Prohibited", "You cannot delete your own account while logged in.")
            return

        if messagebox.askyesno("Confirm Deletion", f"Permanently delete user '{user['full_name']}' ({user['email']})?\nThis cannot be undone."):
            db.delete_user(user['user_id'])
            db.log_activity(
                cur_user['user_id'] if cur_user else 0,
                'delete_user',
                f"Deleted user #{user['user_id']} ({user['email']})"
            )
            self.refresh_data()
            messagebox.showinfo("User Deleted", "The user record has been removed.")

    def _view_user_modal(self, user: dict):
        """Displays user profile along with items reported and claims submitted."""
        dlg = ctk.CTkToplevel(self)
        dlg.title(f"User Profile: {user.get('full_name')}")
        dlg.geometry("520x600")
        dlg.grab_set()

        scroll = ctk.CTkScrollableFrame(dlg)
        scroll.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            scroll, text=f"👤  {user.get('full_name')}",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(anchor="w", pady=(0, 6))

        fields = [
            ("User ID", f"#{user.get('user_id')}"),
            ("USN", user.get('usn', '-')),
            ("Department", user.get('department', '-')),
            ("Email", user.get('email', '-')),
            ("Role", user.get('role', '-').upper()),
            ("Registered", str(user.get('created_at', '-'))[:16]),
        ]
        for f_label, f_val in fields:
            row = ctk.CTkFrame(scroll, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=f"{f_label}:", width=110, font=ctk.CTkFont(weight="bold", size=12), anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=str(f_val), font=ctk.CTkFont(size=12), anchor="w").pack(side="left")

        # Activity summary
        lost_items = db.get_items_by_user(user['user_id'], item_type="lost")
        found_items = db.get_items_by_user(user['user_id'], item_type="found")
        claims = db.get_claims_by_user(user['user_id'])

        ctk.CTkLabel(
            scroll, text=f"\nActivity Summary:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", pady=(6, 4))

        ctk.CTkLabel(scroll, text=f"• Lost Items Reported: {len(lost_items)}").pack(anchor="w")
        ctk.CTkLabel(scroll, text=f"• Found Items Registered: {len(found_items)}").pack(anchor="w")
        ctk.CTkLabel(scroll, text=f"• Ownership Claims Filed: {len(claims)}").pack(anchor="w")

        # Buttons
        btn_box = ctk.CTkFrame(dlg, corner_radius=0)
        btn_box.pack(fill="x", padx=20, pady=(0, 16))

        def export_student_pdf():
            try:
                pdf_path = pdf_service.generate_user_report(user, lost_items, found_items, claims)
                messagebox.showinfo("Export Complete", f"Student activity report generated:\n{pdf_path}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to generate PDF: {e}")

        ctk.CTkButton(btn_box, text="Export Student PDF", command=export_student_pdf).pack(side="left")
        ctk.CTkButton(btn_box, text="Close", width=90, command=dlg.destroy).pack(side="right")

    def _export_users_pdf(self):
        try:
            # Generate a summary PDF of all registered students
            from services.pdf_service import pdf_service
            # We can use generate_lost_items_report or add a dedicated method, or generate user report
            user_items = []
            for u in self._filtered_users:
                user_items.append({
                    "item_id": u.get('user_id'),
                    "item_name": u.get('full_name'),
                    "category": u.get('department'),
                    "location": u.get('usn'),
                    "item_date": str(u.get('created_at', ''))[:10],
                    "status": u.get('role'),
                    "full_name": u.get('email')
                })
            path = pdf_service.generate_lost_items_report(user_items, filename=f"users_list_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
            messagebox.showinfo("Export Successful", f"Users list exported to PDF:\n{path}")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Could not generate PDF: {e}")

    def _prev_page(self):
        if self._current_page > 0:
            self._current_page -= 1
            self._render_table()

    def _next_page(self):
        total = len(self._filtered_users)
        total_pages = max(1, (total + self.USERS_PER_PAGE - 1) // self.USERS_PER_PAGE)
        if self._current_page < total_pages - 1:
            self._current_page += 1
            self._render_table()

    def apply_theme(self, theme: dict):
        self.theme = theme
        try:
            self.configure(fg_color=theme.get("bg_primary", "transparent"))
            accent = theme.get("accent_primary", "#2d7a2d")
            self.export_pdf_btn.configure(
                fg_color=accent,
                hover_color=theme.get("accent_hover", "#1f5a1f")
            )
            self._render_table()
        except Exception:
            pass
