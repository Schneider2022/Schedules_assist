"""
OAuth2 service layer.
Centralises GitHub SSO configuration so routers stay thin.
"""

from fastapi_sso.sso.github import GithubSSO

from app.config import settings


def get_github_sso() -> GithubSSO:
    """
    Return a configured GithubSSO instance.

    fastapi-sso handles:
      • Building the authorization URL
      • The `state` parameter for CSRF protection
      • Token exchange at the callback
      • Fetching the user's GitHub profile (including verified email)
    """
    return GithubSSO(
        client_id=settings.GITHUB_CLIENT_ID,
        client_secret=settings.GITHUB_CLIENT_SECRET,
        redirect_uri=settings.GITHUB_REDIRECT_URI,
        allow_insecure_http=settings.APP_ENV == "development",  # HTTP only in dev
    )
