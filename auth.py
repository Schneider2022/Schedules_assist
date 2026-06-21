"""
Authentication router.

Endpoints
─────────
GET /login            → Redirects the browser to GitHub's consent screen
GET /auth/callback    → GitHub posts back here; we exchange the code for a profile
GET /logout           → Clears the session
"""

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from app.oauth import get_github_sso
from app.session import clear_user, save_user

router = APIRouter(tags=["auth"])


@router.get("/login", summary="Initiate GitHub OAuth2 login")
async def login(request: Request):
    """
    Build the GitHub authorization URL and redirect the user to it.
    fastapi-sso automatically generates and stores a CSRF `state` parameter.
    """
    async with get_github_sso() as sso:
        return await sso.get_login_redirect()


@router.get("/auth/callback", summary="GitHub OAuth2 callback")
async def auth_callback(request: Request):
    """
    Exchange the authorization code for a token, fetch the user's GitHub
    profile, store the email in the session, then redirect to the home page.

    Note: GitHub only returns an email here if the user has a public email
    set, or has granted the `user:email` scope and has at least one verified
    email on their account. fastapi-sso requests `user:email` by default.
    """
    async with get_github_sso() as sso:
        # Verifies state, exchanges code, returns an OpenID-style profile object
        user = await sso.verify_and_process(request)

    if user is None or not user.email:
        # GitHub denied access, or the account has no accessible email
        return RedirectResponse(url="/login?error=access_denied")

    # Persist only the data we actually need — no tokens stored
    save_user(
        request,
        email=user.email,
        name=user.display_name,
        picture=user.picture,
    )

    return RedirectResponse(url="/")


@router.get("/logout", summary="Clear session and log out")
async def logout(request: Request):
    """Remove the user from the session and redirect to the home page."""
    clear_user(request)
    return RedirectResponse(url="/")
