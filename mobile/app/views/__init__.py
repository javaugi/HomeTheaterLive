# views/__init__.py

def get_home_view(app):
    """Lazy import for HomeView"""
    from .home_view import HomeView
    return HomeView(app)


def get_login_view(app):
    """Lazy import for LoginView"""
    from .login_view import LoginView
    return LoginView(app)
