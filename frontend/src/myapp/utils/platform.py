# utils/platform.py
import sys

def is_mobile():
    """Check if running on mobile platform"""
    return sys.platform in ('android', 'ios')

def is_tablet():
    """Check if device is tablet (simplified)"""
    # You'd need device info from platform APIs
    return False

def get_safe_area_insets():
    """Get safe area insets for notched devices"""
    return {"top": 0, "bottom": 0, "left": 0, "right": 0}