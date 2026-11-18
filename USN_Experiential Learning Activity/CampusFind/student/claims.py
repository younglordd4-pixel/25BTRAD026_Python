"""
CampusFind - Claim Management Module (Student)
Allows students to submit ownership claims on found items and track claim status.
"""

from datetime import datetime
import customtkinter as ctk
from tkinter import messagebox

from database import db
from services.email_service import email_service
from services.qr_service import qr_service
from services.image_service import image_service


# ---------------------------------------------------------------------------
# Status Badge Helper
# ---------------------------------------------------------------------------
def _get_status_style(status: str) -> tuple[str, str]:
    """Returns (fg_color, text_color) for status badges."""
    s = str(status).lower()
    if s == "approved":
        return ("#2d7a2d", "white")
    elif s == "pending":
        return ("#f57c00", "white")
    elif s == "under_review":
        return ("#0277bd", "white")
    elif s == "rejected":
        return ("#c62828", "white")
    elif s == "returned":
        return ("#388e3c", "white")
    return ("gray", "white")


# ---------------------------------------------------------------------------
# Submit Claim Dialog
# ---------------------------------------------------------------------------
class SubmitClaimDialog(ctk.CTkToplevel):
    """Dialog allowing a student to file an ownership claim on a found item."""

    def __init__(self, parent, prefill_found_id: int = None, prefill_lost_id: int = None, on_submitted=None):
        super().__init__(parent)
        self.title("Submit Ownership Claim – CampusFind")
        self.geometry("560x640")
        self.resizable(False, False)
        self.grab_set()

        self.on_submitted = on_submitted
        self._prefill_found_id = prefill_found_id
        self._prefill_lost_id = prefill_lost_id

        # Get parent controller for current_user
        controller = getattr(parent, 'controller', parent)
        self.current_user = getattr(controller, 'current_user', None)

        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)

        # Header
        header = ctk.CTkFrame(self, corner_radius=0)
        header.pack(fill="x", padx=0, pady=0)
        ctk.CTkLabel(
            header, text="📝  Submit Ownership Claim",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(anchor="w", padx=20, pady=(16, 4))
        ctk.CTkLabel(
            header,
            text="Provide proof and specific distinguishing features to verify your ownership.",
            font=ctk.CTkFont(size=11), text_color="gray"
        ).pack(anchor="w", padx=20, pady=(0, 12))

        scroll = ctk.CTkScrollableFrame(self, corner_radius=0)
        scroll.pack(fill="both", expand=True, padx=20, pady=10)
        scroll.grid_columnconfigure(0, weight=1)

        row = 0

        # Found Item Selection
        ctk.CTkLabel(scroll, text="Select Found Item *", font=ctk.CTkFont(weight="bold")).grid(
            row=row, column=0, sticky="w", pady=(4, 2))
        row += 1

        all_found = db.get_all_items(item_type="found", status="open")
        self._found_items_map = {}
        found_options = []
        prefill_found_str = None

        for item in all_found:
            label = f"#{item['item_id']} - {item['item_name']} ({item['category']}) in {item['location']}"
            self._found_items_map[label] = item['item_id']
            found_options.append(label)
            if self._prefill_found_id and item['item_id'] == self._prefill_found_id:
                prefill_found_str = label

        if not found_options:
            found_options = ["No open found items available"]
            self._found_items_map["No open found items available"] = None

        default_found = prefill_found_str if prefill_found_str else found_options[0]
        self.found_var = ctk.StringVar(value=default_found)
        self.found_menu = ctk.CTkOptionMenu(
            scroll, variable=self.found_var, values=found_options, height=36)
        self.found_menu.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        row += 1

        # Related Lost Report
        ctk.CTkLabel(scroll, text="Your Related Lost Report (optional)", font=ctk.CTkFont(weight="bold")).grid(
            row=row, column=0, sticky="w", pady=(4, 2))
        row += 1

        user_lost = []
        if self.current_user:
            user_lost = db.get_items_by_user(self.current_user['user_id'], item_type="lost")

        self._lost_items_map = {"(None / Not Reported Yet)": None}
        lost_options = ["(None / Not Reported Yet)"]
        prefill_lost_str = None

        for item in user_lost:
            label = f"#{item['item_id']} - {item['item_name']} (Lost on {item['item_date']})"
            self._lost_items_map[label] = item['item_id']
            lost_options.append(label)
            if self._prefill_lost_id and item['item_id'] == self._prefill_lost_id:
                prefill_lost_str = label

        default_lost = prefill_lost_str if prefill_lost_str else lost_options[0]
        self.lost_var = ctk.StringVar(value=default_lost)
        self.lost_menu = ctk.CTkOptionMenu(
            scroll, variable=self.lost_var, values=lost_options, height=36)
        self.lost_menu.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        row += 1

        # Proof / Description of Ownership
        ctk.CTkLabel(
            scroll, text="Proof & Description of Ownership *", font=ctk.CTkFont(weight="bold")
        ).grid(row=row, column=0, sticky="w", pady=(4, 2))
        row += 1
        ctk.CTkLabel(
            scroll,
            text="Describe unique marks, serial numbers, wallpaper, contents, or purchase info.",
            font=ctk.CTkFont(size=11), text_color="gray"
        ).grid(row=row, column=0, sticky="w", pady=(0, 2))
        row += 1

        self.claim_details_box = ctk.CTkTextbox(scroll, height=110)
        self.claim_details_box.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        row += 1

        # Additional Identifying Information
        ctk.CTkLabel(
            scroll, text="Additional Verification Details (optional)", font=ctk.CTkFont(weight="bold")
        ).grid(row=row, column=0, sticky="w", pady=(4, 2))
        row += 1
        self.additional_box = ctk.CTkTextbox(scroll, height=70)
        self.additional_box.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        row += 1

        # Contact Email
        ctk.CTkLabel(scroll, text="Contact Email Address *", font=ctk.CTkFont(weight="bold")).grid(
            row=row, column=0, sticky="w", pady=(4, 2))
        row += 1
        self.contact_entry = ctk.CTkEntry(scroll, height=36)
        self.contact_entry.grid(row=row, column=0, sticky="ew", pady=(0, 16))
        if self.current_user:
            self.contact_entry.insert(0, self.current_user.get('email', ''))
        row += 1

        # Action Buttons
        btn_box = ctk.CTkFrame(self, corner_radius=0)
        btn_box.pack(fill="x", padx=20, pady=(0, 16))

        ctk.CTkButton(
            btn_box, text="Cancel", width=100, command=self.destroy
        ).pack(side="left")

        self.submit_btn = ctk.CTkButton(
            btn_box, text="Submit Claim", width=140,
            command=self._do_submit
        )
        self.submit_btn.pack(side="right")

    def _do_submit(self):
        if not self.current_user:
            messagebox.showerror("Error", "You must be logged in to submit a claim.")
            return

        found_key = self.found_var.get()
        found_id = self._found_items_map.get(found_key)
        if not found_id:
            messagebox.showerror("Validation Error", "Please select a valid found item.")
            return

        # Check that claimant is not the person who reported it found
        found_item = db.get_item_by_id(found_id)
        if found_item and found_item.get('user_id') == self.current_user['user_id']:
            messagebox.showerror("Invalid Claim", "You cannot submit an ownership claim on an item you reported found.")
            return

        lost_key = self.lost_var.get()
        lost_id = self._lost_items_map.get(lost_key)

        details = self.claim_details_box.get("1.0", "end-1c").strip()
        additional = self.additional_box.get("1.0", "end-1c").strip()
        contact = self.contact_entry.get().strip()

        if len(details) < 20:
            messagebox.showerror(
                "Validation Error",
                "Please provide a thorough description of ownership (at least 20 characters)."
            )
            return

        if not contact:
            messagebox.showerror("Validation Error", "Contact email is required.")
            return

        try:
            claim_id = db.create_claim(
                lost_item_id=lost_id,
                found_item_id=found_id,
                claimant_id=self.current_user['user_id'],
                claim_details=details,
                additional_info=additional,
                contact_email=contact
            )

            # Notifications & logging
            db.log_activity(
                self.current_user['user_id'],
                'submit_claim',
                f"Submitted claim #{claim_id} on item #{found_id}"
            )
            db.create_notification(
                self.current_user['user_id'],
                "Claim Submitted",
                f"Your claim #{claim_id} for '{found_item.get('item_name')}' is now pending review by administrators.",
                "claim_status"
            )

            # Optional email notification
            email_service.send_claim_submitted(
                admin_email="admin@campusfind.local",
                claimant_name=self.current_user.get('full_name', 'Student'),
                item_name=found_item.get('item_name', 'Item'),
                claim_id=claim_id
            )

            messagebox.showinfo(
                "Claim Submitted",
                f"Claim #{claim_id} has been submitted successfully.\n"
                "The administrator will review your evidence and update the status."
            )

            if callable(self.on_submitted):
                self.on_submitted()

            self.destroy()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to submit claim: {e}")


# ---------------------------------------------------------------------------
# ClaimsFrame GUI (My Claims)
# ---------------------------------------------------------------------------
class ClaimsFrame(ctk.CTkFrame):
    """Screen for viewing the user's submitted ownership claims."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.theme = None
        self._filter_status = "all"
        self._claims_cache = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_ui()

    def _build_ui(self):
        # 1. Header
        header = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header, text="📝  My Ownership Claims",
            font=ctk.CTkFont(size=22, weight="bold")
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            header, text="Track the review status and administrative remarks for all your submitted claims.",
            font=ctk.CTkFont(size=12), text_color=("gray50", "gray60")
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))

        btn_box = ctk.CTkFrame(header, fg_color="transparent")
        btn_box.grid(row=0, column=1, rowspan=2, sticky="e")

        self.new_claim_btn = ctk.CTkButton(
            btn_box, text="+ New Claim", width=120,
            command=self._open_new_claim
        )
        self.new_claim_btn.pack(side="right", padx=5)

        # 2. Filter tabs
        filter_bar = ctk.CTkFrame(self, corner_radius=8)
        filter_bar.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))

        self.tab_buttons = {}
        statuses = [
            ("All", "all"),
            ("Pending", "pending"),
            ("Under Review", "under_review"),
            ("Approved", "approved"),
            ("Rejected", "rejected"),
            ("Returned", "returned")
        ]
        for label, code in statuses:
            btn = ctk.CTkButton(
                filter_bar, text=label, width=90, height=30,
                fg_color="transparent",
                command=lambda c=code: self._set_filter(c)
            )
            btn.pack(side="left", padx=4, pady=6)
            self.tab_buttons[code] = btn

        self.count_label = ctk.CTkLabel(
            filter_bar, text="0 claims", font=ctk.CTkFont(size=12, weight="bold")
        )
        self.count_label.pack(side="right", padx=16, pady=6)

        # 3. Scrollable claims area
        self.scroll = ctk.CTkScrollableFrame(self, corner_radius=10)
        self.scroll.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.scroll.grid_columnconfigure(0, weight=1)

    def refresh_data(self):
        """Called upon navigation to reload claims."""
        self.load_claims()

    def _set_filter(self, status: str):
        self._filter_status = status
        theme = self.theme or {}
        accent = theme.get("accent_primary", "#2d7a2d")
        for code, btn in self.tab_buttons.items():
            if code == status:
                btn.configure(fg_color=accent, text_color="white")
            else:
                btn.configure(fg_color="transparent", text_color=theme.get("text_primary", "black"))
        self._render_claims()

    def _open_new_claim(self):
        dlg = SubmitClaimDialog(self, on_submitted=self.load_claims)
        dlg.focus()

    def load_claims(self):
        user = getattr(self.controller, 'current_user', None)
        if not user:
            return
        self._claims_cache = db.get_claims_by_user(user['user_id'])
        self._render_claims()

    def _render_claims(self):
        for w in self.scroll.winfo_children():
            w.destroy()

        filtered = []
        for c in self._claims_cache:
            if self._filter_status != "all" and c.get('claim_status') != self._filter_status:
                continue
            filtered.append(c)

        self.count_label.configure(text=f"{len(filtered)} claim(s)")

        if not filtered:
            box = ctk.CTkFrame(self.scroll, fg_color="transparent")
            box.pack(expand=True, fill="both", pady=60)
            ctk.CTkLabel(box, text="📋", font=ctk.CTkFont(size=44)).pack(pady=(0, 8))
            ctk.CTkLabel(box, text="No claims found.", font=ctk.CTkFont(size=15, weight="bold")).pack()
            ctk.CTkLabel(
                box,
                text="When you see a found item that belongs to you, submit a claim with proof of ownership.",
                font=ctk.CTkFont(size=12), text_color="gray"
            ).pack(pady=4)
            return

        for claim in filtered:
            self._render_claim_row(claim)

    def _render_claim_row(self, claim: dict):
        found_item = db.get_item_by_id(claim.get('found_item_id')) or {}
        lost_item = db.get_item_by_id(claim.get('lost_item_id')) if claim.get('lost_item_id') else None
        status = claim.get('claim_status', 'pending')
        badge_bg, badge_fg = _get_status_style(status)

        row = ctk.CTkFrame(self.scroll, corner_radius=10)
        row.pack(fill="x", padx=10, pady=6)
        row.grid_columnconfigure(1, weight=1)

        # Left: Icon & Claim ID
        left = ctk.CTkFrame(row, fg_color="transparent")
        left.grid(row=0, column=0, padx=14, pady=12, sticky="w")
        ctk.CTkLabel(
            left, text=f"Claim #{claim.get('claim_id')}",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w")
        ctk.CTkLabel(
            left, text=f"Submitted: {str(claim.get('created_at', ''))[:10]}",
            font=ctk.CTkFont(size=11), text_color="gray"
        ).pack(anchor="w")

        # Center: Item Info
        center = ctk.CTkFrame(row, fg_color="transparent")
        center.grid(row=0, column=1, padx=14, pady=12, sticky="w")
        ctk.CTkLabel(
            center, text=f"Found Item: {found_item.get('item_name', 'Unknown')}",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w")

        detail_sub = f"Location: {found_item.get('location', '-')} • Category: {found_item.get('category', '-')}"
        if lost_item:
            detail_sub += f"\nLinked Lost Report: #{lost_item.get('item_id')} - {lost_item.get('item_name')}"
        ctk.CTkLabel(
            center, text=detail_sub,
            font=ctk.CTkFont(size=11), text_color="gray", justify="left"
        ).pack(anchor="w")

        # Right: Status Badge & View Button
        right = ctk.CTkFrame(row, fg_color="transparent")
        right.grid(row=0, column=2, padx=14, pady=12, sticky="e")

        status_lbl = ctk.CTkLabel(
            right, text=f"  {status.replace('_', ' ').upper()}  ",
            fg_color=badge_bg, text_color=badge_fg,
            corner_radius=6, font=ctk.CTkFont(size=11, weight="bold")
        )
        status_lbl.pack(side="left", padx=10)

        view_btn = ctk.CTkButton(
            right, text="View Details", width=100, height=32,
            command=lambda: self._view_claim_details(claim, found_item, lost_item)
        )
        view_btn.pack(side="left")

    def _view_claim_details(self, claim: dict, found_item: dict, lost_item: dict):
        """Displays popup showing full claim info and admin remarks."""
        dlg = ctk.CTkToplevel(self)
        dlg.title(f"Claim #{claim.get('claim_id')} Details")
        dlg.geometry("500x560")
        dlg.grab_set()

        ctk.CTkLabel(
            dlg, text=f"🔍  Claim #{claim.get('claim_id')} Summary",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(16, 8), padx=20, anchor="w")

        scroll = ctk.CTkScrollableFrame(dlg)
        scroll.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        # Status badge
        status = claim.get('claim_status', 'pending')
        bg_col, fg_col = _get_status_style(status)
        badge = ctk.CTkLabel(
            scroll, text=f"  Current Status: {status.replace('_', ' ').upper()}  ",
            fg_color=bg_col, text_color=fg_col, corner_radius=6,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        badge.pack(anchor="w", pady=(0, 10))

        # Info cards
        items_data = [
            ("Item Claimed", found_item.get('item_name', 'Unknown')),
            ("Found Location", found_item.get('location', '-')),
            ("Found Date", str(found_item.get('item_date', '-'))),
            ("Date Submitted", str(claim.get('created_at', '-'))),
            ("Last Updated", str(claim.get('updated_at', '-'))),
            ("Contact Email", claim.get('contact_email', '-')),
        ]
        for label, val in items_data:
            f = ctk.CTkFrame(scroll, fg_color="transparent")
            f.pack(fill="x", pady=2)
            ctk.CTkLabel(f, text=f"{label}:", font=ctk.CTkFont(weight="bold", size=12), width=130, anchor="w").pack(side="left")
            ctk.CTkLabel(f, text=str(val), font=ctk.CTkFont(size=12), anchor="w").pack(side="left")

        # Details
        ctk.CTkLabel(scroll, text="Your Ownership Description:", font=ctk.CTkFont(weight="bold", size=12)).pack(anchor="w", pady=(10, 2))
        tb1 = ctk.CTkTextbox(scroll, height=70)
        tb1.pack(fill="x", pady=(0, 8))
        tb1.insert("1.0", claim.get('claim_details', ''))
        tb1.configure(state="disabled")

        if claim.get('additional_info'):
            ctk.CTkLabel(scroll, text="Additional Verification Info:", font=ctk.CTkFont(weight="bold", size=12)).pack(anchor="w", pady=(4, 2))
            tb2 = ctk.CTkTextbox(scroll, height=50)
            tb2.pack(fill="x", pady=(0, 8))
            tb2.insert("1.0", claim.get('additional_info', ''))
            tb2.configure(state="disabled")

        # Admin Remarks
        ctk.CTkLabel(scroll, text="Admin Remarks:", font=ctk.CTkFont(weight="bold", size=12), text_color="#c62828").pack(anchor="w", pady=(6, 2))
        tb3 = ctk.CTkTextbox(scroll, height=60)
        tb3.pack(fill="x", pady=(0, 8))
        remarks = claim.get('admin_remarks') or "No administrative remarks posted yet."
        tb3.insert("1.0", remarks)
        tb3.configure(state="disabled")

        ctk.CTkButton(dlg, text="Close", width=120, command=dlg.destroy).pack(pady=10)

    def apply_theme(self, theme: dict):
        self.theme = theme
        try:
            self.configure(fg_color=theme.get("bg_primary", "transparent"))
            accent = theme.get("accent_primary", "#2d7a2d")
            self.new_claim_btn.configure(
                fg_color=accent,
                hover_color=theme.get("accent_hover", "#1f5a1f")
            )
            self._set_filter(self._filter_status)
        except Exception:
            pass
