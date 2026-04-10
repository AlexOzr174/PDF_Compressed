"""
UI Components - Reusable UI elements
Modern Python 3.14+ with ttkbootstrap and async support
"""

import tkinter as tk
from tkinter import font as tkfont
from typing import Callable
from pathlib import Path


class ToolTip:
    """
    Modern tooltip implementation for tkinter widgets
    
    Features:
    - Delay before showing
    - Auto-hide on mouse leave
    - Custom styling
    """
    
    def __init__(
        self,
        widget: tk.Widget,
        text: str,
        delay_ms: int = 500,
        bg_color: str = "#333333",
        fg_color: str = "#ffffff",
        font_size: int = 10,
    ):
        self.widget = widget
        self.text = text
        self.delay_ms = delay_ms
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.font_size = font_size
        
        self.tip_window: tk.Toplevel | None = None
        self._after_id: str | None = None
        
        # Bind events
        widget.bind("<Enter>", self._on_enter, "+")
        widget.bind("<Leave>", self._on_leave, "+")
        widget.bind("<ButtonPress>", self._on_leave, "+")
    
    def _on_enter(self, event: tk.Event) -> None:
        """Handle mouse enter event"""
        self._schedule_show()
    
    def _on_leave(self, event: tk.Event) -> None:
        """Handle mouse leave event"""
        self._hide_tip()
        if self._after_id:
            self.widget.after_cancel(self._after_id)
            self._after_id = None
    
    def _schedule_show(self) -> None:
        """Schedule tooltip to show after delay"""
        if self._after_id:
            self.widget.after_cancel(self._after_id)
        self._after_id = self.widget.after(self.delay_ms, self._show_tip)
    
    def _show_tip(self) -> None:
        """Display the tooltip"""
        if self.tip_window:
            return
        
        # Create tooltip window
        self.tip_window = tw = tk.Toplevel(self.widget)
        
        # Remove window decorations
        tw.wm_overrideredirect(True)
        
        # Get widget position
        x, y, _, cy = self.widget.winfo_rootx(), self.widget.winfo_rooty(), 0, self.widget.winfo_height()
        
        # Position tooltip below widget
        offset_x = x + (self.widget.winfo_width() - 20) // 2
        offset_y = y + cy + 5
        
        tw.wm_geometry(f"+{offset_x}+{offset_y}")
        
        # Create label with styling
        label = tk.Label(
            tw,
            text=self.text,
            justify=tk.CENTER,
            background=self.bg_color,
            foreground=self.fg_color,
            relief=tk.SOLID,
            borderwidth=1,
            padx=8,
            pady=4,
            wraplength=250,
        )
        label.config(font=(tkfont.nametofont("TkDefaultFont").actual("family"), self.font_size))
        label.pack()
        
        # Make tooltip stay on top
        tw.wm_attributes("-topmost", True)
    
    def _hide_tip(self) -> None:
        """Hide the tooltip"""
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None
    
    def update_text(self, new_text: str) -> None:
        """Update tooltip text"""
        self.text = new_text
        if self.tip_window:
            self._hide_tip()
            self._show_tip()


class TextHandler(tk.Text):
    """
    Custom text widget with auto-scrolling and formatting
    
    Designed for log display in the application
    """
    
    def __init__(
        self,
        master: tk.Misc | None = None,
        max_lines: int = 1000,
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self.max_lines = max_lines
        self._line_count = 0
        
        # Configure default styling
        self.config(
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=("Consolas", 9),
        )
        
        # Configure tags for different log levels
        self.tag_configure("INFO", foreground="#2E7D32")
        self.tag_configure("WARNING", foreground="#F57C00")
        self.tag_configure("ERROR", foreground="#C62828")
        self.tag_configure("DEBUG", foreground="#1976D2")
        self.tag_configure("CRITICAL", foreground="#B71C1C", background="#FFEBEE")
    
    def append_line(self, text: str, level: str = "INFO") -> None:
        """Append a line with formatting"""
        self.config(state=tk.NORMAL)
        
        # Trim old lines if exceeding max
        if self._line_count >= self.max_lines:
            self.delete("1.0", "2.0")
            self._line_count -= 1
        
        # Insert text with tag
        timestamp = Path().stat().st_mtime  # Just as placeholder, real impl would use datetime
        line = f"[{level}] {text}\n"
        self.insert(tk.END, line, level)
        self._line_count += 1
        
        # Auto-scroll to end
        self.see(tk.END)
        self.config(state=tk.DISABLED)
    
    def clear(self) -> None:
        """Clear all text"""
        self.config(state=tk.NORMAL)
        self.delete("1.0", tk.END)
        self._line_count = 0
        self.config(state=tk.DISABLED)


class ThemeManager:
    """
    Theme manager for ttkbootstrap applications
    
    Supports light/dark themes and custom color schemes
    """
    
    THEMES = {
        "dark": {
            "name": "Dark",
            "bootstrap_theme": "darkly",
            "bg_primary": "#2b2b2b",
            "bg_secondary": "#3c3f41",
            "fg_primary": "#ffffff",
            "fg_secondary": "#aaaaaa",
            "accent": "#4a9eff",
            "success": "#4caf50",
            "warning": "#ff9800",
            "error": "#f44336",
        },
        "light": {
            "name": "Light",
            "bootstrap_theme": "litera",
            "bg_primary": "#ffffff",
            "bg_secondary": "#f5f5f5",
            "fg_primary": "#212121",
            "fg_secondary": "#757575",
            "accent": "#1976d2",
            "success": "#388e3c",
            "warning": "#f57c00",
            "error": "#d32f2f",
        },
        "blue": {
            "name": "Blue",
            "bootstrap_theme": "cosmo",
            "bg_primary": "#e3f2fd",
            "bg_secondary": "#bbdefb",
            "fg_primary": "#0d47a1",
            "fg_secondary": "#42a5f5",
            "accent": "#2196f3",
            "success": "#4caf50",
            "warning": "#ff9800",
            "error": "#f44336",
        },
    }
    
    def __init__(self, initial_theme: str = "dark"):
        self.current_theme = initial_theme
        self._callbacks: list[Callable[[str], None]] = []
    
    def get_theme(self, name: str) -> dict[str, str]:
        """Get theme configuration"""
        return self.THEMES.get(name, self.THEMES["dark"])
    
    def set_theme(self, theme_name: str) -> None:
        """Set active theme and notify callbacks"""
        if theme_name not in self.THEMES:
            theme_name = "dark"
        
        self.current_theme = theme_name
        self._notify_callbacks(theme_name)
    
    def register_callback(self, callback: Callable[[str], None]) -> None:
        """Register a callback for theme changes"""
        self._callbacks.append(callback)
    
    def unregister_callback(self, callback: Callable[[str], None]) -> None:
        """Unregister a callback"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    def _notify_callbacks(self, theme_name: str) -> None:
        """Notify all registered callbacks of theme change"""
        for callback in self._callbacks:
            try:
                callback(theme_name)
            except Exception:
                pass  # Silently ignore callback errors
    
    @property
    def available_themes(self) -> list[str]:
        """Get list of available theme names"""
        return list(self.THEMES.keys())
    
    @property
    def current_config(self) -> dict[str, str]:
        """Get current theme configuration"""
        return self.get_theme(self.current_theme)
