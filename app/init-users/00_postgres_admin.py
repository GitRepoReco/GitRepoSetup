import os

from _role_utils import ensure_login_role, grant_db_connect

POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_DB = os.getenv("POSTGRES_DB", "github_data")


def apply(conn) -> None:
    """Assure l'existence du rôle admin configuré et son accès à la base cible."""
    with conn.cursor() as cur:
        ensure_login_role(cur, POSTGRES_USER, POSTGRES_PASSWORD, rotate_password=False)
        grant_db_connect(cur, POSTGRES_DB, POSTGRES_USER)
