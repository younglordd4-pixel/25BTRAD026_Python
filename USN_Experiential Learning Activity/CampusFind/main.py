"""
CampusFind - Smart College Lost and Found Management System
Main Application Entry Point and Frame Controller
"""

import os
import sys
from pathlib import Path
import customtkinter as ctk
from tkinter import messagebox

# Ensure application base directory is in sys.path
BASE_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(BASE_DIR))

# Ensure MPLCONFIGDIR is set to a local writable directory to avoid matplotlib cache warnings
os.environ["MPLCONFIGDIR"] = str(BASE_DIR / ".matplotlib_cache")

# Set initial appearance mode
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")

from config import (
    APP_NAME, APP_VERSION, WINDOW_WIDTH, WINDOW_HEIGHT,
    MIN_WIDTH, MIN_HEIGHT, SIDEBAR_WIDTH
)
from theme_manager import theme_manager
from database import db

# Import all screen frames
from authentication.login import LoginFrame
from authentication.registration import RegistrationFrame
from student.dashboard import StudentDashboard
from student.lost_items import ReportLostFrame, MyLostFoundFrame
from student.found_items import ReportFoundFrame
from student.search import SearchFrame
from student.matching import MatchingFrame
from student.claims import ClaimsFrame
from admin.dashboard import AdminDashboard
from admin.users import AdminUsersFrame
from admin.reports import AdminReportsFrame
from admin.claim_review import AdminClaimReviewFrame
from admin.analytics import AdminAnalyticsFrame


