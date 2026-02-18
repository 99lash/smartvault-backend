"""
Metric card widget for displaying KPI values.
"""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widget import Widget
from textual.widgets import Label, Static


class MetricCard(Widget):
    """A card displaying a metric with title, value, and optional subtitle."""
    
    DEFAULT_CSS = """
    MetricCard {
        width: auto;
        height: auto;
        min-width: 20;
        border: solid $primary;
        padding: 1 2;
        margin: 0 1;
    }
    
    MetricCard .metric-title {
        color: $text-muted;
        text-style: bold;
    }
    
    MetricCard .metric-value {
        color: $text;
        text-style: bold;
        text-align: center;
    }
    
    MetricCard .metric-subtitle {
        color: $text-muted;
        text-align: center;
    }
    """
    
    def __init__(
        self, 
        title: str, 
        value: str | int, 
        subtitle: str | None = None,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self._title = title
        self._value = str(value)
        self._subtitle = subtitle
    
    def compose(self) -> ComposeResult:
        yield Label(self._title, classes="metric-title")
        yield Label(self._value, classes="metric-value")
        if self._subtitle:
            yield Label(self._subtitle, classes="metric-subtitle")
    
    def update_value(self, value: str | int) -> None:
        """Update the metric value."""
        self._value = str(value)
        try:
            label = self.query(Label)[1]
            label.update(self._value)
        except Exception:
            pass


class MetricRow(Widget):
    """A row of metric cards."""
    
    DEFAULT_CSS = """
    MetricRow {
        layout: horizontal;
        width: 100%;
        height: auto;
    }
    """
    
    def __init__(self, metrics: list[dict], **kwargs) -> None:
        """
        Args:
            metrics: List of dicts with keys: title, value, subtitle (optional)
        """
        super().__init__(**kwargs)
        self._metrics = metrics
    
    def compose(self) -> ComposeResult:
        for m in self._metrics:
            yield MetricCard(
                title=m["title"],
                value=m["value"],
                subtitle=m.get("subtitle"),
            )


class ProgressBar(Static):
    """A simple progress bar widget."""
    
    DEFAULT_CSS = """
    ProgressBar {
        height: 1;
    }
    """
    
    def __init__(
        self, 
        value: float = 0, 
        max_value: float = 100,
        width_chars: int = 30,
        **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self._value = value
        self._max_value = max_value
        self._width_chars = width_chars
        self._update_display()
    
    def _update_display(self) -> None:
        if self._max_value <= 0:
            percent = 0
        else:
            percent = min(100, int((self._value / self._max_value) * 100))
        
        filled = int((percent / 100) * self._width_chars)
        empty = self._width_chars - filled
        
        bar = "█" * filled + "░" * empty
        self.update(f"[{bar}] {percent}%")
    
    def update_value(self, value: float) -> None:
        """Update the progress bar value."""
        self._value = value
        self._update_display()
