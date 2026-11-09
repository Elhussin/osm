"""Create new local secrets once. Never read or copy the legacy environment."""
import secrets
from pathlib import Path

root = Path(__file__).resolve().parents[1]
target = root / ".env"
values = {
    "OSM_REBUILD_ENVIRONMENT": "development",
    "OSM_REBUILD_SECRET_KEY": secrets.token_urlsafe(64),
    "OSM_REBUILD_ALLOWED_HOSTS": "localhost,127.0.0.1,tenant-a.localhost,tenant-b.localhost",
    "OSM_REBUILD_DB_NAME": "optics_rebuild_dev",
    "OSM_REBUILD_DB_USER": "optics_rebuild_owner",
    "OSM_REBUILD_DB_PASSWORD": secrets.token_urlsafe(32),
    "OSM_REBUILD_DB_HOST": "127.0.0.1",
    "OSM_REBUILD_DB_PORT": "55432",
    "OSM_REBUILD_RUNTIME_DB_PASSWORD": secrets.token_urlsafe(32),
}
try:
    with target.open("x", encoding="utf-8") as stream:
        stream.write("\n".join(f"{key}={value}" for key, value in values.items()) + "\n")
except FileExistsError:
    raise SystemExit("Local rebuild .env already exists; no changes made.")
print("Created rebuild/.env with new local-only secrets; values were not printed.")
