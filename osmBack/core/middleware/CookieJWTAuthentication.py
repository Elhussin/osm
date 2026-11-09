
from rest_framework_simplejwt.authentication import JWTAuthentication
import logging
# optics_tenant/core/middleware.py
# This class overrides the authenticate method to retrieve the JWT from cookies
class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        raw_token = request.COOKIES.get("access_token")

        if not raw_token:
            header = self.get_header(request)
            if header is None:
                return None
            raw_token = self.get_raw_token(header)

        if raw_token is None:
            return None

        try:
            validated_token = self.get_validated_token(raw_token)
            return self.get_user(validated_token), validated_token
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error authenticating user: {e}")
            return None


