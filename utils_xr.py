"""
utils_xr.py
Utility functions for hydrological analysis project.
"""

def show_info(msg: str, level: str = "info", log_func=None):
    """
    Display information to the user.
    If log_func is provided (GUI mode), it's called with (msg, level).
    Otherwise (CLI mode), it's printed to the terminal.
    """
    if log_func is not None:
        try:
            log_func(msg, level=level)
        except TypeError:
            # Fallback if log_func doesn't accept level
            log_func(msg)
    else:
        icon = {"info": "ℹ️", "success": "✅", "warning": "⚠️", "error": "❌"}.get(level, "ℹ️")
        print(f"{icon} {msg}")
