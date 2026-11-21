"""
CampusFind - Analytics Service
Visual chart generation using Matplotlib.
Separates pure Figure generation (compatible with headless Agg backend)
from GUI canvas rendering (using FigureCanvasTkAgg).
"""

import sys
from pathlib import Path
from typing import Optional, Tuple, Any

# Ensure project root is in path
BASE_DIR = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(BASE_DIR))

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.figure import Figure


class AnalyticsService:
    """Generates analytics figures and embeds them into CustomTkinter frames."""

    def _apply_theme(self, fig: Figure, ax_list: Any, theme: dict) -> None:
        """Applies light or dark theme palette to a Matplotlib Figure and its Axes."""
        bg = theme.get('chart_bg', '#ffffff')
        text_color = theme.get('chart_text', '#1a3a1a')
        grid_color = theme.get('chart_grid', '#e8f5e8')

        fig.patch.set_facecolor(bg)
        axes = ax_list if isinstance(ax_list, (list, tuple)) else [ax_list]
        for ax in axes:
            ax.set_facecolor(bg)
            ax.tick_params(colors=text_color, labelsize=8)
            ax.xaxis.label.set_color(text_color)
            ax.yaxis.label.set_color(text_color)
            ax.title.set_color(text_color)
            for spine in ax.spines.values():
                spine.set_edgecolor(grid_color)
            ax.grid(True, color=grid_color, alpha=0.5, linewidth=0.5)

    # ------------------------------------------------------------------ #
    # Pure Figure Builders (Backend-Agnostic, Safe for Headless / Agg)    #
    # ------------------------------------------------------------------ #

    def build_lost_vs_found_figure(self, theme_dict: dict, data: Optional[dict] = None) -> Figure:
        """Builds Monthly Lost vs Found bar chart Figure."""
        if data is None:
            from database import db
            data = db.get_analytics_data()

        fig, ax = plt.subplots(figsize=(5, 3.5), tight_layout=True)
        accent = theme_dict.get('accent_primary', '#2d7a2d')
        info = theme_dict.get('info_color', '#0277bd')

        monthly_lost = data.get('monthly_lost', [])
        monthly_found = data.get('monthly_found', [])

        # Collect unique sorted months
        month_set = sorted(list(set([m[0] for m in monthly_lost] + [m[0] for m in monthly_found])))
        lost_map = dict(monthly_lost)
        found_map = dict(monthly_found)

        lost_counts = [lost_map.get(m, 0) for m in month_set]
        found_counts = [found_map.get(m, 0) for m in month_set]

        if month_set:
            x = range(len(month_set))
            ax.bar([i - 0.2 for i in x], lost_counts, 0.4, label='Lost', color=accent, alpha=0.85)
            ax.bar([i + 0.2 for i in x], found_counts, 0.4, label='Found', color=info, alpha=0.85)
            ax.set_xticks(list(x))
            ax.set_xticklabels(month_set, rotation=45, ha='right', fontsize=7)
            ax.legend(fontsize=8)
        else:
            ax.text(0.5, 0.5, 'No monthly data yet', ha='center', va='center', transform=ax.transAxes)

        ax.set_title('Lost vs Found Items (Monthly)', fontsize=10, fontweight='bold')
        ax.set_ylabel('Count', fontsize=8)

        self._apply_theme(fig, ax, theme_dict)
        return fig

    def build_category_figure(self, theme_dict: dict, item_type: str = 'lost', data: Optional[dict] = None) -> Figure:
        """Builds category distribution pie/bar chart Figure."""
        if data is None:
            from database import db
            data = db.get_analytics_data()

        key = f'by_category_{item_type}'
        cats = data.get(key, [])

        fig, ax = plt.subplots(figsize=(5, 3.5), tight_layout=True)
        if cats:
            labels = [c[0] for c in cats]
            values = [c[1] for c in cats]
            colors_list = ['#2d7a2d', '#4CAF50', '#81C784', '#A5D6A7', '#C8E6C9', '#E8F5E9', '#F1F8E9']
            ax.pie(values, labels=labels, colors=colors_list[:len(labels)], autopct='%1.0f%%',
                   textprops={'fontsize': 8}, startangle=140)
        else:
            ax.text(0.5, 0.5, 'No category data yet', ha='center', va='center', transform=ax.transAxes)

        ax.set_title(f'{item_type.title()} Items by Category', fontsize=10, fontweight='bold')
        self._apply_theme(fig, ax, theme_dict)
        return fig

    def build_monthly_trend_figure(self, theme_dict: dict, data: Optional[dict] = None) -> Figure:
        """Builds line chart Figure of monthly trends."""
        if data is None:
            from database import db
            data = db.get_analytics_data()

        fig, ax = plt.subplots(figsize=(5, 3.5), tight_layout=True)
        monthly_lost = data.get('monthly_lost', [])
        monthly_found = data.get('monthly_found', [])

        month_set = sorted(list(set([m[0] for m in monthly_lost] + [m[0] for m in monthly_found])))
        lost_map = dict(monthly_lost)
        found_map = dict(monthly_found)

        lost_counts = [lost_map.get(m, 0) for m in month_set]
        found_counts = [found_map.get(m, 0) for m in month_set]

        accent = theme_dict.get('accent_primary', '#2d7a2d')
        info = theme_dict.get('info_color', '#0277bd')

        if month_set:
            ax.plot(month_set, lost_counts, marker='o', label='Lost', color=accent, linewidth=2, markersize=5)
            ax.plot(month_set, found_counts, marker='s', label='Found', color=info, linewidth=2, markersize=5)
            ax.set_xticks(range(len(month_set)))
            ax.set_xticklabels(month_set, rotation=45, ha='right', fontsize=7)
            ax.legend(fontsize=8)
        else:
            ax.text(0.5, 0.5, 'No trend data yet', ha='center', va='center', transform=ax.transAxes)

        ax.set_title('Monthly Trends', fontsize=10, fontweight='bold')
        ax.set_ylabel('Count', fontsize=8)

        self._apply_theme(fig, ax, theme_dict)
        return fig

    def build_claim_stats_figure(self, theme_dict: dict, data: Optional[dict] = None) -> Figure:
        """Builds pie chart Figure of claim resolution statistics."""
        if data is None:
            from database import db
            data = db.get_analytics_data()

        stats = data.get('claim_stats', {})
        fig, ax = plt.subplots(figsize=(4, 3.5), tight_layout=True)

        labels = [k.replace('_', ' ').title() for k in stats.keys()]
        values = list(stats.values())
        colors_list = ['#FFC107', '#2196F3', '#4CAF50', '#f44336', '#9C27B0']

        if any(v > 0 for v in values):
            ax.pie(values, labels=labels, colors=colors_list[:len(labels)], autopct='%1.0f%%',
                   textprops={'fontsize': 8}, startangle=90)
        else:
            ax.text(0.5, 0.5, 'No claims yet', ha='center', va='center', transform=ax.transAxes)

        ax.set_title('Claim Statistics', fontsize=10, fontweight='bold')
        self._apply_theme(fig, ax, theme_dict)
        return fig

    def build_location_figure(self, theme_dict: dict, data: Optional[dict] = None) -> Figure:
        """Builds horizontal bar chart Figure of report frequency by campus location."""
        if data is None:
            from database import db
            data = db.get_analytics_data()

        locations = data.get('by_location', [])
        fig, ax = plt.subplots(figsize=(5, 3.5), tight_layout=True)
        accent = theme_dict.get('accent_primary', '#2d7a2d')

        if locations:
            locs = [l[0][:15] for l in locations[:8]]
            counts = [l[1] for l in locations[:8]]
            y_pos = range(len(locs))
            ax.barh(list(y_pos), counts, color=accent, alpha=0.85)
            ax.set_yticks(list(y_pos))
            ax.set_yticklabels(locs, fontsize=8)
            ax.set_xlabel('Count', fontsize=8)
        else:
            ax.text(0.5, 0.5, 'No location data', ha='center', va='center', transform=ax.transAxes)

        ax.set_title('Reports by Location', fontsize=10, fontweight='bold')
        self._apply_theme(fig, ax, theme_dict)
        return fig

    # ------------------------------------------------------------------ #
    # GUI Rendering Helpers (Lazily loads TkAgg Canvas for Desktop App)   #
    # ------------------------------------------------------------------ #

    def _embed_in_canvas(self, fig: Figure, parent_frame: Any):
        """Lazily imports FigureCanvasTkAgg and embeds Figure into parent frame."""
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        canvas = FigureCanvasTkAgg(fig, master=parent_frame)
        canvas.draw()
        return canvas

    def create_lost_vs_found_chart(self, parent_frame: Any, theme_dict: dict):
        fig = self.build_lost_vs_found_figure(theme_dict)
        return self._embed_in_canvas(fig, parent_frame)

    def create_category_chart(self, parent_frame: Any, theme_dict: dict, item_type: str = 'lost'):
        fig = self.build_category_figure(theme_dict, item_type=item_type)
        return self._embed_in_canvas(fig, parent_frame)

    def create_monthly_trend_chart(self, parent_frame: Any, theme_dict: dict):
        fig = self.build_monthly_trend_figure(theme_dict)
        return self._embed_in_canvas(fig, parent_frame)

    def create_claim_stats_chart(self, parent_frame: Any, theme_dict: dict):
        fig = self.build_claim_stats_figure(theme_dict)
        return self._embed_in_canvas(fig, parent_frame)

    def create_location_chart(self, parent_frame: Any, theme_dict: dict):
        fig = self.build_location_figure(theme_dict)
        return self._embed_in_canvas(fig, parent_frame)

    def update_chart_theme(self, canvas: Any, theme_dict: dict) -> None:
        """Dynamically redraws embedded Figure with new theme palette."""
        fig = canvas.figure
        for ax in fig.get_axes():
            self._apply_theme(fig, ax, theme_dict)
        canvas.draw()


analytics_service = AnalyticsService()
