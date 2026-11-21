"""
CampusFind - Administrator Claim Review Module
Enables administrators to inspect ownership claims, compare item descriptions side-by-side,
verify proof, update statuses, record administrative remarks, and dispatch notifications.
"""

from datetime import datetime
import customtkinter as ctk
from tkinter import messagebox

from database import db
from services.email_service import email_service
from services.pdf_service import pdf_service
from services.image_service import image_service


class AdminClaimReviewFrame(ctk.CTkFrame):
    """Admin interface for processing and adjudicating ownership claims."""

    CLAIMS_PER_PAGE = 15

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.theme = None
        self._filter_status = "all"
        self._all_claims = []
        self._filtered_claims = []
        self._current_page = 0

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_ui()

    def _build_ui(self):
        # 1. Header
        top_f = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        top_f.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 10))
        top_f.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            top_f, text="⚖️  Ownership Claims Review & Adjudication",
            font=ctk.CTkFont(size=22, weight="bold")
        ).grid(row=0, column=0, sticky="w")

        btn_box = ctk.CTkFrame(top_f, fg_color="transparent")
        btn_box.grid(row=0, column=1, sticky="e")

        self.export_btn = ctk.CTkButton(
            btn_box, text="📄 Export PDF", width=110, height=34,
            command=self._export_pdf
        )
        self.export_btn.pack(side="right", padx=(6, 0))

        self.refresh_btn = ctk.CTkButton(
            btn_box, text="🔄 Refresh", width=90, height=34,
            command=self.refresh_data
        )
        self.refresh_btn.pack(side="right")

        # 2. Filter Bar
        filter_bar = ctk.CTkFrame(self, corner_radius=10)
        filter_bar.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 10))

        self.tab_buttons = {}
        statuses = [
            ("All Claims", "all"),
            ("Pending", "pending"),
            ("Under Review", "under_review"),
            ("Approved", "approved"),
            ("Rejected", "rejected"),
            ("Returned", "returned"),
        ]
        for label, code in statuses:
            btn = ctk.CTkButton(
                filter_bar, text=label, width=95, height=32,
                fg_color="transparent",
                command=lambda c=code: self._set_filter(c)
            )
            btn.pack(side="left", padx=3, pady=6)
            self.tab_buttons[code] = btn

        self.count_lbl = ctk.CTkLabel(
            filter_bar, text="0 claims", font=ctk.CTkFont(size=12, weight="bold")
        )
        self.count_lbl.pack(side="right", padx=16)

        # 3. Claims Scrollable Table
        self.scroll = ctk.CTkScrollableFrame(self, corner_radius=10)
        self.scroll.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 10))
        self.scroll.grid_columnconfigure(0, weight=1)

        # 4. Pagination
        page_box = ctk.CTkFrame(self, height=40, corner_radius=0, fg_color="transparent")
        page_box.grid(row=3, column=0, sticky="ew", padx=24, pady=(0, 14))

        self.prev_btn = ctk.CTkButton(
            page_box, text="◀ Prev", width=80, height=30, command=self._prev_page
        )
        self.prev_btn.pack(side="left")

        self.page_lbl = ctk.CTkLabel(
            page_box, text="Page 1 of 1", font=ctk.CTkFont(size=12, weight="bold")
        )
        self.page_lbl.pack(side="left", padx=14)

        self.next_btn = ctk.CTkButton(
            page_box, text="Next ▶", width=80, height=30, command=self._next_page
        )
        self.next_btn.pack(side="left")

    def refresh_data(self):
        self._all_claims = db.get_all_claims()
        self._filter_claims()

    def _set_filter(self, code: str):
        self._filter_status = code
        theme = self.theme or {}
        accent = theme.get("accent_primary", "#2d7a2d")
        for st, btn in self.tab_buttons.items():
            if st == code:
                btn.configure(fg_color=accent, text_color="white")
            else:
                btn.configure(fg_color="transparent", text_color=theme.get("text_primary", "black"))
        self._filter_claims()

    def _filter_claims(self):
        filtered = []
        for c in self._all_claims:
            if self._filter_status != "all" and c.get('claim_status') != self._filter_status:
                continue
            filtered.append(c)

        self._filtered_claims = filtered
        self._current_page = 0
        self._render_table()

    def _render_table(self):
        for w in self.scroll.winfo_children():
            w.destroy()

        total = len(self._filtered_claims)
        self.count_lbl.configure(text=f"{total} claim(s)")

        total_pages = max(1, (total + self.CLAIMS_PER_PAGE - 1) // self.CLAIMS_PER_PAGE)
        self.page_lbl.configure(text=f"Page {self._current_page + 1} of {total_pages}")
        self.prev_btn.configure(state="normal" if self._current_page > 0 else "disabled")
        self.next_btn.configure(state="normal" if self._current_page < total_pages - 1 else "disabled")

        # Table Header
        hdr = ctk.CTkFrame(self.scroll, height=36, corner_radius=6)
        hdr.pack(fill="x", pady=(0, 6))
        hdr.grid_columnconfigure(2, weight=1)

        cols = [
            ("ID", 50, 0),
            ("Claimant", 140, 1),
            ("Found Item", 180, 2),
            ("Linked Lost", 140, 3),
            ("Date", 90, 4),
            ("Status", 110, 5),
            ("Action", 90, 6)
        ]
        for name, w, col in cols:
            lbl = ctk.CTkLabel(hdr, text=name, font=ctk.CTkFont(size=11, weight="bold"), anchor="w")
            lbl.grid(row=0, column=col, padx=8, pady=6, sticky="w")

        start = self._current_page * self.CLAIMS_PER_PAGE
        page_claims = self._filtered_claims[start:start + self.CLAIMS_PER_PAGE]

        if not page_claims:
            ctk.CTkLabel(
                self.scroll, text="No claims found in this category.",
                font=ctk.CTkFont(size=13), text_color="gray"
            ).pack(pady=40)
            return

        for claim in page_claims:
            self._render_row(claim)

    def _render_row(self, claim: dict):
        row = ctk.CTkFrame(self.scroll, corner_radius=6)
        row.pack(fill="x", pady=2)
        row.grid_columnconfigure(2, weight=1)

        # ID
        ctk.CTkLabel(row, text=f"#{claim.get('claim_id')}", width=50, anchor="w").grid(row=0, column=0, padx=8, pady=6, sticky="w")

        # Claimant
        claimant_name = claim.get('claimant_name') or f"User #{claim.get('claimant_id')}"
        ctk.CTkLabel(row, text=claimant_name, width=140, font=ctk.CTkFont(weight="bold"), anchor="w").grid(row=0, column=1, padx=8, sticky="w")

        # Found Item
        found_name = claim.get('found_item_name') or f"Item #{claim.get('found_item_id')}"
        ctk.CTkLabel(row, text=found_name, width=180, anchor="w").grid(row=0, column=2, padx=8, sticky="w")

        # Linked Lost Item
        lost_name = claim.get('lost_item_name') or (f"Item #{claim.get('lost_item_id')}" if claim.get('lost_item_id') else "(None)")
        ctk.CTkLabel(row, text=lost_name, width=140, anchor="w").grid(row=0, column=3, padx=8, sticky="w")

        # Date
        ctk.CTkLabel(row, text=str(claim.get('created_at', ''))[:10], width=90, anchor="w").grid(row=0, column=4, padx=8, sticky="w")

        # Status badge
        st = claim.get('claim_status', 'pending')
        color_map = {
            "pending": "#f57c00",
            "under_review": "#0277bd",
            "approved": "#2d7a2d",
            "rejected": "#c62828",
            "returned": "#388e3c"
        }
        ctk.CTkLabel(
            row, text=f" {st.replace('_', ' ').upper()} ",
            fg_color=color_map.get(st, "gray"), text_color="white",
            corner_radius=4, font=ctk.CTkFont(size=10, weight="bold")
        ).grid(row=0, column=5, padx=8, sticky="w")

        # Review Button
        ctk.CTkButton(
            row, text="Review", width=70, height=26,
            command=lambda c=claim: self._open_review_modal(c)
        ).grid(row=0, column=6, padx=8, pady=4, sticky="e")

    def _open_review_modal(self, claim: dict):
        """Opens comprehensive claim adjudication modal."""
        found_item = db.get_item_by_id(claim.get('found_item_id')) or {}
        lost_item = db.get_item_by_id(claim.get('lost_item_id')) if claim.get('lost_item_id') else None
        claimant = db.get_user_by_id(claim.get('claimant_id')) or {}

        dlg = ctk.CTkToplevel(self)
        dlg.title(f"Review Claim #{claim['claim_id']} – CampusFind")
        dlg.geometry("720x680")
        dlg.grab_set()

        scroll = ctk.CTkScrollableFrame(dlg)
        scroll.pack(fill="both", expand=True, padx=20, pady=16)

        # Header Title
        ctk.CTkLabel(
            scroll, text=f"Claim Adjudication: Claim #{claim['claim_id']}",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(anchor="w", pady=(0, 4))

        ctk.CTkLabel(
            scroll,
            text=f"Claimant: {claimant.get('full_name', 'Student')} (USN: {claimant.get('usn', '-')}, Dept: {claimant.get('department', '-')}, Email: {claim.get('contact_email', claimant.get('email', '-'))})",
            font=ctk.CTkFont(size=12), text_color="gray"
        ).pack(anchor="w", pady=(0, 12))

        # Side by side comparison (Lost vs Found)
        comp_frame = ctk.CTkFrame(scroll, corner_radius=8)
        comp_frame.pack(fill="x", pady=(0, 14))
        comp_frame.grid_columnconfigure(0, weight=1)
        comp_frame.grid_columnconfigure(1, weight=1)

        # Left: Found Item
        left = ctk.CTkFrame(comp_frame, corner_radius=6)
        left.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        ctk.CTkLabel(left, text="📦 Registered Found Item", font=ctk.CTkFont(size=13, weight="bold"), text_color="#2d7a2d").pack(anchor="w", padx=10, pady=(8, 4))
        ctk.CTkLabel(left, text=f"Name: {found_item.get('item_name', '-')}", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10)
        ctk.CTkLabel(left, text=f"Category: {found_item.get('category', '-')}").pack(anchor="w", padx=10)
        ctk.CTkLabel(left, text=f"Location: {found_item.get('location', '-')}").pack(anchor="w", padx=10)
        ctk.CTkLabel(left, text=f"Date: {found_item.get('item_date', '-')}").pack(anchor="w", padx=10)
        ctk.CTkLabel(left, text=f"Features: {found_item.get('distinguishing_features', '-')}", wraplength=280).pack(anchor="w", padx=10, pady=(0, 8))

        # Right: Lost Item
        right = ctk.CTkFrame(comp_frame, corner_radius=6)
        right.grid(row=0, column=1, sticky="nsew", padx=8, pady=8)
        ctk.CTkLabel(right, text="📋 Claimant's Lost Report", font=ctk.CTkFont(size=13, weight="bold"), text_color="#c62828").pack(anchor="w", padx=10, pady=(8, 4))
        if lost_item:
            ctk.CTkLabel(right, text=f"Name: {lost_item.get('item_name', '-')}", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10)
            ctk.CTkLabel(right, text=f"Category: {lost_item.get('category', '-')}").pack(anchor="w", padx=10)
            ctk.CTkLabel(right, text=f"Location: {lost_item.get('location', '-')}").pack(anchor="w", padx=10)
            ctk.CTkLabel(right, text=f"Date: {lost_item.get('item_date', '-')}").pack(anchor="w", padx=10)
            ctk.CTkLabel(right, text=f"Features: {lost_item.get('distinguishing_features', '-')}", wraplength=280).pack(anchor="w", padx=10, pady=(0, 8))
        else:
            ctk.CTkLabel(right, text="No pre-existing lost report linked.", font=ctk.CTkFont(slant="italic"), text_color="gray").pack(anchor="w", padx=10, pady=20)

        # Claimant's Ownership Testimony
        ctk.CTkLabel(scroll, text="Claimant's Proof of Ownership:", font=ctk.CTkFont(weight="bold", size=13)).pack(anchor="w", pady=(6, 2))
        tb1 = ctk.CTkTextbox(scroll, height=80)
        tb1.pack(fill="x", pady=(0, 8))
        tb1.insert("1.0", claim.get('claim_details', ''))
        tb1.configure(state="disabled")

        if claim.get('additional_info'):
            ctk.CTkLabel(scroll, text="Additional Verification Info:", font=ctk.CTkFont(weight="bold", size=13)).pack(anchor="w", pady=(4, 2))
            tb2 = ctk.CTkTextbox(scroll, height=50)
            tb2.pack(fill="x", pady=(0, 8))
            tb2.insert("1.0", claim.get('additional_info', ''))
            tb2.configure(state="disabled")

        # Admin Remarks Input
        ctk.CTkLabel(scroll, text="Administrative Remarks & Instructions:", font=ctk.CTkFont(weight="bold", size=13)).pack(anchor="w", pady=(8, 2))
        remarks_box = ctk.CTkTextbox(scroll, height=70)
        remarks_box.pack(fill="x", pady=(0, 10))
        if claim.get('admin_remarks'):
            remarks_box.insert("1.0", claim.get('admin_remarks'))

        # Status Update Actions
        cur_status = claim.get('claim_status', 'pending')
        ctk.CTkLabel(scroll, text=f"Current Status: {cur_status.upper()}", font=ctk.CTkFont(weight="bold", size=12)).pack(anchor="w", pady=(4, 8))

        action_box = ctk.CTkFrame(scroll, fg_color="transparent")
        action_box.pack(fill="x", pady=(0, 14))

        def update_status(new_status: str):
            remarks = remarks_box.get("1.0", "end-1c").strip()
            db.update_claim_status(claim['claim_id'], new_status, admin_remarks=remarks)

            # If marked returned, update item status as well
            if new_status == "returned":
                db.update_item_status(claim['found_item_id'], 'returned')
                if claim.get('lost_item_id'):
                    db.update_item_status(claim['lost_item_id'], 'closed')

            # Log activity
            cur_user = getattr(self.controller, 'current_user', None)
            db.log_activity(
                cur_user['user_id'] if cur_user else 0,
                'adjudicate_claim',
                f"Updated claim #{claim['claim_id']} status to {new_status}"
            )

            # Notify user
            target_email = claim.get('contact_email') or claimant.get('email')
            student_name = claimant.get('full_name', 'Student')
            item_name = found_item.get('item_name', 'Item')

            db.create_notification(
                claim['claimant_id'],
                f"Claim #{claim['claim_id']} Updated",
                f"Your claim for '{item_name}' is now marked as {new_status.upper()}.\nRemarks: {remarks}",
                "claim_status"
            )

            # Dispatch email notification
            if target_email:
                if new_status == "returned":
                    email_service.send_item_returned(target_email, student_name, item_name)
                else:
                    email_service.send_claim_status_update(target_email, student_name, item_name, new_status, remarks)

            dlg.destroy()
            self.refresh_data()
            messagebox.showinfo("Status Updated", f"Claim #{claim['claim_id']} set to '{new_status.upper()}'. Notification recorded.")

        # Action buttons
        ctk.CTkButton(
            action_box, text="Under Review", width=120, height=36, fg_color="#0277bd",
            command=lambda: update_status("under_review")
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            action_box, text="Approve Claim", width=120, height=36, fg_color="#2d7a2d",
            command=lambda: update_status("approved")
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            action_box, text="Reject Claim", width=120, height=36, fg_color="#c62828",
            command=lambda: update_status("rejected")
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            action_box, text="Mark Returned", width=130, height=36, fg_color="#388e3c",
            command=lambda: update_status("returned")
        ).pack(side="left", padx=4)

        # Footer Close
        btn_footer = ctk.CTkFrame(dlg, corner_radius=0)
        btn_footer.pack(fill="x", padx=20, pady=(0, 16))
        ctk.CTkButton(btn_footer, text="Close", width=90, command=dlg.destroy).pack(side="right")

    def _export_pdf(self):
        try:
            path = pdf_service.generate_claim_history(self._filtered_claims)
            messagebox.showinfo("PDF Generated", f"Claim history report generated:\n{path}")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Could not generate PDF: {e}")

    def _prev_page(self):
        if self._current_page > 0:
            self._current_page -= 1
            self._render_table()

    def _next_page(self):
        total = len(self._filtered_claims)
        total_pages = max(1, (total + self.CLAIMS_PER_PAGE - 1) // self.CLAIMS_PER_PAGE)
        if self._current_page < total_pages - 1:
            self._current_page += 1
            self._render_table()

    def apply_theme(self, theme: dict):
        self.theme = theme
        try:
            self.configure(fg_color=theme.get("bg_primary", "transparent"))
            accent = theme.get("accent_primary", "#2d7a2d")
            self.export_btn.configure(
                fg_color=accent,
                hover_color=theme.get("accent_hover", "#1f5a1f")
            )
            self._render_table()
        except Exception:
            pass
