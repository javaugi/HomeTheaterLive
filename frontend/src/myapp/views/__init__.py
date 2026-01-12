# views/__init__.py
import sys

def get_home_view(app):
    """Lazy import for HomeView"""
    from .home import HomeView
    return HomeView(app)

def get_login_view(app):
    """Lazy import for LoginView"""
    from .login import LoginView
    return LoginView(app)