import re

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from mozilla_django_oidc.auth import OIDCAuthenticationBackend


USERNAME_MAX_LENGTH = 150


def _sanitize_username(value):
    value = str(value or '').strip().lower()
    value = value.replace('@', '_at_')
    value = re.sub(r'[^a-z0-9._-]+', '_', value)
    value = re.sub(r'_+', '_', value).strip('._-')
    return value[:USERNAME_MAX_LENGTH]


def _normalize_claim_values(value):
    if value is None:
        return []

    if isinstance(value, (list, tuple, set)):
        normalized = []
        for item in value:
            normalized.extend(_normalize_claim_values(item))
        return normalized

    if isinstance(value, dict):
        for key in ('roles', 'groups'):
            if key in value:
                return _normalize_claim_values(value.get(key))
        return []

    text = str(value).strip()
    if not text:
        return []

    if ',' in text:
        return [item.strip() for item in text.split(',') if item.strip()]

    return [text]


def _extract_claim_path(claims, path):
    current = claims
    for key in str(path).split('.'):
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return None
    return current


def _sanitize_group_name(group_name):
    value = str(group_name or '').strip()
    if not value:
        return ''
    return value[:150]


class WriteHatOIDCAuthenticationBackend(OIDCAuthenticationBackend):

    def _extract_values_from_claims(self, claims, claim_paths):
        values = []
        for claim_path in claim_paths:
            claim_value = _extract_claim_path(claims, claim_path)
            for value in _normalize_claim_values(claim_value):
                if value not in values:
                    values.append(value)
        return values

    def _resolve_role_values(self, claims):
        return self._extract_values_from_claims(claims, getattr(settings, 'SSO_ROLE_CLAIM_PATHS', []))

    def _resolve_group_values(self, claims, role_values):
        groups = self._extract_values_from_claims(claims, getattr(settings, 'SSO_GROUP_CLAIM_PATHS', []))

        # Optional mapping from IdP role names to Django group names.
        for role_value in role_values:
            mapped_group = getattr(settings, 'SSO_ROLE_TO_GROUP_MAP', {}).get(role_value.lower(), '')
            if mapped_group and mapped_group not in groups:
                groups.append(mapped_group)

        return groups

    def _sync_role_flags(self, user, role_values):
        role_values_lc = {role.lower() for role in role_values}
        staff_roles = set(getattr(settings, 'SSO_STAFF_ROLES', []))
        superuser_roles = set(getattr(settings, 'SSO_SUPERUSER_ROLES', []))

        is_superuser = bool(getattr(settings, 'SSO_DEFAULT_IS_SUPERUSER', False) or (role_values_lc & superuser_roles))
        is_staff = bool(getattr(settings, 'SSO_DEFAULT_IS_STAFF', False) or (role_values_lc & staff_roles))

        if getattr(settings, 'SSO_STAFF_IF_SUPERUSER', True) and is_superuser:
            is_staff = True

        if getattr(settings, 'SSO_SYNC_ROLE_FLAGS', True):
            user.is_superuser = is_superuser
            user.is_staff = is_staff
        else:
            if is_superuser:
                user.is_superuser = True
            if is_staff:
                user.is_staff = True

        if getattr(settings, 'SSO_STAFF_IF_SUPERUSER', True) and user.is_superuser:
            user.is_staff = True

    def _sync_groups(self, user, group_values):
        if not getattr(settings, 'SSO_SYNC_GROUPS', False):
            return

        group_objects = []
        for group_value in group_values:
            group_name = _sanitize_group_name(group_value)
            if not group_name:
                continue
            group_object, _ = Group.objects.get_or_create(name=group_name)
            group_objects.append(group_object)

        if getattr(settings, 'SSO_SYNC_GROUPS_STRICT', False):
            user.groups.set(group_objects)
            return

        if group_objects:
            user.groups.add(*group_objects)

    def _apply_role_management(self, user, claims):
        role_values = self._resolve_role_values(claims)
        self._sync_role_flags(user, role_values)

        group_values = self._resolve_group_values(claims, role_values)
        self._sync_groups(user, group_values)

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
        self._apply_role_management(user, claims)
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
        self._apply_role_management(user, claims)
        user.save()
        return user
