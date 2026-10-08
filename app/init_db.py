#!/usr/bin/env python3
"""
GitRepoReco — Script d'initialisation de la base de données PostgreSQL.
Attend que la base soit disponible, exécute les scripts SQL dans l'ordre,
et applique les scripts Python de rôles utilisateurs.
"""

import importlib.util
import logging
import os
import sys
import time
from pathlib import Path
from typing import Callable, cast

import psycopg2
from dotenv import load_dotenv

load_dotenv()

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] GitRepoReco-Init — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger("init_db")

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "github_data")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")

COLLECTOR_DB_USER = os.getenv("COLLECTOR_DB_USER", "github_collector")

ROOT_DIR = Path(__file__).parent
SQL_INIT_DIR = ROOT_DIR / "init-scripts"
USER_INIT_DIR = ROOT_DIR / "init-users"
if str(USER_INIT_DIR) not in sys.path:
    sys.path.insert(0, str(USER_INIT_DIR))


def wait_for_postgres(max_attempts: int = 30, delay: float = 2.0) -> psycopg2.extensions.connection:
    """Attend que PostgreSQL soit prêt à accepter les connexions."""
    logger.info(
        "Tentative de connexion à PostgreSQL (%s:%s, base='%s', utilisateur='%s')...",
        POSTGRES_HOST,
        POSTGRES_PORT,
        POSTGRES_DB,
        POSTGRES_USER,
    )
    for attempt in range(1, max_attempts + 1):
        try:
            conn = psycopg2.connect(
                host=POSTGRES_HOST,
                port=POSTGRES_PORT,
                database=POSTGRES_DB,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
                connect_timeout=5,
            )
            logger.info("Connexion à PostgreSQL établie avec succès !")
            return conn
        except psycopg2.OperationalError as exc:
            logger.warning(
                "PostgreSQL non disponible (tentative %d/%d) : %s. Nouvelle tentative dans %.1fs...",
                attempt,
                max_attempts,
                exc,
                delay,
            )
            time.sleep(delay)

    logger.error("Impossible de joindre PostgreSQL après %d tentatives. Arrêt.", max_attempts)
    sys.exit(1)


def execute_sql_file(conn: psycopg2.extensions.connection, file_path: Path) -> None:
    """Exécute un script SQL."""
    logger.info("-> Exécution du script SQL : %s", file_path.name)
    with file_path.open("r", encoding="utf-8") as f:
        sql_content = f.read()

    with conn.cursor() as cur:
        cur.execute(sql_content)

    logger.info("   [OK] %s appliqué avec succès.", file_path.name)


def load_user_script_apply(file_path: Path) -> Callable[[psycopg2.extensions.connection], None]:
    """Charge dynamiquement un script utilisateur et retourne sa fonction apply(conn)."""
    module_name = f"init_user_{file_path.stem.replace('-', '_')}"
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Impossible de créer un module Python pour {file_path.name}.")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    apply_fn = getattr(module, "apply", None)
    if apply_fn is None:
        raise AttributeError(
            f"Le script utilisateur '{file_path.name}' doit exposer une fonction apply(conn)."
        )
    if not callable(apply_fn):
        raise TypeError(
            f"La valeur 'apply' du script '{file_path.name}' n'est pas une fonction callable."
        )
    return cast(Callable[[psycopg2.extensions.connection], None], apply_fn)


def execute_user_init_file(conn: psycopg2.extensions.connection, file_path: Path) -> None:
    """Exécute un script Python d'initialisation utilisateur via apply(conn)."""
    logger.info("-> Exécution du script utilisateur : %s", file_path.name)
    apply_fn = load_user_script_apply(file_path)
    apply_fn(conn)
    logger.info("   [OK] %s appliqué avec succès.", file_path.name)


def list_user_init_files(init_dir: Path) -> list[Path]:
    """Retourne les scripts Python utilisateur à exécuter dans un ordre stable."""
    files = sorted(init_dir.glob("*.py"))
    return [file_path for file_path in files if not file_path.name.startswith("_")]


def print_summary(conn: psycopg2.extensions.connection) -> None:
    """Affiche un récapitulatif des schémas, tables et rôles créés."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT table_schema, count(*)
            FROM information_schema.tables
            WHERE table_schema IN ('github', 'monitoring')
            GROUP BY table_schema
            ORDER BY table_schema;
            """
        )
        rows = cur.fetchall()

    logger.info("=== Résumé des schémas initialisés ===")
    if not rows:
        logger.warning("Aucune table trouvée dans les schémas attendus.")
    for schema, count in rows:
        logger.info(" - Schéma '%s' : %d table(s)", schema, count)

    with conn.cursor() as cur:
        cur.execute(
            "SELECT extname, extversion FROM pg_extension WHERE extname IN ('uuid-ossp', 'pg_trgm', 'vector');"
        )
        extensions = cur.fetchall()

    logger.info("=== Extensions actives ===")
    for extname, extversion in extensions:
        logger.info(" - Extension '%s' (version %s)", extname, extversion)

    with conn.cursor() as cur:
        cur.execute("SELECT rolname FROM pg_roles WHERE rolname = %s;", (COLLECTOR_DB_USER,))
        role = cur.fetchone()

    if role:
        logger.info("=== Rôle applicatif configuré ===")
        logger.info(" - Rôle '%s' présent avec privilèges restreints.", role[0])


def main() -> None:
    logger.info("==================================================")
    logger.info("Démarrage du conteneur d'initialisation GitRepoReco")
    logger.info("==================================================")

    if not SQL_INIT_DIR.exists():
        logger.error("Le dossier %s est introuvable.", SQL_INIT_DIR)
        sys.exit(1)
    if not USER_INIT_DIR.exists():
        logger.error("Le dossier %s est introuvable.", USER_INIT_DIR)
        sys.exit(1)

    sql_files = sorted(SQL_INIT_DIR.glob("*.sql"))
    if not sql_files:
        logger.warning("Aucun script SQL trouvé dans %s.", SQL_INIT_DIR)

    user_files = list_user_init_files(USER_INIT_DIR)
    if not user_files:
        logger.warning("Aucun script utilisateur Python trouvé dans %s.", USER_INIT_DIR)

    conn = wait_for_postgres()
    try:
        for sql_file in sql_files:
            execute_sql_file(conn, sql_file)

        for user_file in user_files:
            execute_user_init_file(conn, user_file)

        print_summary(conn)
        conn.commit()

        logger.info("==================================================")
        logger.info("Initialisation terminée avec succès !")
        logger.info("La base est prête pour Analyse-github et les autres conteneurs.")
        logger.info("==================================================")
    except Exception as exc:
        logger.exception("Erreur lors de l'initialisation de la base : %s", exc)
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
