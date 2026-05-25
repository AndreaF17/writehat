# WriteHat (Independent Fork)

This repository is an independently maintained fork of WriteHat.

It is **not** intended to be merged back into the original upstream project. This fork has its own roadmap, release cycle, and operational decisions.

## What Is Included In This Fork

- CVSS 4.0 support for findings and finding groups
- CWE category import from file upload (`.xml` or `.zip`)
- One-click CWE online sync from MITRE feed
- OIDC-based SSO support (optional)
- Local custom component packs (outside this repo) so teams can extend reporting without pushing private code publicly

## Quick Start

1. Clone the repository.
2. Edit [writehat/config/writehat.conf](writehat/config/writehat.conf) with secure passwords and environment values.
3. Start services:

```bash
docker compose up -d --build
```

1. Open the app through your configured nginx endpoint.

## Core Runtime Configuration

Main config file: [writehat/config/writehat.conf](writehat/config/writehat.conf)

### Base App

- `[writehat]`: admin bootstrap account, secret, hosts, timezone
- `[mongo]`: Mongo connection
- `[mysql]`: MySQL connection
- `[ldap]`: LDAP auth settings (optional)

### SSO (OIDC)

This fork adds optional OIDC SSO under `[sso]`.

Important keys:

- `enabled`
- `auto_redirect`
- `display_name`
- `client_id`
- `client_secret`
- `authorization_endpoint`
- `token_endpoint`
- `userinfo_endpoint`
- `jwks_endpoint`
- `logout_endpoint`
- `sign_algo`
- `verify_ssl`
- `scopes`
- `allowed_email_domains`
- `require_verified_email`
- `role_claim_paths`
- `staff_roles`
- `superuser_roles`
- `default_is_staff`
- `default_is_superuser`
- `sync_role_flags`
- `staff_if_superuser`
- `sync_groups`
- `sync_groups_strict`
- `group_claim_paths`
- `role_to_group_map`

When enabled:

- Login page shows a "Sign In With <display_name>" button
- `/login/sso` starts the OIDC flow
- OIDC callback routes are mounted under `/oidc/`

### Custom Components (Private, Local)

This fork supports loading component packs from paths outside the repository via `[custom_components]`.

```toml
[custom_components]
paths = [
  '/opt/writehat-plugins/acme-pack'
]
```

Each component pack can include:

- `components/*.py`
- `templates/**`
- `static/**`

Recommended layout:

```text
/opt/writehat-plugins/acme-pack/
  components/
    ExecutiveSummary.py
  templates/
    componentTemplates/
      ExecutiveSummary.html
  static/
    css/
      component/
        ExecutiveSummary.css
```

You can also set component roots from environment variable `WRITEHAT_COMPONENT_PATHS` (OS path-separator delimited).

## CWE Category Import + Sync

In Findings (superuser):

- **Import CWE**: upload official CWE XML or ZIP feed
- **Sync CWE**: fetch latest feed online from MITRE

The header shows a persistent last-sync note with timestamp and entry count.

Behavior:

- Import is idempotent by CWE ID (`CWE-<id>:` prefix)
- Deprecated/obsolete CWE entries are ignored
- Existing entries are skipped on re-import/sync

## SSO Deployment Notes

1. Install dependencies (Docker image build handles this automatically).
2. Fill `[sso]` values in [writehat/config/writehat.conf](writehat/config/writehat.conf).
3. Restart the app container:

```bash
docker compose up -d --build writehat
```

1. Test login via `/login` and `/login/sso`.

Security controls available:

- Email verified requirement
- Allowed email domain list

Role management controls available:

- Map IdP roles to Django `is_staff`
- Map IdP roles to Django `is_superuser`
- Keep Django role flags synced (or only elevate)
- Optionally sync Django groups from IdP claims

Example role mapping:

```toml
[sso]
enabled = true
staff_roles = ['writehat_staff', 'writehat_editor']
superuser_roles = ['writehat_admin']
sync_role_flags = true
sync_groups = true
group_claim_paths = ['groups']
role_to_group_map = { writehat_admin = 'Admins', writehat_editor = 'Editors' }
```

## Custom Component Workflow (Private Team Development)

1. Create a private plugin directory outside the public repo.
2. Add your component Python files + templates + static assets.
3. Add plugin root path to `[custom_components].paths`.
4. Restart WriteHat.
5. Components appear in report builder automatically if import succeeds.

If a component fails to import, startup logs include the import error.

## Operations

### Restart services

```bash
docker compose restart
```

### Rebuild app dependencies

```bash
docker compose up -d --build writehat
```

### View logs

```bash
docker compose logs -f writehat
```

### Run migrations manually (if needed)

```bash
docker compose exec writehat ./manage.py makemigrations
docker compose exec writehat ./manage.py migrate
```

## Independent Fork Policy

This fork is managed independently.

- Upstream compatibility is not guaranteed
- Feature and schema changes can diverge
- Release and security patch timelines are controlled by this fork maintainer

If you consume this fork in production, pin your version and maintain your own deployment validation process.

## Troubleshooting

### SSO button not visible

- Verify `[sso].enabled = true`
- Rebuild/restart app after config change
- Check logs for missing OIDC dependency

### OIDC callback loops to login

- Ensure provider endpoints and client credentials are correct
- Verify callback URL configured in IdP matches `/oidc/callback/`
- Confirm TLS/host settings are correct from the browser perspective

### Custom component not listed

- Validate component filename is a valid Python module name
- Check plugin path exists and is mounted in runtime
- Verify component exports `Component` class
- Check logs for import errors

### CWE sync fails

- Confirm outbound network access to MITRE feed
- Use manual **Import CWE** upload if outbound access is restricted

## License

This project remains distributed under the repository license in [LICENSE](LICENSE).
