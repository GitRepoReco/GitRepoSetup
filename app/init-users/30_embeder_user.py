import os

from _role_utils import ensure_login_role, grant_db_connect, revoke_all_schemas, grant_schema_read_only, grant_schema_dml

EMBEDER_DB_USER = os.getenv("EMBEDER_DB_USER", "embeder_user")
EMBEDER_DB_PASSWORD = os.getenv("EMBEDER_DB_PASSWORD", "embeder_password_change_me")
POSTGRES_DB = os.getenv("POSTGRES_DB", "github_data")

def apply(conn) -> None:
    """Crée et configure l'utilisateur embeder dans la base de données PostgreSQL.
    """
    with conn.cursor() as cur:
        ensure_login_role(cur, EMBEDER_DB_USER, EMBEDER_DB_PASSWORD)
        grant_db_connect(cur, POSTGRES_DB, EMBEDER_DB_USER)
        revoke_all_schemas(cur, EMBEDER_DB_USER)
        grant_schema_read_only(cur, "github", EMBEDER_DB_USER)
        grant_schema_dml(cur, "embedding", EMBEDER_DB_USER)