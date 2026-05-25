import re

from django.conf import settings
from django.contrib.auth import get_user_model
from mozilla_django_oidc.auth import OIDCAuthenticationBackend


USERNAME_MAX_LENGTH = 150


def _sanitize_username(value):
    value = str(value or '').strip().lower()
    value = value.replace('@', '_at_')
    value = re.sub(r'[^a-z0-9._-]+', '_', value)
    value = re.sub(r'_+', '_', value).strip('._-')
    return value[:USERNAME_MAX_LENGTH]


class WriteHatOIDCAuthenticationBackend(OIDCAuthenticationBackend):

    def verify_claims(self, claims):
        if not super().verify_claims(claims):
            return False

        if getattr(settings, 'SSO_REQUIRE_VERIFIED_EMAIL', True):
            email_verified = claims.get('email_verified', None)
            if email_verified is False:
                return False

        allowed_domains = set(getattr(settings, 'SSO_ALLOWED_EMAIL_DOMAINS', []))
        if allowed_domains:
            email = str(claims.get('email', '')).strip().lower()
            if '@' not in email:
                return False
            email_domain = email.rsplit('@', 1)[1]
            if email_domain not in allowed_domains:
                return False

        return True

    def _build_username(self, claims):
        user_model = get_user_model()

        raw_candidates = [
            claims.get('preferred_username', ''),
            claims.get('upn', ''),
            claims.get('email', ''),
            claims.get('sub', ''),
        ]

        candidates = []
        for candidate in raw_candidates:
            normalized = _sanitize_username(candidate)
            if normalized and normalized not in candidates:
                candidates.append(normalized)

        if not candidates:
            candidates.append('sso_user')

        for candidate in candidates:
            if not user_model.objects.filter(username=candidate).exists():
                return candidate

        base_candidate = candidates[0]
        for suffix in range(1, 10000):
            suffix_text = f'_{suffix}'
            trimmed = base_candidate[:max(1, USERNAME_MAX_LENGTH - len(suffix_text))]
            username = f'{trimmed}{suffix_text}'
            if not user_model.objects.filter(username=username).exists():
                return username

        return f'{base_candidate[:140]}_{claims.get("sub", "user")[:8]}'

    def filter_users_by_claims(self, claims):
        user_model = get_user_model()

        email = str(claims.get('email', '')).strip().lower()
        if email:
            users = list(user_model.objects.filter(email__iexact=email))
            if users:
                return users

        preferred_username = _sanitize_username(claims.get('preferred_username', ''))
        if preferred_username:
            users = list(user_model.objects.filter(username=preferred_username))
            if users:
                return users

        return []

    def create_user(self, claims):
        user_model = get_user_model()

        email = str(claims.get('email', '')).strip().lower()
        given_name = str(claims.get('given_name', '')).strip()
        family_name = str(claims.get('family_name', '')).strip()

        if not given_name and not family_name:
            full_name = str(claims.get('name', '')).strip()
            if full_name:
                name_parts = full_name.split(' ', 1)
                given_name = name_parts[0]
                if len(name_parts) > 1:
                    family_name = name_parts[1]

        username = self._build_username(claims)

        user = user_model.objects.create_user(
            username=username,
            email=email,
            first_name=given_name,
            last_name=family_name,
        )
        user.is_active = True
        user.save()
        return user

    def update_user(self, user, claims):
        email = str(claims.get('email', '')).strip().lower()
        if email:
            user.email = email

        given_name = str(claims.get('given_name', '')).strip()
        family_name = str(claims.get('family_name', '')).strip()
        if given_name:
            user.first_name = given_name
        if family_name:
            user.last_name = family_name

        user.is_active = True
        user.save()
        return user
