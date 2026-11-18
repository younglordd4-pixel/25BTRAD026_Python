import customtkinter as ctk
from tkinter import messagebox
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


class LoginFrame(ctk.CTkFrame):
    """Login screen frame embedded in the main app window."""
    
    def __init__(self, parent, controller):
        super().__init__(parent, corner_radius=0)
        self.controller = controller
        self.configure(fg_color="transparent")
        self._setup_ui()
    
    def _setup_ui(self):
        # Center container
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Card container
        card = ctk.CTkFrame(self, width=440, height=580, corner_radius=16)
        card.grid(row=0, column=0, padx=20, pady=20)
        card.grid_propagate(False)
        card.grid_columnconfigure(0, weight=1)
        
        # Logo / Title
        logo_label = ctk.CTkLabel(card, text="🎓 CampusFind",
                                   font=ctk.CTkFont(size=28, weight="bold"))
        logo_label.grid(row=0, column=0, padx=40, pady=(40, 4))
        
        subtitle = ctk.CTkLabel(card, text="Smart College Lost & Found System",
                                 font=ctk.CTkFont(size=13),
                                 text_color=("gray50", "gray60"))
        subtitle.grid(row=1, column=0, padx=40, pady=(0, 24))
        
        # Email/USN
        ctk.CTkLabel(card, text="Email or USN", anchor="w",
                     font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=2, column=0, padx=40, sticky="ew")
        self.identifier_entry = ctk.CTkEntry(card, placeholder_text="Enter email or USN",
                                              height=40, corner_radius=8)
        self.identifier_entry.grid(row=3, column=0, padx=40, sticky="ew", pady=(4, 12))
        
        # Password
        ctk.CTkLabel(card, text="Password", anchor="w",
                     font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=4, column=0, padx=40, sticky="ew")
        
        pw_frame = ctk.CTkFrame(card, fg_color="transparent")
        pw_frame.grid(row=5, column=0, padx=40, sticky="ew", pady=(4, 4))
        pw_frame.grid_columnconfigure(0, weight=1)
        
        self.password_entry = ctk.CTkEntry(pw_frame, placeholder_text="Enter password",
                                            height=40, corner_radius=8, show="•")
        self.password_entry.grid(row=0, column=0, sticky="ew")
        
        self._show_pw = False
        self.toggle_btn = ctk.CTkButton(pw_frame, text="👁", width=40, height=40,
                                         corner_radius=8, fg_color="transparent",
                                         border_width=1, text_color=("gray50","gray40"),
                                         hover=False, command=self._toggle_password)
        self.toggle_btn.grid(row=0, column=1, padx=(4, 0))
        
        # Remember me
        self.remember_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(card, text="Remember me", variable=self.remember_var,
                        font=ctk.CTkFont(size=12)).grid(
            row=6, column=0, padx=40, sticky="w", pady=(4, 8))
        
        # Error label (hidden initially)
        self.error_label = ctk.CTkLabel(card, text="", text_color="#c62828",
                                         font=ctk.CTkFont(size=12), wraplength=320)
        self.error_label.grid(row=7, column=0, padx=40, sticky="ew")
        
        # Login button
        self.login_btn = ctk.CTkButton(card, text="Login", height=44, corner_radius=8,
                                        font=ctk.CTkFont(size=14, weight="bold"),
                                        command=self._do_login)
        self.login_btn.grid(row=8, column=0, padx=40, sticky="ew", pady=(8, 4))
        
        # Forgot password
        ctk.CTkButton(card, text="Forgot Password?", fg_color="transparent",
                      text_color=("gray50","gray40"), hover=False,
                      font=ctk.CTkFont(size=12), command=self._forgot_password).grid(
            row=9, column=0, padx=40, pady=(4, 8))
        
        # Separator
        ctk.CTkFrame(card, height=1, fg_color=("gray80","gray30")).grid(
            row=10, column=0, padx=40, sticky="ew")
        
        # Register link
        reg_frame = ctk.CTkFrame(card, fg_color="transparent")
        reg_frame.grid(row=11, column=0, padx=40, pady=(8, 30))
        ctk.CTkLabel(reg_frame, text="Don't have an account?",
                     font=ctk.CTkFont(size=12)).pack(side="left")
        ctk.CTkButton(reg_frame, text="Register", fg_color="transparent",
                      font=ctk.CTkFont(size=12, weight="bold"),
                      text_color=("#2d7a2d","#34c759"), hover=False,
                      command=lambda: self.controller.show_frame("registration")).pack(side="left")
        
        # Bind Enter key
        self.identifier_entry.bind("<Return>", lambda e: self._do_login())
        self.password_entry.bind("<Return>", lambda e: self._do_login())
        
        self._card = card
    
    def _toggle_password(self):
        self._show_pw = not self._show_pw
        self.password_entry.configure(show="" if self._show_pw else "•")
    
    def _do_login(self):
        from database import db
        from authentication.security import verify_password
        
        identifier = self.identifier_entry.get().strip()
        password = self.password_entry.get()
        
        if not identifier or not password:
            self._show_error("Please fill in all fields.")
            return
        
        self.login_btn.configure(state="disabled", text="Logging in...")
        self.update()
        
        try:
            # Try email first, then USN
            user = db.get_user_by_email(identifier)
            if not user:
                user = db.get_user_by_usn(identifier)
            
            if not user:
                self._show_error("Invalid credentials. Please try again.")
                return
            
            if not verify_password(password, user['salt'], user['password_hash']):
                self._show_error("Invalid credentials. Please try again.")
                return
            
            # Success
            self._clear_error()
            self.controller.current_user = user
            db.log_activity(user['user_id'], 'login', f'User {user["email"]} logged in')
            
            if user['role'] == 'admin':
                self.controller.show_frame("admin_dashboard")
            else:
                self.controller.show_frame("student_dashboard")
        
        except Exception as e:
            self._show_error(f"Login error: {str(e)}")
        finally:
            self.login_btn.configure(state="normal", text="Login")
    
    def _show_error(self, msg: str):
        self.error_label.configure(text=msg)
    
    def _clear_error(self):
        self.error_label.configure(text="")
    
    def _forgot_password(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Forgot Password")
        dialog.geometry("360x200")
        dialog.grab_set()
        dialog.resizable(False, False)
        
        ctk.CTkLabel(dialog, text="Reset Password",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20, 8))
        ctk.CTkLabel(dialog, text="Enter your registered email address:",
                     font=ctk.CTkFont(size=12)).pack(pady=(0, 8))
        
        email_entry = ctk.CTkEntry(dialog, placeholder_text="Your email", width=280, height=36)
        email_entry.pack(pady=4)
        
        msg_label = ctk.CTkLabel(dialog, text="", text_color="#2d7a2d", font=ctk.CTkFont(size=11))
        msg_label.pack(pady=4)
        
        def send_reset():
            from database import db
            email = email_entry.get().strip()
            if not email:
                msg_label.configure(text="Please enter your email.", text_color="#c62828")
                return
            user = db.get_user_by_email(email)
            # Always show success message (security: don't reveal if email exists)
            msg_label.configure(
                text="If this email is registered, a reset\nlink has been sent to your inbox.",
                text_color="#2d7a2d")
            if user:
                from authentication.security import generate_reset_token
                token = generate_reset_token()
                db.log_activity(user['user_id'], 'password_reset_requested', '')
        
        ctk.CTkButton(dialog, text="Send Reset Link", command=send_reset,
                      height=36, corner_radius=8).pack(pady=8)
    
    def apply_theme(self, theme: dict):
        """Update all widget colors for theme change."""
        self.configure(fg_color=theme.get('bg_primary', 'transparent'))
        try:
            self._card.configure(fg_color=theme.get('bg_card'))
            self.identifier_entry.configure(
                fg_color=theme.get('input_bg'),
                text_color=theme.get('input_fg'),
                border_color=theme.get('input_border'),
                placeholder_text_color=theme.get('input_placeholder'))
            self.password_entry.configure(
                fg_color=theme.get('input_bg'),
                text_color=theme.get('input_fg'),
                border_color=theme.get('input_border'),
                placeholder_text_color=theme.get('input_placeholder'))
            self.login_btn.configure(
                fg_color=theme.get('btn_primary_bg'),
                text_color=theme.get('btn_primary_fg'),
                hover_color=theme.get('accent_hover'))
        except Exception:
            pass
