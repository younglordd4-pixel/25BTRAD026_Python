"""
CampusFind - Search and Filter Module
Comprehensive multi-factor search across lost and found belongings with item card views and pagination.
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
from services.image_service import image_service
from services.qr_service import qr_service


class SearchFrame(ctk.CTkFrame):
    """Search and filter screen for all reported items."""

    ITEMS_PER_PAGE = 8

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.theme = None
        self._current_page = 0
        self._results = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_ui()

    def _build_ui(self):
        # 1. Header & Search Bar
        top_box = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        top_box.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        top_box.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            top_box, text="🔍  Search & Browse Campus Belongings",
            font=ctk.CTkFont(size=22, weight="bold")
        ).grid(row=0, column=0, sticky="w")

        # Search Bar Row
        search_row = ctk.CTkFrame(top_box, fg_color="transparent")
        search_row.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        search_row.grid_columnconfigure(0, weight=1)

        self.search_entry = ctk.CTkEntry(
            search_row,
            placeholder_text="Search by item name, description, color, keywords...",
            height=40, font=ctk.CTkFont(size=13)
        )
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.search_entry.bind("<Return>", lambda e: self._do_search())

        self.search_btn = ctk.CTkButton(
            search_row, text="Search", width=100, height=40,
            command=self._do_search
        )
        self.search_btn.grid(row=0, column=1, padx=(0, 6))

        self.clear_btn = ctk.CTkButton(
            search_row, text="Clear", width=80, height=40,
            fg_color="gray", command=self._reset_filters
        )
        self.clear_btn.grid(row=0, column=2)

        # 2. Filters Row
        filter_card = ctk.CTkFrame(self, corner_radius=10)
        filter_card.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))

        # Item Type filter
        ctk.CTkLabel(filter_card, text="Type:", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=(12, 4), pady=10)
        self.type_var = ctk.StringVar(value="All Types")
        self.type_menu = ctk.CTkOptionMenu(
            filter_card, variable=self.type_var,
            values=["All Types", "Lost Items", "Found Items"],
            width=110, height=32, command=lambda _: self._do_search()
        )
        self.type_menu.pack(side="left", padx=(0, 10))

        # Category filter
        ctk.CTkLabel(filter_card, text="Category:", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=(4, 4))
        cat_options = ["All Categories"] + CATEGORIES
        self.cat_var = ctk.StringVar(value="All Categories")
        self.cat_menu = ctk.CTkOptionMenu(
            filter_card, variable=self.cat_var, values=cat_options,
            width=150, height=32, command=lambda _: self._do_search()
        )
        self.cat_menu.pack(side="left", padx=(0, 10))

        # Location filter
        ctk.CTkLabel(filter_card, text="Location:", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=(4, 4))
        loc_options = ["All Locations"] + CAMPUS_LOCATIONS
        self.loc_var = ctk.StringVar(value="All Locations")
        self.loc_menu = ctk.CTkOptionMenu(
            filter_card, variable=self.loc_var, values=loc_options,
            width=140, height=32, command=lambda _: self._do_search()
        )
        self.loc_menu.pack(side="left", padx=(0, 10))

        # Status filter
        ctk.CTkLabel(filter_card, text="Status:", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left", padx=(4, 4))
        self.status_var = ctk.StringVar(value="open")
        self.status_menu = ctk.CTkOptionMenu(
            filter_card, variable=self.status_var,
            values=["All Statuses", "open", "closed", "returned"],
            width=110, height=32, command=lambda _: self._do_search()
        )
        self.status_menu.pack(side="left", padx=(0, 10))

        # Results count label
        self.results_count_lbl = ctk.CTkLabel(
            filter_card, text="0 items", font=ctk.CTkFont(size=12, weight="bold")
        )
        self.results_count_lbl.pack(side="right", padx=16)

        # 3. Results Cards Grid (Scrollable)
        self.scroll = ctk.CTkScrollableFrame(self, corner_radius=10)
        self.scroll.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 10))
        self.scroll.grid_columnconfigure(0, weight=1)
        self.scroll.grid_columnconfigure(1, weight=1)

        # 4. Pagination Row
        page_box = ctk.CTkFrame(self, height=44, corner_radius=0, fg_color="transparent")
        page_box.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 14))

        self.prev_btn = ctk.CTkButton(
            page_box, text="◀ Previous", width=100, height=32,
            command=self._prev_page
        )
        self.prev_btn.pack(side="left")

        self.page_lbl = ctk.CTkLabel(
            page_box, text="Page 1 of 1", font=ctk.CTkFont(size=12, weight="bold")
        )
        self.page_lbl.pack(side="left", padx=16)

        self.next_btn = ctk.CTkButton(
            page_box, text="Next ▶", width=100, height=32,
            command=self._next_page
        )
        self.next_btn.pack(side="left")

    def refresh_data(self):
        """Called whenever this frame is shown."""
        self._do_search()

    def _reset_filters(self):
        self.search_entry.delete(0, "end")
        self.type_var.set("All Types")
        self.cat_var.set("All Categories")
        self.loc_var.set("All Locations")
        self.status_var.set("open")
        self._current_page = 0
        self._do_search()

    def _do_search(self):
        keyword = self.search_entry.get().strip() or None

        # Type filter
        t_sel = self.type_var.get()
        item_type = None
        if t_sel == "Lost Items":
            item_type = "lost"
        elif t_sel == "Found Items":
            item_type = "found"

        # Category filter
        c_sel = self.cat_var.get()
        category = None if c_sel == "All Categories" else c_sel

        # Location filter
        l_sel = self.loc_var.get()
        location = None if l_sel == "All Locations" else l_sel

        # Status filter
        s_sel = self.status_var.get()
        status = None if s_sel == "All Statuses" else s_sel

        self._results = db.get_all_items(
            item_type=item_type,
            status=status,
            category=category,
            location=location,
            keyword=keyword
        )
        self._current_page = 0
        self._render_page()

    def _render_page(self):
        for w in self.scroll.winfo_children():
            w.destroy()

        total = len(self._results)
        self.results_count_lbl.configure(text=f"{total} item(s) found")

        total_pages = max(1, (total + self.ITEMS_PER_PAGE - 1) // self.ITEMS_PER_PAGE)
        self._current_page = min(self._current_page, total_pages - 1)

        self.page_lbl.configure(text=f"Page {self._current_page + 1} of {total_pages}")
        self.prev_btn.configure(state="normal" if self._current_page > 0 else "disabled")
        self.next_btn.configure(state="normal" if self._current_page < total_pages - 1 else "disabled")

        if not self._results:
            empty_box = ctk.CTkFrame(self.scroll, fg_color="transparent")
            empty_box.grid(row=0, column=0, columnspan=2, pady=60)
            ctk.CTkLabel(empty_box, text="🔎", font=ctk.CTkFont(size=44)).pack(pady=(0, 6))
            ctk.CTkLabel(empty_box, text="No items matched your search.", font=ctk.CTkFont(size=16, weight="bold")).pack()
            ctk.CTkLabel(empty_box, text="Try adjusting your keywords, category, or location filters.", font=ctk.CTkFont(size=12), text_color="gray").pack(pady=4)
            return

        start = self._current_page * self.ITEMS_PER_PAGE
        page_items = self._results[start:start + self.ITEMS_PER_PAGE]

        for i, item in enumerate(page_items):
            r = i // 2
            c = i % 2
            self._render_card(item, r, c)

    def _render_card(self, item: dict, row: int, col: int):
        card = ctk.CTkFrame(self.scroll, corner_radius=12)
        card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
        card.grid_columnconfigure(1, weight=1)

        # Left: Image thumbnail or Category Icon
        thumb_frame = ctk.CTkFrame(card, width=110, height=110, corner_radius=8, fg_color=("gray90", "gray25"))
        thumb_frame.grid(row=0, column=0, rowspan=4, padx=10, pady=10)
        thumb_frame.pack_propagate(False)

        photo = None
        if item.get('image_path'):
            photo = image_service.get_thumbnail(item['image_path'], size=(100, 100))

        if photo:
            img_lbl = ctk.CTkLabel(thumb_frame, text="", image=photo)
            img_lbl.image = photo  # keep reference
            img_lbl.pack(expand=True, fill="both")
        else:
            icon_map = {
                "Electronics": "💻",
                "Personal Belongings": "🎒",
                "Documents & ID Cards": "🪪",
                "Books & Stationery": "📚",
                "Clothing & Accessories": "👕",
                "Keys": "🔑",
                "Other": "📦"
            }
            cat_icon = icon_map.get(item.get('category'), "📦")
            ctk.CTkLabel(thumb_frame, text=cat_icon, font=ctk.CTkFont(size=36)).pack(expand=True)

        # Right top: Type badge & Status
        info_top = ctk.CTkFrame(card, fg_color="transparent")
        info_top.grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=(10, 2))

        is_lost = item.get('item_type') == 'lost'
        type_bg = "#c62828" if is_lost else "#2d7a2d"
        type_txt = "LOST" if is_lost else "FOUND"

        ctk.CTkLabel(
            info_top, text=f"  {type_txt}  ", fg_color=type_bg, text_color="white",
            corner_radius=6, font=ctk.CTkFont(size=10, weight="bold")
        ).pack(side="left")

        status_str = str(item.get('status', 'open')).upper()
        ctk.CTkLabel(
            info_top, text=f"•  Status: {status_str}",
            font=ctk.CTkFont(size=11), text_color="gray"
        ).pack(side="left", padx=8)

        # Item Name
        name_lbl = ctk.CTkLabel(
            card, text=item.get('item_name', 'Unnamed Item'),
            font=ctk.CTkFont(size=14, weight="bold"), anchor="w"
        )
        name_lbl.grid(row=1, column=1, sticky="ew", padx=(0, 10))

        # Details line
        cat_loc = f"{item.get('category', '-')} • {item.get('location', '-')}\nDate: {item.get('item_date', '-')}"
        ctk.CTkLabel(
            card, text=cat_loc, font=ctk.CTkFont(size=11),
            text_color="gray", anchor="w", justify="left"
        ).grid(row=2, column=1, sticky="ew", padx=(0, 10), pady=(2, 6))

        # View button
        view_btn = ctk.CTkButton(
            card, text="View Details", height=28, width=100,
            command=lambda it=item: self._show_details(it)
        )
        view_btn.grid(row=3, column=1, sticky="w", padx=(0, 10), pady=(0, 10))

    def _show_details(self, item: dict):
        """Displays full item details dialog with QR code and Claim button."""
        dlg = ctk.CTkToplevel(self)
        dlg.title(f"Item #{item.get('item_id')} – {item.get('item_name')}")
        dlg.geometry("540x620")
        dlg.grab_set()

        scroll = ctk.CTkScrollableFrame(dlg)
        scroll.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        is_lost = item.get('item_type') == 'lost'
        type_bg = "#c62828" if is_lost else "#2d7a2d"
        type_txt = "LOST ITEM" if is_lost else "FOUND ITEM"

        top_f = ctk.CTkFrame(scroll, fg_color="transparent")
        top_f.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            top_f, text=f"  {type_txt}  ", fg_color=type_bg, text_color="white",
            corner_radius=6, font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left")

        ctk.CTkLabel(
            top_f, text=f"Report ID: #{item.get('item_id')}",
            font=ctk.CTkFont(size=12), text_color="gray"
        ).pack(side="left", padx=10)

        ctk.CTkLabel(
            scroll, text=item.get('item_name', 'Item Details'),
            font=ctk.CTkFont(size=20, weight="bold"), anchor="w"
        ).pack(anchor="w", pady=(0, 10))

        # QR Code and Image row
        media_row = ctk.CTkFrame(scroll, fg_color="transparent")
        media_row.pack(fill="x", pady=(0, 12))

        # Image if available
        if item.get('image_path'):
            img_photo = image_service.get_thumbnail(item['image_path'], size=(140, 140))
            if img_photo:
                img_lbl = ctk.CTkLabel(media_row, image=img_photo, text="")
                img_lbl.image = img_photo
                img_lbl.pack(side="left", padx=(0, 16))

        # QR Code Display
        try:
            qr_photo = qr_service.get_qr_image(item['item_id'], item['item_type'], item['item_name'], size=130)
            if qr_photo:
                qr_box = ctk.CTkFrame(media_row, corner_radius=8)
                qr_box.pack(side="left")
                qr_lbl = ctk.CTkLabel(qr_box, image=qr_photo, text="")
                qr_lbl.image = qr_photo
                qr_lbl.pack(padx=6, pady=4)
                ctk.CTkLabel(qr_box, text="Reference QR", font=ctk.CTkFont(size=10)).pack(pady=(0, 4))
        except Exception:
            pass

        # Metadata table
        fields = [
            ("Category", item.get('category', '-')),
            ("Location", item.get('location', '-')),
            ("Date", str(item.get('item_date', '-'))),
            ("Status", str(item.get('status', '-')).upper()),
            ("Contact Email", item.get('contact_email', '-')),
            ("Created", str(item.get('created_at', '-'))[:16]),
        ]
        for f_label, f_val in fields:
            f_row = ctk.CTkFrame(scroll, fg_color="transparent")
            f_row.pack(fill="x", pady=2)
            ctk.CTkLabel(f_row, text=f"{f_label}:", width=120, font=ctk.CTkFont(weight="bold", size=12), anchor="w").pack(side="left")
            ctk.CTkLabel(f_row, text=str(f_val), font=ctk.CTkFont(size=12), anchor="w").pack(side="left")

        # Description
        ctk.CTkLabel(scroll, text="Description:", font=ctk.CTkFont(weight="bold", size=12)).pack(anchor="w", pady=(10, 2))
        desc_box = ctk.CTkTextbox(scroll, height=70)
        desc_box.pack(fill="x", pady=(0, 6))
        desc_box.insert("1.0", item.get('description', 'No description provided.'))
        desc_box.configure(state="disabled")

        if item.get('distinguishing_features'):
            ctk.CTkLabel(scroll, text="Distinguishing Features:", font=ctk.CTkFont(weight="bold", size=12)).pack(anchor="w", pady=(4, 2))
            feat_box = ctk.CTkTextbox(scroll, height=50)
            feat_box.pack(fill="x", pady=(0, 6))
            feat_box.insert("1.0", item.get('distinguishing_features'))
            feat_box.configure(state="disabled")

        # Buttons
        btn_box = ctk.CTkFrame(dlg, corner_radius=0)
        btn_box.pack(fill="x", padx=20, pady=(0, 16))

        ctk.CTkButton(btn_box, text="Close", width=100, command=dlg.destroy).pack(side="left")

        # If it's a found item, allow claiming!
        user = getattr(self.controller, 'current_user', None)
        if not is_lost and item.get('status') == 'open' and user and user['user_id'] != item.get('user_id'):
            def open_claim():
                dlg.destroy()
                from student.claims import SubmitClaimDialog
                SubmitClaimDialog(self, prefill_found_id=item['item_id']).focus()

            ctk.CTkButton(
                btn_box, text="Claim This Item", width=140,
                fg_color="#2d7a2d", command=open_claim
            ).pack(side="right")

    def _prev_page(self):
        if self._current_page > 0:
            self._current_page -= 1
            self._render_page()

    def _next_page(self):
        total = len(self._results)
        total_pages = max(1, (total + self.ITEMS_PER_PAGE - 1) // self.ITEMS_PER_PAGE)
        if self._current_page < total_pages - 1:
            self._current_page += 1
            self._render_page()

    def apply_theme(self, theme: dict):
        self.theme = theme
        try:
            self.configure(fg_color=theme.get("bg_primary", "transparent"))
            accent = theme.get("accent_primary", "#2d7a2d")
            self.search_btn.configure(
                fg_color=accent,
                hover_color=theme.get("accent_hover", "#1f5a1f")
            )
            self._render_page()
        except Exception:
            pass
