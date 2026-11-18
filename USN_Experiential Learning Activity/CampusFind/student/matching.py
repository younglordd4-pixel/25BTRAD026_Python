"""
CampusFind - Automatic Item Matching System
Compares lost items against found items using a weighted multi-factor scoring model.
"""

import re
import difflib
from datetime import datetime
import customtkinter as ctk
from tkinter import messagebox
from PIL import Image

try:
    from config import MATCH_THRESHOLD, BASE_DIR
except ImportError:
    MATCH_THRESHOLD = 60
    BASE_DIR = None

from database import db
from services.image_service import image_service


# ---------------------------------------------------------------------------
# Stopwords for keyword matching
# ---------------------------------------------------------------------------
STOPWORDS = {
    "a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "of", "with",
    "by", "from", "up", "about", "into", "over", "after", "is", "was", "are",
    "were", "it", "this", "that", "these", "those", "i", "me", "my", "lost",
    "found", "item", "has", "have", "had", "be", "been", "color", "colour",
    "near", "inside", "outside", "room", "floor", "block", "building"
}


class MatchingEngine:
    """Calculates weighted similarity scores between lost and found items."""

    @staticmethod
    def _tokenize(text: str) -> set:
        if not text:
            return set()
        words = re.findall(r'\b[a-zA-Z0-9]{2,}\b', text.lower())
        return {w for w in words if w not in STOPWORDS}

    def compute_similarity(self, lost_item: dict, found_item: dict) -> dict:
        """
        Calculates similarity score out of 100 points:
          - Item Name similarity: 30 pts
          - Category match: 20 pts
          - Location match: 20 pts
          - Date proximity: 15 pts
          - Description keywords: 15 pts
        """
        # 1. Item Name (30 pts)
        name1 = str(lost_item.get('item_name', '')).strip().lower()
        name2 = str(found_item.get('item_name', '')).strip().lower()
        name_ratio = difflib.SequenceMatcher(None, name1, name2).ratio()
        name_score = round(name_ratio * 30.0, 1)

        # 2. Category Match (20 pts)
        cat1 = str(lost_item.get('category', '')).strip().lower()
        cat2 = str(found_item.get('category', '')).strip().lower()
        if cat1 and cat2 and cat1 == cat2:
            cat_score = 20.0
        else:
            cat_score = 0.0

        # 3. Location Match (20 pts)
        loc1 = str(lost_item.get('location', '')).strip().lower()
        loc2 = str(found_item.get('location', '')).strip().lower()
        if loc1 and loc2 and loc1 == loc2:
            loc_score = 20.0
        elif loc1 and loc2 and (loc1 in loc2 or loc2 in loc1):
            loc_score = 10.0
        else:
            loc_score = 0.0

        # 4. Date Proximity (15 pts)
        date_score = 0.0
        d1_str = str(lost_item.get('item_date', ''))[:10]
        d2_str = str(found_item.get('item_date', ''))[:10]
        try:
            d1 = datetime.strptime(d1_str, "%Y-%m-%d")
            d2 = datetime.strptime(d2_str, "%Y-%m-%d")
            diff_days = abs((d1 - d2).days)
            if diff_days <= 3:
                date_score = 15.0
            elif diff_days <= 7:
                date_score = 10.0
            elif diff_days <= 14:
                date_score = 5.0
            elif diff_days <= 30:
                date_score = 2.0
            else:
                date_score = 0.0
        except Exception:
            date_score = 5.0  # neutral if unparseable

        # 5. Description & Features Keywords (15 pts)
        text1 = f"{lost_item.get('description', '')} {lost_item.get('distinguishing_features', '')}"
        text2 = f"{found_item.get('description', '')} {found_item.get('distinguishing_features', '')}"
        tokens1 = self._tokenize(text1)
        tokens2 = self._tokenize(text2)
        if tokens1 and tokens2:
            overlap = tokens1.intersection(tokens2)
            max_possible = min(len(tokens1), len(tokens2))
            desc_ratio = len(overlap) / max_possible if max_possible > 0 else 0
            desc_score = round(min(15.0, desc_ratio * 15.0), 1)
        else:
            desc_score = 0.0

        total_score = round(name_score + cat_score + loc_score + date_score + desc_score, 1)
        total_score = min(100.0, max(0.0, total_score))

        return {
            "total_score": total_score,
            "name_score": name_score,
            "category_score": cat_score,
            "location_score": loc_score,
            "date_score": date_score,
            "description_score": desc_score,
        }

    def run_matching(self, new_item_id: int = None) -> list:
        """
        Runs matching comparisons and writes to matches table.
        If new_item_id is provided, matches that item against opposite open items.
        Otherwise matches all open lost items against open found items.
        Returns list of newly created or updated match dicts.
        """
        matches_found = []

        if new_item_id:
            target = db.get_item_by_id(new_item_id)
            if not target:
                return []
            if target['item_type'] == 'lost':
                lost_items = [target]
                found_items = db.get_all_items(item_type='found', status='open')
            else:
                lost_items = db.get_all_items(item_type='lost', status='open')
                found_items = [target]
        else:
            lost_items = db.get_all_items(item_type='lost', status='open')
            found_items = db.get_all_items(item_type='found', status='open')

        for lost in lost_items:
            for found in found_items:
                scores = self.compute_similarity(lost, found)
                if scores["total_score"] >= MATCH_THRESHOLD:
                    match_id = db.create_or_update_match(
                        lost_item_id=lost['item_id'],
                        found_item_id=found['item_id'],
                        similarity_score=scores["total_score"],
                        name_score=scores["name_score"],
                        category_score=scores["category_score"],
                        location_score=scores["location_score"],
                        date_score=scores["date_score"],
                        description_score=scores["description_score"],
                    )
                    matches_found.append({
                        "match_id": match_id,
                        "lost_item": lost,
                        "found_item": found,
                        "score": scores["total_score"]
                    })

        return matches_found


