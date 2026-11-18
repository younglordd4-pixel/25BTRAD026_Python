"""
Lost Items Module - CampusFind
ReportLostFrame  : form to report a lost item
MyLostFoundFrame : view/manage the user's own reports
"""

import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime

import customtkinter as ctk

try:
    from config import CATEGORIES, CAMPUS_LOCATIONS, UPLOADS_DIR
except ImportError:
    CATEGORIES = ["Electronics", "Personal Belongings", "Documents & ID Cards",
                  "Books & Stationery", "Clothing & Accessories", "Keys", "Other"]
    CAMPUS_LOCATIONS = ["Library", "Cafeteria", "Main Block", "Science Block",
                        "Engineering Block", "Sports Complex", "Hostel",
                        "Parking Area", "Auditorium", "Admin Block", "Other"]
    UPLOADS_DIR = None


# ---------------------------------------------------------------------------
# ReportLostFrame
# ---------------------------------------------------------------------------

class ReportLostFrame(ctk.CTkFrame):
    """Form for reporting a lost item."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.theme = None
        self._image_path = None
        self._image_dest = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_ui()

    # -----------------------------------------------------------------------
    # UI
    # -----------------------------------------------------------------------

    def _build_ui(self):
        # Outer scrollable container
        self.scroll = ctk.CTkScrollableFrame(self)
        self.scroll.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.scroll.grid_columnconfigure(0, weight=1)
        self.scroll.grid_columnconfigure(1, weight=1)

        row = 0

        # Title
        title = ctk.CTkLabel(
            self.scroll,
            text="📋  Report Lost Item",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        title.grid(row=row, column=0, columnspan=2, sticky="w", padx=20, pady=(20, 4))
        row += 1

        sep = ctk.CTkFrame(self.scroll, height=2)
        sep.grid(row=row, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 14))
        row += 1

        # Item Name
        ctk.CTkLabel(self.scroll, text="Item Name *").grid(
            row=row, column=0, sticky="w", padx=20, pady=(0, 2))
        row += 1
        self.item_name_entry = ctk.CTkEntry(
            self.scroll, placeholder_text="e.g. Blue backpack", height=36)
        self.item_name_entry.grid(row=row, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 10))
        row += 1

        # Category
        ctk.CTkLabel(self.scroll, text="Category *").grid(
            row=row, column=0, sticky="w", padx=20, pady=(0, 2))
        row += 1
        self.category_var = ctk.StringVar(value=CATEGORIES[0])
        self.category_menu = ctk.CTkOptionMenu(
            self.scroll, variable=self.category_var, values=CATEGORIES, height=36)
        self.category_menu.grid(row=row, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 10))
        row += 1

        # Lost Location
        ctk.CTkLabel(self.scroll, text="Lost Location *").grid(
            row=row, column=0, sticky="w", padx=20, pady=(0, 2))
        row += 1
        self.location_var = ctk.StringVar(value=CAMPUS_LOCATIONS[0])
        self.location_menu = ctk.CTkOptionMenu(
            self.scroll, variable=self.location_var,
            values=CAMPUS_LOCATIONS, height=36,
            command=self._on_location_change,
        )
        self.location_menu.grid(row=row, column=0, sticky="ew", padx=(20, 6), pady=(0, 10))

        self.location_custom = ctk.CTkEntry(
            self.scroll, placeholder_text="Custom location (optional)", height=36)
        self.location_custom.grid(row=row, column=1, sticky="ew", padx=(0, 20), pady=(0, 10))
        row += 1

        # Lost Date
        ctk.CTkLabel(self.scroll, text="Lost Date *").grid(
            row=row, column=0, sticky="w", padx=20, pady=(0, 2))
        row += 1
        self.date_entry = ctk.CTkEntry(
            self.scroll, placeholder_text="YYYY-MM-DD", height=36)
        self.date_entry.grid(row=row, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 10))
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        row += 1

        # Description
        ctk.CTkLabel(self.scroll, text="Description (at least 100 characters encouraged)").grid(
            row=row, column=0, columnspan=2, sticky="w", padx=20, pady=(0, 2))
        row += 1
        self.description_box = ctk.CTkTextbox(self.scroll, height=100)
        self.description_box.grid(row=row, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 10))
        row += 1

        # Distinguishing Features
        ctk.CTkLabel(self.scroll, text="Distinguishing Features").grid(
            row=row, column=0, columnspan=2, sticky="w", padx=20, pady=(0, 2))
        row += 1
        self.features_box = ctk.CTkTextbox(self.scroll, height=70)
        self.features_box.grid(row=row, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 10))
        row += 1

        # Contact Email
        ctk.CTkLabel(self.scroll, text="Contact Email *").grid(
            row=row, column=0, sticky="w", padx=20, pady=(0, 2))
        row += 1
        self.email_entry = ctk.CTkEntry(self.scroll, height=36)
        self.email_entry.grid(row=row, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 10))
        try:
            user = self.controller.current_user
            if user:
                self.email_entry.insert(0, user.get("email", ""))
        except Exception:
            pass
        row += 1

        # Image Upload
        ctk.CTkLabel(self.scroll, text="Item Image (optional)").grid(
            row=row, column=0, sticky="w", padx=20, pady=(0, 2))
        row += 1

        img_row_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        img_row_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 10))

        self.upload_btn = ctk.CTkButton(
            img_row_frame, text="📷 Upload Image", width=140, command=self._upload_image)
        self.upload_btn.pack(side="left", padx=(0, 14))

        self.image_preview = ctk.CTkLabel(
            img_row_frame, text="No image selected", width=150, height=150)
        self.image_preview.pack(side="left")
        row += 1

        # Buttons
        btn_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        btn_frame.grid(row=row, column=0, columnspan=2, sticky="e", padx=20, pady=(10, 20))

        ctk.CTkButton(
            btn_frame, text="Cancel", width=110,
            command=lambda: self.controller.show_frame("dashboard"),
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            btn_frame, text="Submit Report", width=140, command=self._submit
        ).pack(side="left")
        row += 1

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _on_location_change(self, value):
        if value == "Other":
            self.location_custom.configure(state="normal")
        else:
            self.location_custom.configure(state="normal")

    def _upload_image(self):
        path = filedialog.askopenfilename(
            title="Select Item Image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.webp *.bmp")],
        )
        if not path:
            return
        try:
            img_svc = None
            try:
                from services.image_service import image_service
                img_svc = image_service
            except ImportError:
                pass

            if img_svc:
                ok, msg = img_svc.validate_image(path)
                if not ok:
                    messagebox.showerror("Invalid Image", msg)
                    return
                thumb = img_svc.create_thumbnail(path, size=(150, 150))
                if thumb:
                    self.image_preview.configure(image=thumb, text="")
            else:
                try:
                    from PIL import Image, ImageTk
                    img = Image.open(path).resize((150, 150))
                    photo = ImageTk.PhotoImage(img)
                    self.image_preview.configure(image=photo, text="")
                    self.image_preview._photo = photo
                except Exception:
                    self.image_preview.configure(text="Image selected ✓")

            self._image_path = path
        except Exception as exc:
            messagebox.showerror("Image Error", str(exc))

    def _submit(self):
        name = self.item_name_entry.get().strip()
        category = self.category_var.get()
        location = self.location_var.get()
        if location == "Other":
            custom_loc = self.location_custom.get().strip()
            if custom_loc:
                location = custom_loc
        date_str = self.date_entry.get().strip()
        description = self.description_box.get("1.0", "end").strip()
        features = self.features_box.get("1.0", "end").strip()
        email = self.email_entry.get().strip()

        # Validation
        errors = []
        if not name:
            errors.append("Item Name is required.")
        if not date_str:
            errors.append("Lost Date is required.")
        else:
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                errors.append("Lost Date must be in YYYY-MM-DD format.")
        if not email:
            errors.append("Contact Email is required.")
        if errors:
            messagebox.showerror("Validation Error", "\n".join(errors))
            return

        try:
            user = self.controller.current_user
            user_id = user.get("id") or user.get("user_id")
            db = self.controller.db

            image_filename = None
            if self._image_path:
                try:
                    uploads = UPLOADS_DIR
                    if uploads is None:
                        from config import UPLOADS_DIR as ud
                        uploads = ud
                    ext = os.path.splitext(self._image_path)[1]
                    image_filename = f"lost_{user_id}_{int(datetime.now().timestamp())}{ext}"
                    shutil.copy2(self._image_path, os.path.join(str(uploads), image_filename))
                except Exception as img_err:
                    print(f"[ReportLostFrame] Image copy error: {img_err}")

            db.create_item(
                user_id=user_id,
                item_type="lost",
                item_name=name,
                category=category,
                location=location,
                date_reported=date_str,
                description=description,
                features=features,
                contact_email=email,
                image_filename=image_filename,
                status="open",
            )
            messagebox.showinfo("Success", "Lost item report submitted successfully!")
            self._reset_form()
            self.controller.show_frame("my_reports")
        except Exception as exc:
            messagebox.showerror("Error", f"Failed to submit report:\n{exc}")

    def _reset_form(self):
        self.item_name_entry.delete(0, "end")
        self.category_var.set(CATEGORIES[0])
        self.location_var.set(CAMPUS_LOCATIONS[0])
        self.date_entry.delete(0, "end")
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.description_box.delete("1.0", "end")
        self.features_box.delete("1.0", "end")
        self._image_path = None
        self.image_preview.configure(image=None, text="No image selected")

    def apply_theme(self, theme):
        self.theme = theme
        try:
            self.configure(fg_color=theme["bg_primary"])
            self.scroll.configure(fg_color=theme["bg_card"])
            self.upload_btn.configure(
                fg_color=theme["btn_secondary_bg"],
                text_color=theme["btn_secondary_fg"],
                hover_color=theme["accent_hover"],
            )
        except Exception as exc:
            print(f"[ReportLostFrame] apply_theme error: {exc}")


# ---------------------------------------------------------------------------
# MyLostFoundFrame
# ---------------------------------------------------------------------------

class MyLostFoundFrame(ctk.CTkFrame):
    """View, filter, and manage the current user's lost/found reports."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.theme = None
        self._current_filter = "all"
        self._rows = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_ui()

    # -----------------------------------------------------------------------
    # UI
    # -----------------------------------------------------------------------

    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self)
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 0))
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header, text="📄 My Reports",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=(10, 20), pady=10)

        # Filter tabs
        tab_frame = ctk.CTkFrame(header, fg_color="transparent")
        tab_frame.grid(row=0, column=1, sticky="w")

        self._tab_buttons = {}
        for label in ("All", "Lost", "Found"):
            key = label.lower()
            btn = ctk.CTkButton(
                tab_frame, text=label, width=80,
                command=lambda k=key: self._set_filter(k),
            )
            btn.pack(side="left", padx=4)
            self._tab_buttons[key] = btn

        # Export PDF button
        self.export_btn = ctk.CTkButton(
            header, text="📄 Export PDF", width=130,
            command=self._export_pdf,
        )
        self.export_btn.grid(row=0, column=2, padx=(0, 10), pady=10)

        # Table header
        col_frame = ctk.CTkFrame(self)
        col_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(60, 0))
        for i, label in enumerate(("ID", "Item Name", "Category", "Location", "Date", "Status", "Actions")):
            w = 60 if i in (0, 5) else (200 if i == 1 else 110)
            ctk.CTkLabel(col_frame, text=label, font=ctk.CTkFont(size=12, weight="bold"), width=w).grid(
                row=0, column=i, padx=4, pady=4, sticky="w")

        # Scrollable body
        self.table_scroll = ctk.CTkScrollableFrame(self)
        self.table_scroll.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 10))
        self.table_scroll.grid_columnconfigure((0, 1, 2, 3, 4, 5, 6), weight=1)

    # -----------------------------------------------------------------------
    # Data
    # -----------------------------------------------------------------------

    def refresh_data(self):
        self._load_reports()

    def _set_filter(self, key):
        self._current_filter = key
        self._load_reports()

    def _load_reports(self):
        for w in self._rows:
            w.destroy()
        self._rows.clear()

        try:
            user = self.controller.current_user
            user_id = user.get("id") or user.get("user_id")
            db = self.controller.db

            filter_type = None if self._current_filter == "all" else self._current_filter
            items = db.get_items_by_user(user_id=user_id, item_type=filter_type)
        except Exception as exc:
            print(f"[MyLostFoundFrame] load error: {exc}")
            items = []

        if not items:
            lbl = ctk.CTkLabel(self.table_scroll, text="No reports found.", font=ctk.CTkFont(size=13))
            lbl.grid(row=0, column=0, columnspan=7, padx=10, pady=20)
            self._rows.append(lbl)
            return

        for row_idx, item in enumerate(items):
            item_id = item.get("id") or item.get("item_id")
            cols = [
                str(item_id),
                item.get("item_name", ""),
                item.get("category", ""),
                item.get("location", ""),
                str(item.get("date_reported") or item.get("lost_date") or ""),
                item.get("status", "open").capitalize(),
            ]
            for col_idx, text in enumerate(cols):
                lbl = ctk.CTkLabel(
                    self.table_scroll, text=text, font=ctk.CTkFont(size=11),
                    anchor="w",
                )
                lbl.grid(row=row_idx, column=col_idx, padx=4, pady=3, sticky="w")
                self._rows.append(lbl)

            # Action buttons
            act_frame = ctk.CTkFrame(self.table_scroll, fg_color="transparent")
            act_frame.grid(row=row_idx, column=6, padx=4, pady=2, sticky="w")

            view_btn = ctk.CTkButton(
                act_frame, text="View", width=55,
                command=lambda i=item: self._view_item(i),
            )
            view_btn.pack(side="left", padx=2)

            del_btn = ctk.CTkButton(
                act_frame, text="Delete", width=60,
                command=lambda i=item: self._delete_item(i),
            )
            del_btn.pack(side="left", padx=2)

            self._rows.append(act_frame)

    # -----------------------------------------------------------------------
    # Detail popup
    # -----------------------------------------------------------------------

    def _view_item(self, item):
        popup = ctk.CTkToplevel(self)
        popup.title(f"Item Details – {item.get('item_name', '')}")
        popup.geometry("640x560")
        popup.grab_set()

        popup.grid_columnconfigure(0, weight=1)
        popup.grid_rowconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(popup)
        scroll.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        scroll.grid_columnconfigure((0, 1), weight=1)

        fields = [
            ("ID", item.get("id") or item.get("item_id")),
            ("Type", (item.get("item_type") or "").capitalize()),
            ("Item Name", item.get("item_name", "")),
            ("Category", item.get("category", "")),
            ("Location", item.get("location", "")),
            ("Date", item.get("date_reported") or item.get("lost_date") or ""),
            ("Status", item.get("status", "open").capitalize()),
            ("Contact Email", item.get("contact_email", "")),
            ("Description", item.get("description", "")),
            ("Features", item.get("features") or item.get("distinguishing_features") or ""),
        ]

        for r, (label, value) in enumerate(fields):
            ctk.CTkLabel(scroll, text=f"{label}:", font=ctk.CTkFont(weight="bold"), anchor="w").grid(
                row=r, column=0, sticky="w", padx=10, pady=3)
            ctk.CTkLabel(scroll, text=str(value or ""), anchor="w", wraplength=350).grid(
                row=r, column=1, sticky="w", padx=10, pady=3)

        # Image
        img_file = item.get("image_filename") or item.get("image")
        if img_file:
            try:
                uploads = None
                try:
                    from config import UPLOADS_DIR
                    uploads = UPLOADS_DIR
                except ImportError:
                    pass
                if uploads:
                    img_path = os.path.join(str(uploads), img_file)
                    from PIL import Image, ImageTk
                    img = Image.open(img_path).resize((200, 200))
                    photo = ImageTk.PhotoImage(img)
                    img_lbl = ctk.CTkLabel(scroll, image=photo, text="")
                    img_lbl.grid(row=len(fields), column=0, columnspan=2, pady=10)
                    img_lbl._photo = photo
            except Exception:
                pass

        # QR Code
        try:
            from services.qr_service import qr_service
            item_id = item.get("id") or item.get("item_id")
            qr_img = qr_service.generate_qr(data=f"campusfind://item/{item_id}", size=(150, 150))
            if qr_img:
                qr_lbl = ctk.CTkLabel(scroll, image=qr_img, text="")
                qr_lbl.grid(row=len(fields) + 1, column=0, columnspan=2, pady=6)
                qr_lbl._photo = qr_img
        except Exception:
            pass

        ctk.CTkButton(popup, text="Close", command=popup.destroy).pack(pady=8)

    # -----------------------------------------------------------------------
    # Delete
    # -----------------------------------------------------------------------

    def _delete_item(self, item):
        item_id = item.get("id") or item.get("item_id")
        item_name = item.get("item_name", "this item")
        confirmed = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete '{item_name}'?\nThis action cannot be undone.",
        )
        if not confirmed:
            return
        try:
            db = self.controller.db
            db.delete_item(item_id=item_id)
            messagebox.showinfo("Deleted", f"'{item_name}' has been deleted.")
            self._load_reports()
        except Exception as exc:
            messagebox.showerror("Error", f"Failed to delete item:\n{exc}")

    # -----------------------------------------------------------------------
    # Export PDF
    # -----------------------------------------------------------------------

    def _export_pdf(self):
        try:
            from services.pdf_service import pdf_service
            user = self.controller.current_user
            user_id = user.get("id") or user.get("user_id")
            db = self.controller.db
            filter_type = None if self._current_filter == "all" else self._current_filter
            items = db.get_items_by_user(user_id=user_id, item_type=filter_type)
            path = pdf_service.generate_lost_items_report(items=items, user=user)
            messagebox.showinfo("PDF Exported", f"Report saved to:\n{path}")
        except Exception as exc:
            messagebox.showerror("Export Error", f"Could not export PDF:\n{exc}")

    # -----------------------------------------------------------------------
    # Theme
    # -----------------------------------------------------------------------

    def apply_theme(self, theme):
        self.theme = theme
        try:
            self.configure(fg_color=theme["bg_primary"])
            self.table_scroll.configure(fg_color=theme["bg_card"])
            self.export_btn.configure(
                fg_color=theme["btn_secondary_bg"],
                text_color=theme["btn_secondary_fg"],
                hover_color=theme["accent_hover"],
            )
            for key, btn in self._tab_buttons.items():
                btn.configure(
                    fg_color=theme["accent_primary"] if key == self._current_filter else theme["btn_secondary_bg"],
                    text_color=theme["btn_primary_fg"] if key == self._current_filter else theme["btn_secondary_fg"],
                )
        except Exception as exc:
            print(f"[MyLostFoundFrame] apply_theme error: {exc}")
