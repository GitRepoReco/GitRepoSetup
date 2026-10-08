from psycopg2 import sql


def ensure_login_role(cur, username: str, password: str, *, rotate_password: bool = True) -> None:
    if rotate_password:
        cur.execute(
            sql.SQL(
                """
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = {user_literal}) THEN
                        CREATE ROLE {user_ident} WITH LOGIN PASSWORD {password_literal};
                    ELSE
                        ALTER ROLE {user_ident} WITH LOGIN PASSWORD {password_literal};
                    END IF;
                END $$;
                """
            ).format(
                user_literal=sql.Literal(username),
                user_ident=sql.Identifier(username),
                password_literal=sql.Literal(password),
            )
        )
        return

    cur.execute(
        sql.SQL(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = {user_literal}) THEN
                    CREATE ROLE {user_ident} WITH LOGIN PASSWORD {password_literal};
                END IF;
            END $$;
            """
        ).format(
            user_literal=sql.Literal(username),
            user_ident=sql.Identifier(username),
            password_literal=sql.Literal(password),
        )
    )


def grant_db_connect(cur, db_name: str, username: str) -> None:
    cur.execute(
        sql.SQL("GRANT CONNECT ON DATABASE {db_ident} TO {user_ident};").format(
            db_ident=sql.Identifier(db_name),
            user_ident=sql.Identifier(username),
        )
    )


def revoke_schema_all(cur, schema_name: str, username: str) -> None:
    cur.execute(
        sql.SQL("REVOKE ALL ON SCHEMA {schema_ident} FROM {user_ident};").format(
            schema_ident=sql.Identifier(schema_name),
            user_ident=sql.Identifier(username),
        )
    )


def grant_schema_dml(cur, schema_name: str, username: str) -> None:
    cur.execute(
        sql.SQL("GRANT USAGE ON SCHEMA {schema_ident} TO {user_ident};").format(
            schema_ident=sql.Identifier(schema_name),
            user_ident=sql.Identifier(username),
        )
    )
    cur.execute(
        sql.SQL(
            "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA {schema_ident} TO {user_ident};"
        ).format(
            schema_ident=sql.Identifier(schema_name),
            user_ident=sql.Identifier(username),
        )
    )
    cur.execute(
        sql.SQL(
            "GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA {schema_ident} TO {user_ident};"
        ).format(
            schema_ident=sql.Identifier(schema_name),
            user_ident=sql.Identifier(username),
        )
    )
    cur.execute(
        sql.SQL(
            "ALTER DEFAULT PRIVILEGES IN SCHEMA {schema_ident} GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {user_ident};"
        ).format(
            schema_ident=sql.Identifier(schema_name),
            user_ident=sql.Identifier(username),
        )
    )
    cur.execute(
        sql.SQL(
            "ALTER DEFAULT PRIVILEGES IN SCHEMA {schema_ident} GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO {user_ident};"
        ).format(
            schema_ident=sql.Identifier(schema_name),
            user_ident=sql.Identifier(username),
        )
    )


def grant_schema_read_only(cur, schema_name: str, username: str) -> None:
    cur.execute(
        sql.SQL("GRANT USAGE ON SCHEMA {schema_ident} TO {user_ident};").format(
            schema_ident=sql.Identifier(schema_name),
            user_ident=sql.Identifier(username),
        )
    )
    cur.execute(
        sql.SQL("GRANT SELECT ON ALL TABLES IN SCHEMA {schema_ident} TO {user_ident};").format(
            schema_ident=sql.Identifier(schema_name),
            user_ident=sql.Identifier(username),
        )
    )
    cur.execute(
        sql.SQL("GRANT SELECT ON ALL SEQUENCES IN SCHEMA {schema_ident} TO {user_ident};").format(
            schema_ident=sql.Identifier(schema_name),
            user_ident=sql.Identifier(username),
        )
    )
    cur.execute(
        sql.SQL(
            "ALTER DEFAULT PRIVILEGES IN SCHEMA {schema_ident} GRANT SELECT ON TABLES TO {user_ident};"
        ).format(
            schema_ident=sql.Identifier(schema_name),
            user_ident=sql.Identifier(username),
        )
    )
    cur.execute(
        sql.SQL(
            "ALTER DEFAULT PRIVILEGES IN SCHEMA {schema_ident} GRANT SELECT ON SEQUENCES TO {user_ident};"
        ).format(
            schema_ident=sql.Identifier(schema_name),
            user_ident=sql.Identifier(username),
        )
    )


def grant_schema_read_insert(cur, schema_name: str, username: str) -> None:
    cur.execute(
        sql.SQL("GRANT USAGE ON SCHEMA {schema_ident} TO {user_ident};").format(
            schema_ident=sql.Identifier(schema_name),
            user_ident=sql.Identifier(username),
        )
    )
    cur.execute(
        sql.SQL("GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA {schema_ident} TO {user_ident};").format(
            schema_ident=sql.Identifier(schema_name),
            user_ident=sql.Identifier(username),
        )
    )
    cur.execute(
        sql.SQL("GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA {schema_ident} TO {user_ident};").format(
            schema_ident=sql.Identifier(schema_name),
            user_ident=sql.Identifier(username),
        )
    )
    cur.execute(
        sql.SQL(
            "ALTER DEFAULT PRIVILEGES IN SCHEMA {schema_ident} GRANT SELECT, INSERT, UPDATE ON TABLES TO {user_ident};"
        ).format(
            schema_ident=sql.Identifier(schema_name),
            user_ident=sql.Identifier(username),
        )
    )
    cur.execute(
        sql.SQL(
            "ALTER DEFAULT PRIVILEGES IN SCHEMA {schema_ident} GRANT USAGE, SELECT ON SEQUENCES TO {user_ident};"
        ).format(
            schema_ident=sql.Identifier(schema_name),
            user_ident=sql.Identifier(username),
        )
    )
