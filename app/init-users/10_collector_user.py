import os

from _role_utils import ensure_login_role, grant_db_connect, grant_schema_dml, revoke_schema_all, grant_schema_read_insert

COLLECTOR_DB_USER = os.getenv("COLLECTOR_DB_USER", "github_collector")
COLLECTOR_DB_PASSWORD = os.getenv("COLLECTOR_DB_PASSWORD", "collector_password_change_me")
POSTGRES_DB = os.getenv("POSTGRES_DB", "github_data")


def apply(conn) -> None:
    """Crée et configure le rôle applicatif collector avec privilèges DML restreints."""
    with conn.cursor() as cur:
        ensure_login_role(cur, COLLECTOR_DB_USER, COLLECTOR_DB_PASSWORD)
        grant_db_connect(cur, POSTGRES_DB, COLLECTOR_DB_USER)

        revoke_schema_all(cur, "public", COLLECTOR_DB_USER)
        grant_schema_read_insert(cur, "github", COLLECTOR_DB_USER)
        grant_schema_dml(cur, "monitoring", COLLECTOR_DB_USER)
