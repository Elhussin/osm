from django.conf import settings


def set_token_cookies(response, access: str = None, refresh: str = None):
    secure_flag = not settings.DEBUG  # ← False في التطوير، True في الإنتاج
    common_cookie_args = {
    "httponly": True,
    "secure": secure_flag,  # يجب أن تكون False في التطوير
    "samesite": 'Lax' if settings.DEBUG else 'None',  # Lax في localhost
    "path": "/",
    # "domain": None if settings.DEBUG else f".{settings.TENANT_BASE_DOMAIN}", # for local only
    "domain":None
  
    }

    if access:
        response.set_cookie(
            key="access_token",
            value=access,
            max_age=60 * 15,
            **common_cookie_args
        )

    if refresh:
        response.set_cookie(
            key="refresh_token",
            value=refresh,
            max_age=60 * 60 * 24 * 7,
            **common_cookie_args
        )


