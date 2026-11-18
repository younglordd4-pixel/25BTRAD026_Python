"""
CampusFind - Administrator Reports Management Module
Complete administrative interface for viewing, filtering, moderating, updating, and exporting all item reports.
"""

from datetime import datetime
import customtkinter as ctk
from tkinter import messagebox

try:
    from config import CATEGORIES, CAMPUS_LOCATIONS
except ImportError:
    CATEGORIES = ["Electronics", "Personal Belongings", "Documents & ID Cards",
                  "Books & Stationery", "Clothing & Accessories", "Keys", "Other"]
    CAMPUS_LOCATIONS = ["Library", "Cafeteria", "Main Block", "Science Block",
                        "Engineering Block", "Sports Complex", "Hostel",
                        "Parking Area", "Auditorium", "Admin Block", "Other"]

from database import db
from services.pdf_service import pdf_service
from services.image_service import image_service
from services.qr_service import qr_service
from student.matching import matching_engine


class AdminReportsFrame(ctk.CTkFrame):
    """Admin panel to oversee all lost and found item reports."""

    ITEMS_PER_PAGE = 15

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.theme = None
        self._current_type = "lost"  # "lost" or "found"
        self._all_items = []
        self._filtered_items = []
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
            top_f, text="📋  All Item Reports Management",
            font=ctk.CTkFont(size=22, weight="bold")
        ).grid(row=0, column=0, sticky="w")

        btn_box = ctk.CTkFrame(top_f, fg_color="transparent")
        btn_box.grid(row=0, column=1, sticky="e")

        self.match_btn = ctk.CTkButton(
            btn_box, text="⚡ Run Matching", width=120, height=34,
            command=self._run_matching
        )
        self.match_btn.pack(side="right", padx=(6, 0))

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

        # 2. Filter Bar with Tabs
        filter_bar = ctk.CTkFrame(self, corner_radius=10)
        filter_bar.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 10))

        # Tabs for Lost vs Found
        self.tab_lost = ctk.CTkButton(
            filter_bar, text="Lost Items", width=110, height=34,
            command=lambda: self._set_type("lost")
        )
        self.tab_lost.pack(side="left", padx=(10, 4), pady=8)

        self.tab_found = ctk.CTkButton(
            filter_bar, text="Found Items", width=110, height=34,
            fg_color="transparent", command=lambda: self._set_type("found")
        )
        self.tab_found.pack(side="left", padx=4, pady=8)

        # Keyword search
        self.search_entry = ctk.CTkEntry(
            filter_bar, placeholder_text="Search reports...", width=200, height=34
        )
        self.search_entry.pack(side="left", padx=(12, 6))
        self.search_entry.bind("<Return>", lambda _: self._filter_items())

        ctk.CTkButton(
            filter_bar, text="Go", width=50, height=34, command=self._filter_items
        ).pack(side="left", padx=(0, 10))

        # Category dropdown
        cat_vals = ["All Categories"] + CATEGORIES
        self.cat_var = ctk.StringVar(value="All Categories")
        self.cat_menu = ctk.CTkOptionMenu(
            filter_bar, variable=self.cat_var, values=cat_vals,
            width=140, height=34, command=lambda _: self._filter_items()
        )
        self.cat_menu.pack(side="left", padx=4)

        # Status dropdown
        self.status_var = ctk.StringVar(value="All Statuses")
        self.status_menu = ctk.CTkOptionMenu(
            filter_bar, variable=self.status_var,
            values=["All Statuses", "open", "closed", "returned"],
            width=120, height=34, command=lambda _: self._filter_items()
        )
        self.status_menu.pack(side="left", padx=4)

        self.count_lbl = ctk.CTkLabel(
            filter_bar, text="0 items", font=ctk.CTkFont(size=12, weight="bold")
        )
        self.count_lbl.pack(side="right", padx=16)

        # 3. Items Scrollable Table
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
        self._all_items = db.get_all_items()
        self._filter_items()

    def _set_type(self, item_type: str):
        self._current_type = item_type
        theme = self.theme or {}
        accent = theme.get("accent_primary", "#2d7a2d")
        if item_type == "lost":
            self.tab_lost.configure(fg_color=accent, text_color="white")
            self.tab_found.configure(fg_color="transparent", text_color=theme.get("text_primary", "black"))
        else:
            self.tab_found.configure(fg_color=accent, text_color="white")
            self.tab_lost.configure(fg_color="transparent", text_color=theme.get("text_primary", "black"))
        self._filter_items()

    def _filter_items(self):
        query = self.search_entry.get().strip().lower()
        cat_sel = self.cat_var.get()
        stat_sel = self.status_var.get()

        filtered = []
        for it in self._all_items:
            if it.get('item_type') != self._current_type:
                continue
            if cat_sel != "All Categories" and it.get('category') != cat_sel:
                continue
            if stat_sel != "All Statuses" and it.get('status') != stat_sel:
                continue
            if query:
                match = (
                    query in str(it.get('item_name', '')).lower() or
                    query in str(it.get('location', '')).lower() or
                    query in str(it.get('description', '')).lower()
                )
                if not match:
                    continue
            filtered.append(it)

        self._filtered_items = filtered
        self._current_page = 0
        self._render_table()

    def _render_table(self):
        for w in self.scroll.winfo_children():
            w.destroy()

        total = len(self._filtered_items)
        self.count_lbl.configure(text=f"{total} {self._current_type} item(s)")

        total_pages = max(1, (total + self.ITEMS_PER_PAGE - 1) // self.ITEMS_PER_PAGE)
        self.page_lbl.configure(text=f"Page {self._current_page + 1} of {total_pages}")
        self.prev_btn.configure(state="normal" if self._current_page > 0 else "disabled")
        self.next_btn.configure(state="normal" if self._current_page < total_pages - 1 else "disabled")

        # Table Header
        hdr = ctk.CTkFrame(self.scroll, height=36, corner_radius=6)
        hdr.pack(fill="x", pady=(0, 6))
        hdr.grid_columnconfigure(1, weight=1)

        cols = [
            ("ID", 50, 0),
            ("Item Name", 160, 1),
            ("Category", 130, 2),
            ("Location", 130, 3),
            ("Date", 90, 4),
            ("Status", 80, 5),
            ("Actions", 160, 6)
        ]
        for name, w, col in cols:
            lbl = ctk.CTkLabel(hdr, text=name, font=ctk.CTkFont(size=11, weight="bold"), anchor="w")
            lbl.grid(row=0, column=col, padx=8, pady=6, sticky="w")

        start = self._current_page * self.ITEMS_PER_PAGE
        page_items = self._filtered_items[start:start + self.ITEMS_PER_PAGE]

        if not page_items:
            ctk.CTkLabel(
                self.scroll, text=f"No {self._current_type} items found.",
                font=ctk.CTkFont(size=13), text_color="gray"
            ).pack(pady=40)
            return

        for it in page_items:
            self._render_row(it)

    def _render_row(self, item: dict):
        row = ctk.CTkFrame(self.scroll, corner_radius=6)
        row.pack(fill="x", pady=2)
        row.grid_columnconfigure(1, weight=1)

        # ID
        ctk.CTkLabel(row, text=str(item.get('item_id')), width=50, anchor="w").grid(row=0, column=0, padx=8, pady=6, sticky="w")

        # Name
        ctk.CTkLabel(row, text=item.get('item_name', '-'), width=160, font=ctk.CTkFont(weight="bold"), anchor="w").grid(row=0, column=1, padx=8, sticky="w")

        # Category
        ctk.CTkLabel(row, text=item.get('category', '-'), width=130, anchor="w").grid(row=0, column=2, padx=8, sticky="w")

        # Location
        ctk.CTkLabel(row, text=item.get('location', '-'), width=130, anchor="w").grid(row=0, column=3, padx=8, sticky="w")

        # Date
        ctk.CTkLabel(row, text=str(item.get('item_date', '-')), width=90, anchor="w").grid(row=0, column=4, padx=8, sticky="w")

        # Status badge
        st = str(item.get('status', 'open'))
        color_map = {"open": "#2d7a2d", "closed": "gray", "returned": "#388e3c"}
        ctk.CTkLabel(
            row, text=f" {st.upper()} ", fg_color=color_map.get(st, "gray"),
            text_color="white", corner_radius=4, font=ctk.CTkFont(size=10, weight="bold")
        ).grid(row=0, column=5, padx=8, sticky="w")

        # Action Buttons
        act_box = ctk.CTkFrame(row, fg_color="transparent")
        act_box.grid(row=0, column=6, padx=8, pady=4, sticky="e")

        ctk.CTkButton(
            act_box, text="View", width=44, height=26,
            command=lambda it=item: self._view_details(it)
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            act_box, text="Status", width=50, height=26, fg_color="#f57c00",
            command=lambda it=item: self._change_status(it)
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            act_box, text="Del", width=42, height=26, fg_color="#c62828",
            command=lambda it=item: self._delete_item(it)
        ).pack(side="left", padx=2)

    def _view_details(self, item: dict):
        """Displays modal with full item information, reporter, photo, and QR code."""
        dlg = ctk.CTkToplevel(self)
        dlg.title(f"Item #{item.get('item_id')} Details")
        dlg.geometry("540x600")
        dlg.grab_set()

        scroll = ctk.CTkScrollableFrame(dlg)
        scroll.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        reporter = db.get_user_by_id(item.get('user_id')) or {}
        ctk.CTkLabel(
            scroll, text=f"Item #{item.get('item_id')}: {item.get('item_name')}",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(anchor="w", pady=(0, 6))

        # Media section: photo & QR
        media_row = ctk.CTkFrame(scroll, fg_color="transparent")
        media_row.pack(fill="x", pady=(0, 10))

        if item.get('image_path'):
            photo = image_service.get_thumbnail(item['image_path'], size=(130, 130))
            if photo:
                lbl = ctk.CTkLabel(media_row, image=photo, text="")
                lbl.image = photo
                lbl.pack(side="left", padx=(0, 14))

        try:
            qr = qr_service.get_qr_image(item['item_id'], item['item_type'], item['item_name'], size=130)
            if qr:
                qr_box = ctk.CTkFrame(media_row, corner_radius=8)
                qr_box.pack(side="left")
                qlbl = ctk.CTkLabel(qr_box, image=qr, text="")
                qlbl.image = qr
                qlbl.pack(padx=6, pady=4)
                ctk.CTkLabel(qr_box, text="System QR Code", font=ctk.CTkFont(size=10)).pack(pady=(0, 4))
        except Exception:
            pass

        # Details
        fields = [
            ("Item Type", item.get('item_type', '-').upper()),
            ("Category", item.get('category', '-')),
            ("Location", item.get('location', '-')),
            ("Date Reported", str(item.get('item_date', '-'))),
            ("Current Status", str(item.get('status', '-')).upper()),
            ("Reporter Name", reporter.get('full_name', 'Unknown')),
            ("Reporter USN", reporter.get('usn', '-')),
            ("Contact Email", item.get('contact_email', '-')),
        ]
        for f_label, f_val in fields:
            f_row = ctk.CTkFrame(scroll, fg_color="transparent")
            f_row.pack(fill="x", pady=2)
            ctk.CTkLabel(f_row, text=f"{f_label}:", width=120, font=ctk.CTkFont(weight="bold", size=12), anchor="w").pack(side="left")
            ctk.CTkLabel(f_row, text=str(f_val), font=ctk.CTkFont(size=12), anchor="w").pack(side="left")

        ctk.CTkLabel(scroll, text="Description:", font=ctk.CTkFont(weight="bold", size=12)).pack(anchor="w", pady=(8, 2))
        tb = ctk.CTkTextbox(scroll, height=70)
        tb.pack(fill="x", pady=(0, 6))
        tb.insert("1.0", item.get('description', ''))
        tb.configure(state="disabled")

        if item.get('distinguishing_features'):
            ctk.CTkLabel(scroll, text="Distinguishing Features:", font=ctk.CTkFont(weight="bold", size=12)).pack(anchor="w", pady=(4, 2))
            tb2 = ctk.CTkTextbox(scroll, height=50)
            tb2.pack(fill="x", pady=(0, 6))
            tb2.insert("1.0", item.get('distinguishing_features'))
            tb2.configure(state="disabled")

        ctk.CTkButton(dlg, text="Close", width=100, command=dlg.destroy).pack(pady=12)

    def _change_status(self, item: dict):
        """Dialog to update item status."""
        dlg = ctk.CTkToplevel(self)
        dlg.title("Update Status")
        dlg.geometry("340x220")
        dlg.grab_set()

        ctk.CTkLabel(
            dlg, text=f"Update Status for Item #{item['item_id']}",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(16, 10))

        st_var = ctk.StringVar(value=item.get('status', 'open'))
        menu = ctk.CTkOptionMenu(dlg, variable=st_var, values=["open", "closed", "returned"], width=180)
        menu.pack(pady=10)

        def save():
            new_st = st_var.get()
            db.update_item_status(item['item_id'], new_st)
            cur_user = getattr(self.controller, 'current_user', None)
            db.log_activity(
                cur_user['user_id'] if cur_user else 0,
                'update_item_status',
                f"Updated item #{item['item_id']} status to {new_st}"
            )
            dlg.destroy()
            self.refresh_data()
            messagebox.showinfo("Status Updated", f"Item status changed to '{new_st}'.")

        ctk.CTkButton(dlg, text="Save Status", command=save, width=120).pack(pady=10)

    def _delete_item(self, item: dict):
        if messagebox.askyesno("Confirm Delete", f"Delete item report #{item['item_id']} ({item['item_name']})?"):
            db.delete_item(item['item_id'])
            cur_user = getattr(self.controller, 'current_user', None)
            db.log_activity(
                cur_user['user_id'] if cur_user else 0,
                'delete_item',
                f"Deleted item #{item['item_id']}"
            )
            self.refresh_data()
            messagebox.showinfo("Deleted", "Item report deleted successfully.")

    def _run_matching(self):
        try:
            self.match_btn.configure(state="disabled", text="Running...")
            self.update()
            matches = matching_engine.run_matching()
            messagebox.showinfo("Matching Analysis", f"Analysis complete! Found {len(matches)} potential match pair(s).")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to run matching: {e}")
        finally:
            self.match_btn.configure(state="normal", text="⚡ Run Matching")

    def _export_pdf(self):
        try:
            if self._current_type == "lost":
                path = pdf_service.generate_lost_items_report(self._filtered_items)
            else:
                path = pdf_service.generate_found_items_report(self._filtered_items)
            messagebox.showinfo("PDF Generated", f"Report saved successfully:\n{path}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Could not generate PDF: {e}")

    def _prev_page(self):
        if self._current_page > 0:
            self._current_page -= 1
            self._render_table()

    def _next_page(self):
        total = len(self._filtered_items)
        total_pages = max(1, (total + self.ITEMS_PER_PAGE - 1) // self.ITEMS_PER_PAGE)
        if self._current_page < total_pages - 1:
            self._current_page += 1
            self._render_table()

    def apply_theme(self, theme: dict):
        self.theme = theme
        try:
            self.configure(fg_color=theme.get("bg_primary", "transparent"))
            accent = theme.get("accent_primary", "#2d7a2d")
            self.match_btn.configure(
                fg_color=accent,
                hover_color=theme.get("accent_hover", "#1f5a1f")
            )
            self._render_table()
        except Exception:
            pass