matching_engine = MatchingEngine()


# ---------------------------------------------------------------------------
# MatchingFrame GUI
# ---------------------------------------------------------------------------

class MatchingFrame(ctk.CTkFrame):
    """Screen displaying potential matches for the current user's items."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.theme = None
        self._filter_mode = "all"  # "all", "strong", "moderate"
        self._matches_data = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_ui()

    def _build_ui(self):
        # 1. Header Frame
        header = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        header.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            header,
            text="🔗  Automatic Item Matches",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        title.grid(row=0, column=0, sticky="w")

        subtitle = ctk.CTkLabel(
            header,
            text="System-detected possible matches between reported lost and found belongings.",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray60")
        )
        subtitle.grid(row=1, column=0, sticky="w", pady=(2, 0))

        btn_box = ctk.CTkFrame(header, fg_color="transparent")
        btn_box.grid(row=0, column=1, rowspan=2, sticky="e")

        self.refresh_btn = ctk.CTkButton(
            btn_box,
            text="🔄 Refresh Matches",
            width=140,
            command=self.refresh_matches
        )
        self.refresh_btn.pack(side="right", padx=5)

        # 2. Filter tabs
        filter_bar = ctk.CTkFrame(self, corner_radius=8)
        filter_bar.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))

        self.tab_all = ctk.CTkButton(
            filter_bar, text="All Matches", width=120, height=32,
            command=lambda: self._set_filter("all")
        )
        self.tab_all.pack(side="left", padx=8, pady=6)

        self.tab_strong = ctk.CTkButton(
            filter_bar, text="🟢 Strong (80%+)", width=140, height=32,
            fg_color="transparent",
            command=lambda: self._set_filter("strong")
        )
        self.tab_strong.pack(side="left", padx=8, pady=6)

        self.tab_moderate = ctk.CTkButton(
            filter_bar, text="🟠 Moderate (60-79%)", width=160, height=32,
            fg_color="transparent",
            command=lambda: self._set_filter("moderate")
        )
        self.tab_moderate.pack(side="left", padx=8, pady=6)

        self.count_label = ctk.CTkLabel(
            filter_bar, text="0 matches", font=ctk.CTkFont(size=12, weight="bold")
        )
        self.count_label.pack(side="right", padx=16, pady=6)

        # 3. Scrollable matches container
        self.scroll = ctk.CTkScrollableFrame(self, corner_radius=10)
        self.scroll.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.scroll.grid_columnconfigure(0, weight=1)

    def refresh_data(self):
        """Called when this frame is navigated to."""
        self.load_matches()

    def refresh_matches(self):
        """Triggers MatchingEngine and reloads."""
        try:
            self.refresh_btn.configure(state="disabled", text="Matching...")
            self.update()
            matching_engine.run_matching()
            self.load_matches()
            messagebox.showinfo("Matching Complete", "Automatic matching analysis finished successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to run matching: {e}")
        finally:
            self.refresh_btn.configure(state="normal", text="🔄 Refresh Matches")

    def _set_filter(self, mode: str):
        self._filter_mode = mode
        # Update tab visual styling
        theme = self.theme or {}
        accent = theme.get("accent_primary", "#2d7a2d")
        for tab, t_mode in [(self.tab_all, "all"), (self.tab_strong, "strong"), (self.tab_moderate, "moderate")]:
            if t_mode == mode:
                tab.configure(fg_color=accent, text_color="white")
            else:
                tab.configure(fg_color="transparent", text_color=theme.get("text_primary", "black"))
        self._render_cards()

    def load_matches(self):
        """Fetch matches from DB for current user or all if admin."""
        user = getattr(self.controller, 'current_user', None)
        if not user:
            return

        if user.get('role') == 'admin':
            raw_matches = db.get_all_matches(min_score=MATCH_THRESHOLD)
        else:
            raw_matches = db.get_matches_for_user(user['user_id'], min_score=MATCH_THRESHOLD)

        self._matches_data = raw_matches
        self._render_cards()

    def _render_cards(self):
        # Clear existing cards
        for widget in self.scroll.winfo_children():
            widget.destroy()

        # Filter matches
        filtered = []
        for m in self._matches_data:
            score = float(m.get('similarity_score', 0))
            if self._filter_mode == "strong" and score < 80:
                continue
            if self._filter_mode == "moderate" and (score < 60 or score >= 80):
                continue
            filtered.append(m)

        self.count_label.configure(text=f"{len(filtered)} match(es) displayed")

        if not filtered:
            empty_box = ctk.CTkFrame(self.scroll, fg_color="transparent")
            empty_box.pack(expand=True, fill="both", pady=60)
            ctk.CTkLabel(
                empty_box, text="🔍", font=ctk.CTkFont(size=48)
            ).pack(pady=(0, 10))
            ctk.CTkLabel(
                empty_box,
                text="No matches found in this category.",
                font=ctk.CTkFont(size=16, weight="bold")
            ).pack()
            ctk.CTkLabel(
                empty_box,
                text="Matches are generated when reported lost and found items share key attributes.\nTry reporting items or refreshing the matching engine.",
                font=ctk.CTkFont(size=12),
                text_color="gray"
            ).pack(pady=6)
            return

        for m in filtered:
            self._create_match_card(m)

    def _create_match_card(self, match: dict):
        score = float(match.get('similarity_score', 0))
        is_strong = score >= 80
        badge_color = "#2d7a2d" if is_strong else "#f57c00"
        badge_text = "Strong Match" if is_strong else "Moderate Match"

        lost_item = db.get_item_by_id(match.get('lost_item_id')) or {}
        found_item = db.get_item_by_id(match.get('found_item_id')) or {}

        card = ctk.CTkFrame(self.scroll, corner_radius=12)
        card.pack(fill="x", padx=10, pady=8)
        card.grid_columnconfigure(0, weight=1)
        card.grid_columnconfigure(1, weight=0)
        card.grid_columnconfigure(2, weight=1)

        # Top Banner inside card
        banner = ctk.CTkFrame(card, height=36, corner_radius=6, fg_color="transparent")
        banner.grid(row=0, column=0, columnspan=3, sticky="ew", padx=14, pady=(10, 6))

        match_badge = ctk.CTkLabel(
            banner, text=f"  {badge_text}  ",
            fg_color=badge_color, text_color="white",
            corner_radius=6, font=ctk.CTkFont(size=11, weight="bold")
        )
        match_badge.pack(side="left")

        ref_lbl = ctk.CTkLabel(
            banner,
            text=f"Match #{match.get('match_id')} • Date: {str(match.get('created_at', ''))[:10]}",
            font=ctk.CTkFont(size=11), text_color="gray"
        )
        ref_lbl.pack(side="left", padx=10)

        # Column 0: Lost Item Info
        col_lost = ctk.CTkFrame(card, corner_radius=8)
        col_lost.grid(row=1, column=0, sticky="nsew", padx=(14, 6), pady=8)

        ctk.CTkLabel(
            col_lost, text="📋 Lost Item (Reported)",
            font=ctk.CTkFont(size=13, weight="bold"), text_color="#c62828"
        ).pack(anchor="w", padx=10, pady=(8, 4))

        ctk.CTkLabel(
            col_lost, text=f"Name: {lost_item.get('item_name', 'Unknown')}",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=10)

        ctk.CTkLabel(
            col_lost, text=f"Category: {lost_item.get('category', '-')}",
            font=ctk.CTkFont(size=11)
        ).pack(anchor="w", padx=10)

        ctk.CTkLabel(
            col_lost, text=f"Location: {lost_item.get('location', '-')}",
            font=ctk.CTkFont(size=11)
        ).pack(anchor="w", padx=10)

        ctk.CTkLabel(
            col_lost, text=f"Date: {lost_item.get('item_date', '-')}",
            font=ctk.CTkFont(size=11)
        ).pack(anchor="w", padx=10, pady=(0, 8))

        # Column 1: Middle Score Indicator
        col_score = ctk.CTkFrame(card, width=160, corner_radius=8, fg_color="transparent")
        col_score.grid(row=1, column=1, sticky="ns", padx=6, pady=8)

        ctk.CTkLabel(
            col_score, text=f"{score:.0f}%",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=badge_color
        ).pack(pady=(10, 2))

        ctk.CTkLabel(
            col_score, text="Similarity",
            font=ctk.CTkFont(size=11), text_color="gray"
        ).pack()

        # Score Breakdown items
        breakdown_text = (
            f"Name: {match.get('name_score', 0):.0f}/30\n"
            f"Category: {match.get('category_score', 0):.0f}/20\n"
            f"Location: {match.get('location_score', 0):.0f}/20\n"
            f"Date: {match.get('date_score', 0):.0f}/15\n"
            f"Desc: {match.get('description_score', 0):.0f}/15"
        )
        ctk.CTkLabel(
            col_score, text=breakdown_text,
            font=ctk.CTkFont(size=10), text_color="gray", justify="center"
        ).pack(pady=4)

        # Action Button: Submit Claim or View
        claim_btn = ctk.CTkButton(
            col_score, text="Submit Claim",
            width=120, height=32,
            fg_color=badge_color,
            command=lambda: self._submit_claim_for_match(match, lost_item, found_item)
        )
        claim_btn.pack(pady=(6, 10))

        # Column 2: Found Item Info
        col_found = ctk.CTkFrame(card, corner_radius=8)
        col_found.grid(row=1, column=2, sticky="nsew", padx=(6, 14), pady=8)

        ctk.CTkLabel(
            col_found, text="📦 Found Item (Registered)",
            font=ctk.CTkFont(size=13, weight="bold"), text_color="#2d7a2d"
        ).pack(anchor="w", padx=10, pady=(8, 4))

        ctk.CTkLabel(
            col_found, text=f"Name: {found_item.get('item_name', 'Unknown')}",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=10)

        ctk.CTkLabel(
            col_found, text=f"Category: {found_item.get('category', '-')}",
            font=ctk.CTkFont(size=11)
        ).pack(anchor="w", padx=10)

        ctk.CTkLabel(
            col_found, text=f"Location: {found_item.get('location', '-')}",
            font=ctk.CTkFont(size=11)
        ).pack(anchor="w", padx=10)

        ctk.CTkLabel(
            col_found, text=f"Date: {found_item.get('item_date', '-')}",
            font=ctk.CTkFont(size=11)
        ).pack(anchor="w", padx=10, pady=(0, 8))

    def _submit_claim_for_match(self, match: dict, lost_item: dict, found_item: dict):
        """Opens SubmitClaim dialog with prefilled lost and found IDs."""
        try:
            from student.claims import SubmitClaimDialog
            dlg = SubmitClaimDialog(
                self,
                prefill_found_id=found_item.get('item_id'),
                prefill_lost_id=lost_item.get('item_id'),
                on_submitted=self.load_matches
            )
            dlg.focus()
        except Exception as e:
            messagebox.showerror("Error", f"Could not open claim dialog: {e}")

    def apply_theme(self, theme: dict):
        self.theme = theme
        try:
            self.configure(fg_color=theme.get("bg_primary", "transparent"))
            accent = theme.get("accent_primary", "#2d7a2d")
            self.refresh_btn.configure(
                fg_color=accent,
                hover_color=theme.get("accent_hover", "#1f5a1f")
            )
            self._set_filter(self._filter_mode)
        except Exception:
            pass
