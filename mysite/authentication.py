from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.utils.timezone import now
from datetime import timedelta


class ExpiringTokenAuthentication(TokenAuthentication):
    def authenticate_credentials(self, key):
        user, token = super().authenticate_credentials(key)

        if now() - token.created > timedelta(minutes=1) and not user.is_superuser:
            token.delete()
            raise AuthenticationFailed('Token has expired')

        return user, token
