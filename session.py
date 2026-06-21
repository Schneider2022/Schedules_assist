"""
Session helpers.
Thin wrappers around Starlette's signed-cookie session so the rest of the
app never touches raw session keys directly.
"""

from typing import Optional

from starlette.requests import Request

_SESSION_KEY = "user"


def save_user(request: Request, email: str, name: Optional[str], picture: Optional[str]) -> None:
    """Persist minimal user info in the signed session cookie."""
    request.session[_SESSION_KEY] = {
        "email": email,
        "name": name or "",
        "picture": picture or "",
    }


def get_current_user(request: Request) -> Optional[dict]:
    """Return the stored user dict, or None if not logged in."""
    return request.session.get(_SESSION_KEY)


def clear_user(request: Request) -> None:
    """Remove user data from the session (logout)."""
    request.session.pop(_SESSION_KEY, None)
