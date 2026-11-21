"""
CampusFind - Administrator Analytics Module
Data visualization using Matplotlib embedded in CustomTkinter frames with real SQLite statistics.
"""

from datetime import datetime
import customtkinter as ctk
from tkinter import messagebox

from database import db
from services.analytics_service import analytics_service
from services.pdf_service import pdf_service


class AdminAnalyticsFrame(ctk.CTkFrame):
    """Analytics dashboard providing visual graphs for CampusFind operations."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.theme = None
        self._canvases = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_ui()

    def _build_ui(self):
        # 1. Header & Controls
        top_f = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        top_f.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 10))
        top_f.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            top_f, text="📊  Campus Lost & Found Analytics",
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
            btn_box, text="🔄 Reload Charts", width=120, height=34,
            command=self.refresh_data
        )
        self.refresh_btn.pack(side="right")

        # 2. Scrollable container for charts
        self.scroll = ctk.CTkScrollableFrame(self, corner_radius=10)
        self.scroll.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 20))
        self.scroll.grid_columnconfigure(0, weight=1)
        self.scroll.grid_columnconfigure(1, weight=1)

    def refresh_data(self):
        """Re-render all charts with fresh database data."""
        self._load_charts()

    def _load_charts(self):
        # Clear existing canvases
        for c in self._canvases:
            try:
                c.get_tk_widget().destroy()
            except Exception:
                pass
        self._canvases.clear()

        for w in self.scroll.winfo_children():
            w.destroy()

        theme = self.theme or self.controller.theme_manager.get_theme()

        # KPI Summary Cards at top of scroll
        kpi_row = ctk.CTkFrame(self.scroll, corner_radius=10)
        kpi_row.grid(row=0, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 14))
        for i in range(4):
            kpi_row.grid_columnconfigure(i, weight=1)

        analytics_data = db.get_analytics_data()
        counts = db.get_item_counts()
        claims = analytics_data.get('claim_stats', {})
        rec_rate = analytics_data.get('recovery_rate', 0.0)

        kpis = [
            ("Total Lost Items", str(counts.get('total_lost', 0)), "#c62828", "📋"),
            ("Total Found Items", str(counts.get('total_found', 0)), "#2d7a2d", "📦"),
            ("Active Claims", str(claims.get('pending', 0) + claims.get('under_review', 0)), "#f57c00", "⏳"),
            ("Recovery Rate", f"{rec_rate:.1f}%", "#0277bd", "🎯"),
        ]
        for col, (title, val, accent, icon) in enumerate(kpis):
            kf = ctk.CTkFrame(kpi_row, corner_radius=8, fg_color=("gray95", "gray20"))
            kf.grid(row=0, column=col, padx=8, pady=10, sticky="ew")
            ctk.CTkLabel(kf, text=icon, font=ctk.CTkFont(size=22)).pack(anchor="w", padx=12, pady=(8, 0))
            ctk.CTkLabel(kf, text=val, font=ctk.CTkFont(size=24, weight="bold"), text_color=accent).pack(anchor="w", padx=12)
            ctk.CTkLabel(kf, text=title, font=ctk.CTkFont(size=11), text_color="gray").pack(anchor="w", padx=12, pady=(0, 8))

        # Chart 1: Lost vs Found Bar Chart
        c1_frame = ctk.CTkFrame(self.scroll, corner_radius=10)
        c1_frame.grid(row=1, column=0, padx=8, pady=8, sticky="nsew")
        ctk.CTkLabel(c1_frame, text="📊 Monthly Lost vs Found Reports", font=ctk.CTkFont(size=13, weight="bold")).pack(pady=(10, 4))
        try:
            canvas1 = analytics_service.create_lost_vs_found_chart(c1_frame, theme)
            canvas1.get_tk_widget().pack(fill="both", expand=True, padx=6, pady=6)
            self._canvases.append(canvas1)
        except Exception as e:
            ctk.CTkLabel(c1_frame, text=f"Error rendering chart: {e}").pack(pady=20)

        # Chart 2: Monthly Trends Line Chart
        c2_frame = ctk.CTkFrame(self.scroll, corner_radius=10)
        c2_frame.grid(row=1, column=1, padx=8, pady=8, sticky="nsew")
        ctk.CTkLabel(c2_frame, text="📈 Activity Trends Over Time", font=ctk.CTkFont(size=13, weight="bold")).pack(pady=(10, 4))
        try:
            canvas2 = analytics_service.create_monthly_trend_chart(c2_frame, theme)
            canvas2.get_tk_widget().pack(fill="both", expand=True, padx=6, pady=6)
            self._canvases.append(canvas2)
        except Exception as e:
            ctk.CTkLabel(c2_frame, text=f"Error rendering chart: {e}").pack(pady=20)

        # Chart 3: Category Distribution - Lost
        c3_frame = ctk.CTkFrame(self.scroll, corner_radius=10)
        c3_frame.grid(row=2, column=0, padx=8, pady=8, sticky="nsew")
        ctk.CTkLabel(c3_frame, text="🎒 Lost Belongings by Category", font=ctk.CTkFont(size=13, weight="bold")).pack(pady=(10, 4))
        try:
            canvas3 = analytics_service.create_category_chart(c3_frame, theme, item_type='lost')
            canvas3.get_tk_widget().pack(fill="both", expand=True, padx=6, pady=6)
            self._canvases.append(canvas3)
        except Exception as e:
            ctk.CTkLabel(c3_frame, text=f"Error rendering chart: {e}").pack(pady=20)

        # Chart 4: Category Distribution - Found
        c4_frame = ctk.CTkFrame(self.scroll, corner_radius=10)
        c4_frame.grid(row=2, column=1, padx=8, pady=8, sticky="nsew")
        ctk.CTkLabel(c4_frame, text="📦 Found Belongings by Category", font=ctk.CTkFont(size=13, weight="bold")).pack(pady=(10, 4))
        try:
            canvas4 = analytics_service.create_category_chart(c4_frame, theme, item_type='found')
            canvas4.get_tk_widget().pack(fill="both", expand=True, padx=6, pady=6)
            self._canvases.append(canvas4)
        except Exception as e:
            ctk.CTkLabel(c4_frame, text=f"Error rendering chart: {e}").pack(pady=20)

        # Chart 5: Claim Statistics Pie Chart
        c5_frame = ctk.CTkFrame(self.scroll, corner_radius=10)
        c5_frame.grid(row=3, column=0, padx=8, pady=8, sticky="nsew")
        ctk.CTkLabel(c5_frame, text="⚖️ Claim Resolution Distribution", font=ctk.CTkFont(size=13, weight="bold")).pack(pady=(10, 4))
        try:
            canvas5 = analytics_service.create_claim_stats_chart(c5_frame, theme)
            canvas5.get_tk_widget().pack(fill="both", expand=True, padx=6, pady=6)
            self._canvases.append(canvas5)
        except Exception as e:
            ctk.CTkLabel(c5_frame, text=f"Error rendering chart: {e}").pack(pady=20)

        # Chart 6: Reports by Location Horizontal Bar
        c6_frame = ctk.CTkFrame(self.scroll, corner_radius=10)
        c6_frame.grid(row=3, column=1, padx=8, pady=8, sticky="nsew")
        ctk.CTkLabel(c6_frame, text="📍 High-Activity Campus Locations", font=ctk.CTkFont(size=13, weight="bold")).pack(pady=(10, 4))
        try:
            canvas6 = analytics_service.create_location_chart(c6_frame, theme)
            canvas6.get_tk_widget().pack(fill="both", expand=True, padx=6, pady=6)
            self._canvases.append(canvas6)
        except Exception as e:
            ctk.CTkLabel(c6_frame, text=f"Error rendering chart: {e}").pack(pady=20)

    def _export_pdf(self):
        try:
            data = db.get_analytics_data()
            path = pdf_service.generate_analytics_report(data)
            messagebox.showinfo("Export Successful", f"Analytics report exported:\n{path}")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Could not generate PDF: {e}")

    def apply_theme(self, theme: dict):
        self.theme = theme
        try:
            self.configure(fg_color=theme.get("bg_primary", "transparent"))
            accent = theme.get("accent_primary", "#2d7a2d")
            self.export_btn.configure(
                fg_color=accent,
                hover_color=theme.get("accent_hover", "#1f5a1f")
            )
            # Update active chart canvases
            for c in self._canvases:
                analytics_service.update_chart_theme(c, theme)
        except Exception:
            pass
