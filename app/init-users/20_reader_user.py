import os

from _role_utils import ensure_login_role, grant_db_connect, revoke_all_schemas, grant_schema_read_only, grant_system_role

READER_DB_USER = os.getenv("READER_DB_USER", "github_reader")
READER_DB_PASSWORD = os.getenv("READER_DB_PASSWORD", "reader_password_change_me")
POSTGRES_DB = os.getenv("POSTGRES_DB", "github_data")

def apply(conn) -> None:
    """Crée et configure l'utilisateur lecteur dans la base de données.

    Args:
        conn: Connexion à la base de données PostgreSQL.
    """
    with conn.cursor() as cur:
        # Crée le rôle de l'utilisateur lecteur
        ensure_login_role(cur, READER_DB_USER, READER_DB_PASSWORD)

        # Accorde la connexion à la base de données
        grant_db_connect(cur, POSTGRES_DB, READER_DB_USER)

        # Révoque tous les privilèges sur les schémas existants
        revoke_all_schemas(cur, READER_DB_USER)

        # Accorde les privilèges en lecture seule sur les schémas existants
        grant_schema_read_only(cur, "github", READER_DB_USER)
        grant_schema_read_only(cur, "monitoring", READER_DB_USER)

        # Accorde l'accès aux vues de monitoring PostgreSQL (pg_stat_activity, etc.)
        grant_system_role(cur, "pg_monitor", READER_DB_USER)