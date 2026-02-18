"""
Trends screen — user signup and vault provisioning over time.

Shows ASCII sparklines and KPI summary for both series.
Window switchable with 7 / 3 / 9 keys (7, 30, 90 days).
"""
from __future__ import annotations

from typing import Any

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Label

from smartvault_admin_tui.screens.base import BaseScreen

# Max bar width in characters
_BAR_WIDTH = 30


def _sparkline(daily: list[dict], max_width: int = _BAR_WIDTH) -> str:
    """
    Render daily data as a multi-line ASCII bar chart string.

    Each line: YYYY-MM-DD  ████░░░░  12

    Args:
        daily:     List of {date, count} dicts from the API response.
        max_width: Maximum bar width in characters.

    Returns:
        Multi-line string ready for a Label widget.
    """
    if not daily:
        return "No data"

    peak = max(d["count"] for d in daily)
    lines: list[str] = []

    for entry in daily:
        count = entry["count"]
        bar_len = round((count / peak) * max_width) if peak > 0 else 0
        bar = "█" * bar_len
        lines.append(f"{entry['date']}  {bar:<{max_width}}  {count}")

    return "\n".join(lines)


def _change_label(change_pct: float | None) -> str:
    """Format change_pct as a human-readable direction label."""
    if change_pct is None:
        return "trend: no prior data"
    arrow = "▲" if change_pct >= 0 else "▼"
    return f"trend: {arrow} {abs(change_pct):.1f}%"


class TrendsScreen(BaseScreen):
    """Business trends — user signups and vault provisioning over time."""

    BINDINGS = [
        ("escape", "back", "Back"),
        ("r", "refresh", "Refresh"),
        ("7", "window_7", "7 days"),
        ("3", "window_30", "30 days"),
        ("9", "window_90", "90 days"),
    ]

    DEFAULT_CSS = """
    TrendsScreen {
        layout: vertical;
    }

    TrendsScreen .section-title {
        text-style: bold;
        color: $primary;
        margin: 1 0;
    }

    TrendsScreen .kpi-row {
        layout: horizontal;
        height: auto;
        margin: 0 0 1 0;
    }

    TrendsScreen .kpi-item {
        padding: 0 2;
        width: 1fr;
    }

    TrendsScreen .sparkline {
        margin: 1 0;
        color: $text;
    }

    TrendsScreen #loading {
        text-align: center;
        padding: 2;
        color: $text-muted;
    }

    TrendsScreen #window-label {
        color: $text-muted;
        margin-bottom: 1;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._data: dict[str, Any] | None = None
        self._days = 30

    def compose(self) -> ComposeResult:
        with Container():
            yield Label("Loading trends...", id="loading")
            with Container(id="content", classes="hidden"):
                yield Label("", id="window-label")

                # User signups section
                yield Label("USER SIGNUPS", classes="section-title")
                with Horizontal(classes="kpi-row"):
                    yield Label("", id="users-total", classes="kpi-item")
                    yield Label("", id="users-avg", classes="kpi-item")
                    yield Label("", id="users-peak", classes="kpi-item")
                    yield Label("", id="users-trend", classes="kpi-item")
                yield Label("", id="users-sparkline", classes="sparkline")

                # Vault provisioning section
                yield Label("VAULT PROVISIONING", classes="section-title")
                with Horizontal(classes="kpi-row"):
                    yield Label("", id="vaults-total", classes="kpi-item")
                    yield Label("", id="vaults-avg", classes="kpi-item")
                    yield Label("", id="vaults-peak", classes="kpi-item")
                    yield Label("", id="vaults-trend", classes="kpi-item")
                yield Label("", id="vaults-sparkline", classes="sparkline")

    async def on_mount(self) -> None:
        """Load data when screen mounts."""
        self.run_worker(self.load_data())

    async def load_data(self) -> None:
        """Fetch trend data from API."""
        loading = self.query_one("#loading", Label)
        content = self.query_one("#content", Container)

        try:
            loading.update(f"Loading {self._days}-day trends...")
            loading.remove_class("hidden")
            content.add_class("hidden")

            self._data = await self.api_client.get_business_trends(days=self._days)

            self._render_data()
            loading.add_class("hidden")
            content.remove_class("hidden")

        except Exception as e:
            self.handle_error(e, "Trends Load Error")
            loading.update(f"Error: {e}")

    def _render_data(self) -> None:
        """Render fetched data into widgets."""
        if not self._data:
            return

        self.query_one("#window-label", Label).update(
            f"Period: {self._data.get('period_start')} → "
            f"{self._data.get('period_end')}  "
            f"[7] 7d  [3] 30d  [9] 90d"
        )

        self._render_series(
            series=self._data.get("user_signups", {}),
            total_id="users-total",
            avg_id="users-avg",
            peak_id="users-peak",
            trend_id="users-trend",
            sparkline_id="users-sparkline",
        )
        self._render_series(
            series=self._data.get("vault_provisioning", {}),
            total_id="vaults-total",
            avg_id="vaults-avg",
            peak_id="vaults-peak",
            trend_id="vaults-trend",
            sparkline_id="vaults-sparkline",
        )

    def _render_series(
        self,
        series: dict,
        total_id: str,
        avg_id: str,
        peak_id: str,
        trend_id: str,
        sparkline_id: str,
    ) -> None:
        """Render one trend series into its widgets."""
        self.query_one(f"#{total_id}", Label).update(
            f"Total: {series.get('total', 0):,}"
        )
        self.query_one(f"#{avg_id}", Label).update(
            f"Avg/day: {series.get('average_per_day', 0)}"
        )
        peak_date = series.get("peak_date") or "—"
        peak_count = series.get("peak_count", 0)
        self.query_one(f"#{peak_id}", Label).update(
            f"Peak: {peak_count} on {peak_date}"
        )
        self.query_one(f"#{trend_id}", Label).update(
            _change_label(series.get("change_pct"))
        )
        self.query_one(f"#{sparkline_id}", Label).update(
            _sparkline(series.get("daily", []))
        )

    # =========================================================================
    # WINDOW SWITCHING
    # =========================================================================

    def action_window_7(self) -> None:
        """Switch to 7-day window."""
        self._days = 7
        self.run_worker(self.load_data(), exclusive=True, group="refresh")

    def action_window_30(self) -> None:
        """Switch to 30-day window."""
        self._days = 30
        self.run_worker(self.load_data(), exclusive=True, group="refresh")

    def action_window_90(self) -> None:
        """Switch to 90-day window."""
        self._days = 90
        self.run_worker(self.load_data(), exclusive=True, group="refresh")