class CampusFindApp(ctk.CTk):
    """
    Main application window that serves as the controller for all screen frames.
    Implements dynamic light/dark theming, sidebar navigation, top bar controls,
    and role-based access control.
    """

    def __init__(self):
        super().__init__()

        self.theme_manager = theme_manager
        self.db = db
        self.current_user = None
        self._frames = {}
        self._sidebar_buttons = {}
        self._current_frame_name = None

        # Window settings
        self.title(f"{APP_NAME} – Smart College Lost and Found Management System v{APP_VERSION}")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(MIN_WIDTH, MIN_HEIGHT)

        # Apply saved theme preference
        saved_theme = self.theme_manager.current_theme
        ctk.set_appearance_mode("dark" if saved_theme == "dark" else "light")

        # Build main layout
        self._build_layout()
        self._register_frames()

        # Connect theme callbacks
        self.theme_manager.register_callback(self._on_theme_change)

        # Show initial screen
        self.show_frame("login")

        # Center window on screen
        self.update_idletasks()
        try:
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            x = max(0, (sw - WINDOW_WIDTH) // 2)
            y = max(0, (sh - WINDOW_HEIGHT) // 2)
            self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")
        except Exception:
            pass

    def _build_layout(self):
        """Constructs the sidebar, top navigation bar, and main content area."""
        theme = self.theme_manager.get_theme()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # ── 1. Left Sidebar ──────────────────────────────────────────────────
        self.sidebar = ctk.CTkFrame(
            self, width=SIDEBAR_WIDTH, corner_radius=0,
            fg_color=theme.get('sidebar_bg', '#ffffff')
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_columnconfigure(0, weight=1)
        self.sidebar.grid_rowconfigure(2, weight=1)  # nav items expand
        self.sidebar.grid_rowconfigure(3, weight=0)  # logout button fixed at bottom

        # Sidebar Header: Logo & Title
        logo_box = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=70)
        logo_box.grid(row=0, column=0, sticky="ew", padx=14, pady=(16, 8))
        logo_box.grid_propagate(False)

        ctk.CTkLabel(
            logo_box, text="🎓 CampusFind",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color=theme.get('accent_primary', '#2d7a2d')
        ).pack(anchor="w", padx=4)

        ctk.CTkLabel(
            logo_box, text="Lost & Found System",
            font=ctk.CTkFont(size=11),
            text_color=theme.get('text_muted', '#6b8f6b')
        ).pack(anchor="w", padx=4)

        # Divider
        ctk.CTkFrame(
            self.sidebar, height=1, fg_color=theme.get('separator_color', '#e0f0e0')
        ).grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 8))

        # Nav items container
        self._nav_container = ctk.CTkScrollableFrame(self.sidebar, fg_color="transparent")
        self._nav_container.grid(row=2, column=0, sticky="nsew", padx=4, pady=0)
        self._nav_container.grid_columnconfigure(0, weight=1)

        # Logout button
        self._logout_btn = ctk.CTkButton(
            self.sidebar, text="🚪  Logout", anchor="w",
            fg_color="transparent", text_color=theme.get('error_color', '#c62828'),
            hover_color=theme.get('sidebar_hover', '#e8f5e8'),
            corner_radius=8, height=38,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._do_logout
        )
        self._logout_btn.grid(row=3, column=0, sticky="ew", padx=10, pady=(8, 16))

        # ── 2. Right Workspace (Top Bar + Content) ───────────────────────────
        self.right_workspace = ctk.CTkFrame(self, corner_radius=0, fg_color=theme.get('bg_primary', '#f8fdf8'))
        self.right_workspace.grid(row=0, column=1, sticky="nsew")
        self.right_workspace.grid_rowconfigure(1, weight=1)
        self.right_workspace.grid_columnconfigure(0, weight=1)

        # Top Bar
        self.topbar = ctk.CTkFrame(
            self.right_workspace, height=54, corner_radius=0,
            fg_color=theme.get('topbar_bg', '#ffffff')
        )
        self.topbar.grid(row=0, column=0, sticky="ew")
        self.topbar.grid_propagate(False)
        self.topbar.grid_columnconfigure(0, weight=1)

        self.title_label = ctk.CTkLabel(
            self.topbar, text="CampusFind",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=theme.get('text_primary', '#1a3a1a')
        )
        self.title_label.grid(row=0, column=0, padx=20, sticky="w")

        # Top Bar Controls: Notification, Profile, Theme Switcher
        top_controls = ctk.CTkFrame(self.topbar, fg_color="transparent")
        top_controls.grid(row=0, column=1, padx=14, sticky="e")

        self.notif_btn = ctk.CTkButton(
            top_controls, text="🔔", width=42, height=34,
            fg_color="transparent", text_color=theme.get('text_primary', '#1a3a1a'),
            hover_color=theme.get('sidebar_hover', '#e8f5e8'),
            corner_radius=8, command=self._open_notifications
        )
        self.notif_btn.pack(side="left", padx=3)

        self.profile_btn = ctk.CTkButton(
            top_controls, text="👤 Profile", width=88, height=34,
            fg_color="transparent", text_color=theme.get('text_primary', '#1a3a1a'),
            hover_color=theme.get('sidebar_hover', '#e8f5e8'),
            corner_radius=8, command=self._open_profile
        )
        self.profile_btn.pack(side="left", padx=3)

        is_dark = self.theme_manager.current_theme == "dark"
        self.theme_btn = ctk.CTkButton(
            top_controls, text="☀" if is_dark else "🌙",
            width=42, height=34,
            fg_color=theme.get('accent_primary', '#2d7a2d'),
            hover_color=theme.get('accent_hover', '#1f5a1f'),
            text_color="white", corner_radius=8,
            command=self._toggle_theme
        )
        self.theme_btn.pack(side="left", padx=3)

        # Topbar bottom divider
        ctk.CTkFrame(
            self.right_workspace, height=1,
            fg_color=theme.get('separator_color', '#e0f0e0')
        ).grid(row=0, column=0, sticky="sew")

        # Main Content Frame
        self.content_container = ctk.CTkFrame(
            self.right_workspace, corner_radius=0,
            fg_color=theme.get('bg_primary', '#f8fdf8')
        )
        self.content_container.grid(row=1, column=0, sticky="nsew")
        self.content_container.grid_rowconfigure(0, weight=1)
        self.content_container.grid_columnconfigure(0, weight=1)

    def _register_frames(self):
        """Instantiates all frames and hides them in the content container."""
        frame_specs = {
            "login": LoginFrame,
            "registration": RegistrationFrame,
            "student_dashboard": StudentDashboard,
            "report_lost": ReportLostFrame,
            "report_found": ReportFoundFrame,
            "my_reports": MyLostFoundFrame,
            "search": SearchFrame,
            "matches": MatchingFrame,
            "my_claims": ClaimsFrame,
            "admin_dashboard": AdminDashboard,
            "admin_users": AdminUsersFrame,
            "admin_reports": AdminReportsFrame,
            "admin_claims": AdminClaimReviewFrame,
            "admin_analytics": AdminAnalyticsFrame,
        }

        for name, frame_cls in frame_specs.items():
            frame = frame_cls(self.content_container, self)
            frame.grid(row=0, column=0, sticky="nsew")
            frame.grid_remove()
            self._frames[name] = frame
            if hasattr(frame, 'apply_theme'):
                self.theme_manager.register_callback(frame.apply_theme)

    def show_frame(self, name: str):
        """
        Switches the visible screen frame and configures sidebar/topbar visibility.
        Enforces role-based security: students cannot access admin screens.
        """
        # Role-based authorization check
        if name.startswith("admin_"):
            if not self.current_user or self.current_user.get('role') != 'admin':
                messagebox.showerror(
                    "Access Denied",
                    "Administrative privileges are required to access this section."
                )
                if self.current_user:
                    self.show_frame("student_dashboard")
                else:
                    self.show_frame("login")
                return

        # Hide current frame
        for f in self._frames.values():
            f.grid_remove()

        # Display target frame
        if name in self._frames:
            target = self._frames[name]
            target.grid()
            if hasattr(target, 'refresh_data'):
                try:
                    target.refresh_data()
                except Exception as e:
                    print(f"Error refreshing frame {name}: {e}")

        # Update topbar title
        titles = {
            "login": "Login to CampusFind",
            "registration": "Create a New Student Account",
            "student_dashboard": "Student Dashboard",
            "report_lost": "Report a Lost Belonging",
            "report_found": "Report a Found Belonging",
            "my_reports": "My Reported Items",
            "search": "Search & Browse Items",
            "matches": "Automatic Item Matches",
            "my_claims": "My Ownership Claims",
            "admin_dashboard": "Administrator Dashboard",
            "admin_users": "Student Account Management",
            "admin_reports": "All Campus Item Reports",
            "admin_claims": "Claim Adjudication & Review",
            "admin_analytics": "Campus Analytics & Reports",
        }
        self.title_label.configure(text=titles.get(name, name.replace("_", " ").title()))

        # Determine whether this is an authentication screen or internal workspace
        is_auth = name in ("login", "registration")
        if is_auth:
            self.sidebar.grid_remove()
            self.notif_btn.pack_forget()
            self.profile_btn.pack_forget()
        else:
            self.sidebar.grid()
            self.notif_btn.pack(side="left", padx=3)
            self.profile_btn.pack(side="left", padx=3)

            # Rebuild sidebar nav if role has changed or buttons not built
            if self.current_user:
                role = self.current_user.get('role', 'student')
                if not self._sidebar_buttons or getattr(self, '_active_nav_role', None) != role:
                    self._build_sidebar_nav(role)
                self._highlight_sidebar(name)
                self._update_notification_badge()

        self._current_frame_name = name

    def _build_sidebar_nav(self, role: str):
        """Populates the sidebar navigation with appropriate links for the user's role."""
        for w in self._nav_container.winfo_children():
            w.destroy()
        self._sidebar_buttons.clear()
        self._active_nav_role = role

        theme = self.theme_manager.get_theme()

        if role == 'admin':
            nav_items = [
                ("🏠  Dashboard", "admin_dashboard"),
                ("👥  Students", "admin_users"),
                ("📋  All Reports", "admin_reports"),
                ("⚖️  Review Claims", "admin_claims"),
                ("📊  Analytics", "admin_analytics"),
                ("🔍  Search Items", "search"),
                ("📦  Report Found", "report_found"),
            ]
        else:
            nav_items = [
                ("🏠  Dashboard", "student_dashboard"),
                ("📋  Report Lost", "report_lost"),
                ("📦  Report Found", "report_found"),
                ("🔍  Search Items", "search"),
                ("🔗  Matches", "matches"),
                ("📄  My Reports", "my_reports"),
                ("📝  My Claims", "my_claims"),
            ]

        for i, (label, target_name) in enumerate(nav_items):
            btn = ctk.CTkButton(
                self._nav_container, text=label, anchor="w",
                fg_color="transparent",
                text_color=theme.get('text_sidebar', '#2d5a2d'),
                hover_color=theme.get('sidebar_hover', '#e8f5e8'),
                corner_radius=8, height=38,
                font=ctk.CTkFont(size=12, weight="bold"),
                command=lambda fn=target_name: self.show_frame(fn)
            )
            btn.grid(row=i, column=0, sticky="ew", padx=4, pady=2)
            self._sidebar_buttons[target_name] = btn

    def _highlight_sidebar(self, active_frame_name: str):
        """Highlights the active navigation button in the sidebar."""
        theme = self.theme_manager.get_theme()
        for fn, btn in self._sidebar_buttons.items():
            if fn == active_frame_name:
                btn.configure(
                    fg_color=theme.get('sidebar_active', '#d4edd4'),
                    text_color=theme.get('text_sidebar_active', '#1a3a1a')
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=theme.get('text_sidebar', '#2d5a2d')
                )

    def _update_notification_badge(self):
        """Updates unread count on the topbar notification bell."""
        if self.current_user:
            try:
                unread = self.db.get_unread_count(self.current_user['user_id'])
                if unread > 0:
                    self.notif_btn.configure(text=f"🔔 {unread}")
                else:
                    self.notif_btn.configure(text="🔔")
            except Exception:
                pass

    def _open_notifications(self):
        """Opens modal popup to view and dismiss student notifications."""
        if not self.current_user:
            return

        dlg = ctk.CTkToplevel(self)
        dlg.title("Notifications – CampusFind")
        dlg.geometry("420x520")
        dlg.grab_set()

        top_f = ctk.CTkFrame(dlg, corner_radius=0)
        top_f.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(
            top_f, text="🔔  Your Notifications",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left")

        def mark_all():
            self.db.mark_all_read(self.current_user['user_id'])
            self._update_notification_badge()
            dlg.destroy()
            self._open_notifications()

        ctk.CTkButton(
            top_f, text="Mark All Read", width=100, height=28,
            command=mark_all
        ).pack(side="right")

        scroll = ctk.CTkScrollableFrame(dlg)
        scroll.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        notifs = self.db.get_notifications(self.current_user['user_id'], limit=30)
        if not notifs:
            ctk.CTkLabel(
                scroll, text="No notifications yet.",
                font=ctk.CTkFont(size=13), text_color="gray"
            ).pack(pady=40)
        else:
            for n in notifs:
                is_unread = n.get('is_read') == 0
                bg_col = ("#e8f5e9", "#1e3325") if is_unread else ("gray95", "gray20")

                item_card = ctk.CTkFrame(scroll, corner_radius=8, fg_color=bg_col)
                item_card.pack(fill="x", pady=4, padx=2)

                ctk.CTkLabel(
                    item_card, text=n.get('title', 'Notification'),
                    font=ctk.CTkFont(size=12, weight="bold"), anchor="w"
                ).pack(anchor="w", padx=10, pady=(8, 2))

                ctk.CTkLabel(
                    item_card, text=n.get('message', ''),
                    font=ctk.CTkFont(size=11), anchor="w", wraplength=340, justify="left"
                ).pack(anchor="w", padx=10, pady=(0, 4))

                ctk.CTkLabel(
                    item_card, text=str(n.get('created_at', ''))[:16],
                    font=ctk.CTkFont(size=9), text_color="gray", anchor="w"
                ).pack(anchor="w", padx=10, pady=(0, 6))

                # Mark individual notification read
                if is_unread:
                    self.db.mark_notification_read(n['notification_id'])

        self._update_notification_badge()

    def _open_profile(self):
        """Displays user profile modal."""
        if not self.current_user:
            return

        u = self.current_user
        dlg = ctk.CTkToplevel(self)
        dlg.title("My Profile – CampusFind")
        dlg.geometry("380x440")
        dlg.grab_set()

        ctk.CTkLabel(
            dlg, text="👤  User Profile",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(20, 8), padx=20, anchor="w")

        info_box = ctk.CTkFrame(dlg, corner_radius=10)
        info_box.pack(fill="x", padx=20, pady=8)

        fields = [
            ("Full Name", u.get('full_name', '-')),
            ("University USN", u.get('usn', '-')),
            ("Department", u.get('department', '-')),
            ("Email Address", u.get('email', '-')),
            ("Account Role", u.get('role', '-').upper()),
            ("Member Since", str(u.get('created_at', '-'))[:10]),
        ]
        for i, (label, val) in enumerate(fields):
            ctk.CTkLabel(info_box, text=f"{label}:", font=ctk.CTkFont(size=11, weight="bold"), anchor="w").grid(row=i, column=0, padx=14, pady=6, sticky="w")
            ctk.CTkLabel(info_box, text=str(val), font=ctk.CTkFont(size=11), anchor="w").grid(row=i, column=1, padx=8, pady=6, sticky="w")

        ctk.CTkButton(dlg, text="Close", width=100, command=dlg.destroy).pack(pady=20)

    def _toggle_theme(self):
        """Switches between Light and Dark themes dynamically."""
        self.theme_manager.toggle_theme()

    def _on_theme_change(self, theme: dict):
        """Theme callback triggered by ThemeManager on theme toggle."""
        is_dark = self.theme_manager.current_theme == "dark"
        ctk.set_appearance_mode("dark" if is_dark else "light")

        self.theme_btn.configure(
            text="☀" if is_dark else "🌙",
            fg_color=theme.get('accent_primary', '#2d7a2d'),
            hover_color=theme.get('accent_hover', '#1f5a1f')
        )

        self.sidebar.configure(fg_color=theme.get('sidebar_bg', '#ffffff'))
        self.right_workspace.configure(fg_color=theme.get('bg_primary', '#f8fdf8'))
        self.topbar.configure(fg_color=theme.get('topbar_bg', '#ffffff'))
        self.content_container.configure(fg_color=theme.get('bg_primary', '#f8fdf8'))
        self.title_label.configure(text_color=theme.get('text_primary', '#1a3a1a'))
        self.notif_btn.configure(
            text_color=theme.get('text_primary', '#1a3a1a'),
            hover_color=theme.get('sidebar_hover', '#e8f5e8')
        )
        self.profile_btn.configure(
            text_color=theme.get('text_primary', '#1a3a1a'),
            hover_color=theme.get('sidebar_hover', '#e8f5e8')
        )
        self._logout_btn.configure(
            text_color=theme.get('error_color', '#c62828'),
            hover_color=theme.get('sidebar_hover', '#e8f5e8')
        )

        # Refresh sidebar styles
        if self.current_user:
            self._highlight_sidebar(self._current_frame_name)
            self.db.update_theme(self.current_user['user_id'], self.theme_manager.current_theme)

    def _do_logout(self):
        """Handles user logout after confirmation."""
        if messagebox.askyesno("Logout Confirmation", "Are you sure you want to log out of CampusFind?"):
            if self.current_user:
                self.db.log_activity(self.current_user['user_id'], 'logout', "User logged out")
            self.current_user = None
            self._sidebar_buttons.clear()
            self.show_frame("login")


def main():
    """Initializes and runs CampusFind desktop application."""
    app = CampusFindApp()
    app.mainloop()


if __name__ == "__main__":
    main()
