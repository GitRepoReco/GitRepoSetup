import os

from _role_utils import ensure_login_role, grant_db_connect, revoke_schema_all, grant_schema_read_only

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
        revoke_schema_all(cur, "public", POSTGRES_DB)

        # Accorde les privilèges en lecture seule sur les schémas existants
        grant_schema_read_only(cur, "github", POSTGRES_DB)