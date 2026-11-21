"""
CampusFind - Report Found Item Module
Allows students/staff to register found belongings and immediately triggers the matching engine.
"""

import os
from datetime import datetime
import customtkinter as ctk
from tkinter import filedialog, messagebox

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
from student.matching import matching_engine


class ReportFoundFrame(ctk.CTkFrame):
    """Form to register a found item on campus."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.theme = None
        self._image_path = None
        self._preview_photo = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_ui()

    def _build_ui(self):
        self.scroll = ctk.CTkScrollableFrame(self)
        self.scroll.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.scroll.grid_columnconfigure(0, weight=1)
        self.scroll.grid_columnconfigure(1, weight=1)

        row = 0

        # Title
        title = ctk.CTkLabel(
            self.scroll,
            text="📦  Report Found Belonging",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        title.grid(row=row, column=0, columnspan=2, sticky="w", padx=20, pady=(20, 4))
        row += 1

        subtitle = ctk.CTkLabel(
            self.scroll,
            text="Help return lost items to their rightful owners. Fill in the details accurately.",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray60")
        )
        subtitle.grid(row=row, column=0, columnspan=2, sticky="w", padx=20, pady=(0, 10))
        row += 1

        # Sensitive Items Notice
        notice_frame = ctk.CTkFrame(self.scroll, corner_radius=8, fg_color=("#e8f5e9", "#1b3320"))
        notice_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 14))
        ctk.CTkLabel(
            notice_frame,
            text="🔒 Privacy Notice: For sensitive items like ID cards, wallets, or official documents,\n"
                 "do not post sensitive identification numbers publicly. Keep identifying marks for claim verification.",
            font=ctk.CTkFont(size=11),
            text_color=("#2e7d32", "#81c784"),
            justify="left"
        ).pack(padx=14, pady=8, anchor="w")
        row += 1

        # Item Name
        ctk.CTkLabel(self.scroll, text="Item Name *", font=ctk.CTkFont(weight="bold")).grid(
            row=row, column=0, sticky="w", padx=20, pady=(0, 2))
        row += 1
        self.item_name_entry = ctk.CTkEntry(
            self.scroll, placeholder_text="e.g. Silver Casio Scientific Calculator", height=36)
        self.item_name_entry.grid(row=row, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 10))
        row += 1

        # Category
        ctk.CTkLabel(self.scroll, text="Category *", font=ctk.CTkFont(weight="bold")).grid(
            row=row, column=0, sticky="w", padx=20, pady=(0, 2))
        row += 1
        self.category_var = ctk.StringVar(value=CATEGORIES[0])
        self.category_menu = ctk.CTkOptionMenu(
            self.scroll, variable=self.category_var, values=CATEGORIES, height=36)
        self.category_menu.grid(row=row, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 10))
        row += 1

        # Found Location
        ctk.CTkLabel(self.scroll, text="Found Location *", font=ctk.CTkFont(weight="bold")).grid(
            row=row, column=0, sticky="w", padx=20, pady=(0, 2))
        row += 1
        self.location_var = ctk.StringVar(value=CAMPUS_LOCATIONS[0])
        self.location_menu = ctk.CTkOptionMenu(
            self.scroll, variable=self.location_var, values=CAMPUS_LOCATIONS, height=36)
        self.location_menu.grid(row=row, column=0, sticky="ew", padx=(20, 6), pady=(0, 10))

        self.location_custom = ctk.CTkEntry(
            self.scroll, placeholder_text="Specific spot / Room No. (optional)", height=36)
        self.location_custom.grid(row=row, column=1, sticky="ew", padx=(0, 20), pady=(0, 10))
        row += 1

        # Found Date
        ctk.CTkLabel(self.scroll, text="Found Date * (YYYY-MM-DD)", font=ctk.CTkFont(weight="bold")).grid(
            row=row, column=0, sticky="w", padx=20, pady=(0, 2))
        row += 1
        self.date_entry = ctk.CTkEntry(self.scroll, placeholder_text="YYYY-MM-DD", height=36)
        self.date_entry.grid(row=row, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 10))
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        row += 1

        # Description
        ctk.CTkLabel(self.scroll, text="Detailed Description *", font=ctk.CTkFont(weight="bold")).grid(
            row=row, column=0, sticky="w", padx=20, pady=(0, 2))
        row += 1
        self.description_box = ctk.CTkTextbox(self.scroll, height=90)
        self.description_box.grid(row=row, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 10))
        row += 1

        # Distinguishing Features (Kept for claim verification)
        ctk.CTkLabel(
            self.scroll,
            text="Distinguishing Features (Scratches, Stickers, Brand, Color)",
            font=ctk.CTkFont(weight="bold")
        ).grid(row=row, column=0, sticky="w", padx=20, pady=(0, 2))
        row += 1
        self.features_box = ctk.CTkTextbox(self.scroll, height=70)
        self.features_box.grid(row=row, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 10))
        row += 1

        # Contact Info
        ctk.CTkLabel(self.scroll, text="Finder's Contact Email *", font=ctk.CTkFont(weight="bold")).grid(
            row=row, column=0, sticky="w", padx=20, pady=(0, 2))
        row += 1
        self.email_entry = ctk.CTkEntry(self.scroll, height=36)
        self.email_entry.grid(row=row, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 10))
        row += 1

        # Image Upload
        ctk.CTkLabel(self.scroll, text="Item Photograph (optional)", font=ctk.CTkFont(weight="bold")).grid(
            row=row, column=0, sticky="w", padx=20, pady=(0, 2))
        row += 1

        img_row_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        img_row_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 14))

        self.upload_btn = ctk.CTkButton(
            img_row_frame, text="📷 Upload Photo", width=140, command=self._upload_image)
        self.upload_btn.pack(side="left", padx=(0, 14))

        self.image_preview = ctk.CTkLabel(
            img_row_frame, text="No image selected", width=140, height=140,
            fg_color=("gray90", "gray25"), corner_radius=8
        )
        self.image_preview.pack(side="left")
        row += 1

        # Action Buttons
        btn_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        btn_frame.grid(row=row, column=0, columnspan=2, sticky="e", padx=20, pady=(10, 30))

        ctk.CTkButton(
            btn_frame, text="Cancel", width=110,
            command=lambda: self.controller.show_frame("student_dashboard")
        ).pack(side="left", padx=(0, 10))

        self.submit_btn = ctk.CTkButton(
            btn_frame, text="Submit Found Report", width=170, command=self._submit
        )
        self.submit_btn.pack(side="left")

    def refresh_data(self):
        """Pre-populate finder email if user is logged in."""
        user = getattr(self.controller, 'current_user', None)
        if user and not self.email_entry.get().strip():
            self.email_entry.insert(0, user.get('email', ''))

    def _upload_image(self):
        filetypes = [
            ("Image files", "*.jpg *.jpeg *.png *.webp"),
            ("All files", "*.*")
        ]
        path = filedialog.askopenfilename(title="Select Item Image", filetypes=filetypes)
        if not path:
            return

        valid, err = image_service.validate_image(path)
        if not valid:
            messagebox.showerror("Invalid Image", err)
            return

        self._image_path = path
        thumb = image_service.get_thumbnail(path, size=(140, 140))
        if thumb:
            self._preview_photo = thumb
            self.image_preview.configure(image=thumb, text="")
        else:
            self.image_preview.configure(text=os.path.basename(path))

    def _submit(self):
        user = getattr(self.controller, 'current_user', None)
        if not user:
            messagebox.showerror("Error", "You must be logged in to submit a report.")
            return

        name = self.item_name_entry.get().strip()
        cat = self.category_var.get()
        base_loc = self.location_var.get()
        custom_loc = self.location_custom.get().strip()
        location = f"{base_loc} ({custom_loc})" if custom_loc else base_loc
        date_str = self.date_entry.get().strip()
        desc = self.description_box.get("1.0", "end-1c").strip()
        features = self.features_box.get("1.0", "end-1c").strip()
        contact = self.email_entry.get().strip()

        # Validation
        if not name:
            messagebox.showerror("Validation Error", "Item name is required.")
            return
        if not date_str:
            messagebox.showerror("Validation Error", "Found date is required.")
            return
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Validation Error", "Date must be in YYYY-MM-DD format.")
            return
        if not desc:
            messagebox.showerror("Validation Error", "Description is required.")
            return
        if not contact:
            messagebox.showerror("Validation Error", "Contact email is required.")
            return

        saved_img_path = None
        if self._image_path:
            try:
                saved_img_path = image_service.process_upload(self._image_path)
            except Exception as e:
                messagebox.showwarning("Image Upload Warning", f"Could not process image: {e}")

        try:
            item_id = db.create_item(
                user_id=user['user_id'],
                item_type='found',
                item_name=name,
                category=cat,
                location=location,
                item_date=date_str,
                description=desc,
                distinguishing_features=features,
                image_path=saved_img_path,
                contact_email=contact
            )

            db.log_activity(user['user_id'], 'report_found', f"Reported found item: {name} (ID: #{item_id})")
            db.create_notification(
                user['user_id'],
                "Found Item Registered",
                f"Your found item report for '{name}' (ID: #{item_id}) has been registered.",
                "item_update"
            )

            # Automatic item matching check
            new_matches = matching_engine.run_matching(new_item_id=item_id)
            match_msg = f"\n\n🎯 Automatic Matching: Found {len(new_matches)} potential match(es) with reported lost items!" if new_matches else ""

            messagebox.showinfo(
                "Report Submitted",
                f"Found item '{name}' has been successfully recorded.{match_msg}"
            )

            # Clear form
            self.item_name_entry.delete(0, "end")
            self.location_custom.delete(0, "end")
            self.description_box.delete("1.0", "end")
            self.features_box.delete("1.0", "end")
            self._image_path = None
            self._preview_photo = None
            self.image_preview.configure(image=None, text="No image selected")

            if new_matches:
                self.controller.show_frame("matches")
            else:
                self.controller.show_frame("my_reports")

        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to save report: {e}")

    def apply_theme(self, theme: dict):
        self.theme = theme
        try:
            self.configure(fg_color=theme.get("bg_primary", "transparent"))
            accent = theme.get("accent_primary", "#2d7a2d")
            self.submit_btn.configure(
                fg_color=accent,
                hover_color=theme.get("accent_hover", "#1f5a1f")
            )
        except Exception:
            pass
