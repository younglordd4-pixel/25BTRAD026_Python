import customtkinter as ctk
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


class RegistrationFrame(ctk.CTkFrame):
    """Registration screen frame."""
    
    def __init__(self, parent, controller):
        super().__init__(parent, corner_radius=0)
        self.controller = controller
        self.configure(fg_color="transparent")
        self._setup_ui()
    
    def _setup_ui(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Scrollable container
        scroll = ctk.CTkScrollableFrame(self, corner_radius=0, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)
        
        # Card
        card = ctk.CTkFrame(scroll, width=480, corner_radius=16)
        card.grid(row=0, column=0, padx=20, pady=20)
        card.grid_columnconfigure(0, weight=1)
        
        # Title
        ctk.CTkLabel(card, text="🎓 CampusFind",
                     font=ctk.CTkFont(size=26, weight="bold")).grid(
            row=0, column=0, padx=40, pady=(36, 4))
        ctk.CTkLabel(card, text="Create a New Account",
                     font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=1, column=0, padx=40, pady=(0, 20))
        
        # Full name
        ctk.CTkLabel(card, text="Full Name *", anchor="w",
                     font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=2, column=0, padx=40, sticky="ew")
        self.name_entry = ctk.CTkEntry(card, placeholder_text="Your full name",
                                        height=38, corner_radius=8)
        self.name_entry.grid(row=3, column=0, padx=40, sticky="ew", pady=(4, 10))
        
        # USN
        ctk.CTkLabel(card, text="USN (University Serial Number) *", anchor="w",
                     font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=4, column=0, padx=40, sticky="ew")
        self.usn_entry = ctk.CTkEntry(card, placeholder_text="e.g. 1AB22CS001",
                                       height=38, corner_radius=8)
        self.usn_entry.grid(row=5, column=0, padx=40, sticky="ew", pady=(4, 10))
        
        # Department
        ctk.CTkLabel(card, text="Department *", anchor="w",
                     font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=6, column=0, padx=40, sticky="ew")
        self.dept_var = ctk.StringVar(value="Computer Science")
        self.dept_menu = ctk.CTkOptionMenu(card, values=[
            "Computer Science", "Electronics & Communication", "Mechanical",
            "Civil Engineering", "Information Science", "MBA", "Other"],
            variable=self.dept_var, height=38, corner_radius=8)
        self.dept_menu.grid(row=7, column=0, padx=40, sticky="ew", pady=(4, 10))
        
        # Email
        ctk.CTkLabel(card, text="Email Address *", anchor="w",
                     font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=8, column=0, padx=40, sticky="ew")
        self.email_entry = ctk.CTkEntry(card, placeholder_text="student@college.edu",
                                         height=38, corner_radius=8)
        self.email_entry.grid(row=9, column=0, padx=40, sticky="ew", pady=(4, 10))
        
        # Password
        ctk.CTkLabel(card, text="Password *", anchor="w",
                     font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=10, column=0, padx=40, sticky="ew")
        pw1_frame = ctk.CTkFrame(card, fg_color="transparent")
        pw1_frame.grid(row=11, column=0, padx=40, sticky="ew", pady=(4, 4))
        pw1_frame.grid_columnconfigure(0, weight=1)
        self.pw_entry = ctk.CTkEntry(pw1_frame, placeholder_text="Min 8 chars, upper, lower, digit",
                                      height=38, corner_radius=8, show="•")
        self.pw_entry.grid(row=0, column=0, sticky="ew")
        self._show_pw1 = False
        self.pw1_toggle = ctk.CTkButton(pw1_frame, text="👁", width=38, height=38,
                                         corner_radius=8, fg_color="transparent",
                                         border_width=1, text_color=("gray50","gray40"),
                                         hover=False,
                                         command=lambda: self._toggle_pw('1'))
        self.pw1_toggle.grid(row=0, column=1, padx=(4, 0))
        
        ctk.CTkLabel(card, text="Confirm Password *", anchor="w",
                     font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=12, column=0, padx=40, sticky="ew")
        pw2_frame = ctk.CTkFrame(card, fg_color="transparent")
        pw2_frame.grid(row=13, column=0, padx=40, sticky="ew", pady=(4, 10))
        pw2_frame.grid_columnconfigure(0, weight=1)
        self.pw_confirm_entry = ctk.CTkEntry(pw2_frame, placeholder_text="Repeat password",
                                              height=38, corner_radius=8, show="•")
        self.pw_confirm_entry.grid(row=0, column=0, sticky="ew")
        self._show_pw2 = False
        self.pw2_toggle = ctk.CTkButton(pw2_frame, text="👁", width=38, height=38,
                                         corner_radius=8, fg_color="transparent",
                                         border_width=1, text_color=("gray50","gray40"),
                                         hover=False,
                                         command=lambda: self._toggle_pw('2'))
        self.pw2_toggle.grid(row=0, column=1, padx=(4, 0))
        
        # Terms
        self.terms_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(card, text="I agree to the Terms of Use and Privacy Policy",
                        variable=self.terms_var,
                        font=ctk.CTkFont(size=12)).grid(
            row=14, column=0, padx=40, sticky="w", pady=(4, 8))
        
        # Error / success labels
        self.error_label = ctk.CTkLabel(card, text="", text_color="#c62828",
                                         font=ctk.CTkFont(size=12), wraplength=380)
        self.error_label.grid(row=15, column=0, padx=40, sticky="ew")
        
        self.success_label = ctk.CTkLabel(card, text="", text_color="#2d7a2d",
                                           font=ctk.CTkFont(size=12), wraplength=380)
        self.success_label.grid(row=16, column=0, padx=40, sticky="ew")
        
        # Register button
        self.register_btn = ctk.CTkButton(card, text="Create Account", height=44,
                                           corner_radius=8,
                                           font=ctk.CTkFont(size=14, weight="bold"),
                                           command=self._do_register)
        self.register_btn.grid(row=17, column=0, padx=40, sticky="ew", pady=(8, 8))
        
        # Login link
        ctk.CTkFrame(card, height=1, fg_color=("gray80","gray30")).grid(
            row=18, column=0, padx=40, sticky="ew")
        login_frame = ctk.CTkFrame(card, fg_color="transparent")
        login_frame.grid(row=19, column=0, padx=40, pady=(8, 30))
        ctk.CTkLabel(login_frame, text="Already have an account?",
                     font=ctk.CTkFont(size=12)).pack(side="left")
        ctk.CTkButton(login_frame, text="Login", fg_color="transparent",
                      font=ctk.CTkFont(size=12, weight="bold"),
                      text_color=("#2d7a2d","#34c759"), hover=False,
                      command=lambda: self.controller.show_frame("login")).pack(side="left")
        
        self._card = card
    
    def _toggle_pw(self, which):
        if which == '1':
            self._show_pw1 = not self._show_pw1
            self.pw_entry.configure(show="" if self._show_pw1 else "•")
        else:
            self._show_pw2 = not self._show_pw2
            self.pw_confirm_entry.configure(show="" if self._show_pw2 else "•")
    
    def _do_register(self):
        from database import db
        from authentication.security import (validate_email, validate_password,
                                              validate_usn, hash_password, generate_salt)
        
        name = self.name_entry.get().strip()
        usn = self.usn_entry.get().strip().upper()
        dept = self.dept_var.get()
        email = self.email_entry.get().strip().lower()
        pw = self.pw_entry.get()
        pw_confirm = self.pw_confirm_entry.get()
        terms = self.terms_var.get()
        
        # Validation
        if not all([name, usn, dept, email, pw, pw_confirm]):
            self._show_error("All fields are required.")
            return
        if len(name) < 3:
            self._show_error("Full name must be at least 3 characters.")
            return
        if not validate_usn(usn):
            self._show_error("USN must be at least 5 alphanumeric characters.")
            return
        if not validate_email(email):
            self._show_error("Please enter a valid email address.")
            return
        valid, msg = validate_password(pw)
        if not valid:
            self._show_error(msg)
            return
        if pw != pw_confirm:
            self._show_error("Passwords do not match.")
            return
        if not terms:
            self._show_error("You must agree to the Terms of Use.")
            return
        
        # Check duplicates
        if db.get_user_by_email(email):
            self._show_error("This email is already registered.")
            return
        if db.get_user_by_usn(usn):
            self._show_error("This USN is already registered.")
            return
        
        # Create user
        self.register_btn.configure(state="disabled", text="Creating account...")
        self.update()
        
        try:
            salt = generate_salt()
            pw_hash = hash_password(pw, salt)
            user_id = db.create_user(name, usn, dept, email, pw_hash, salt, role='student')
            
            if user_id:
                db.create_notification(user_id, "Welcome to CampusFind!",
                    f"Hi {name}, welcome! You can now report lost/found items and search for matches.",
                    "info")
                db.log_activity(user_id, 'registration', f'New student registered: {email}')
                
                self._clear_error()
                self.success_label.configure(
                    text="✅ Account created successfully! Redirecting to login...")
                self.after(2000, lambda: self.controller.show_frame("login"))
            else:
                self._show_error("Registration failed. Please try again.")
        
        except Exception as e:
            self._show_error(f"Registration error: {str(e)}")
        finally:
            self.register_btn.configure(state="normal", text="Create Account")
    
    def _show_error(self, msg):
        self.error_label.configure(text=f"⚠ {msg}")
        self.success_label.configure(text="")
    
    def _clear_error(self):
        self.error_label.configure(text="")
    
    def apply_theme(self, theme: dict):
        try:
            self.configure(fg_color=theme.get('bg_primary', 'transparent'))
            self._card.configure(fg_color=theme.get('bg_card'))
            for entry in [self.name_entry, self.usn_entry, self.email_entry,
                          self.pw_entry, self.pw_confirm_entry]:
                entry.configure(
                    fg_color=theme.get('input_bg'),
                    text_color=theme.get('input_fg'),
                    border_color=theme.get('input_border'),
                    placeholder_text_color=theme.get('input_placeholder'))
            self.register_btn.configure(
                fg_color=theme.get('btn_primary_bg'),
                text_color=theme.get('btn_primary_fg'),
                hover_color=theme.get('accent_hover'))
            self.dept_menu.configure(
                fg_color=theme.get('input_bg'),
                text_color=theme.get('input_fg'),
                button_color=theme.get('accent_primary'),
                dropdown_fg_color=theme.get('bg_card'))
        except Exception:
            pass
