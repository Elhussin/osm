"""Provision a rebuild-only DML role using the migration connection, not runtime."""
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from psycopg import sql
from config.environment import required
from directory.models import Company

ROLE = "optics_rebuild_runtime"


class Command(BaseCommand):
    help = "Configure the dedicated rebuild runtime DB role (no DDL or role creation)."

    def handle(self, **options):
        if not connection.settings_dict["NAME"].startswith("optics_rebuild_"):
            raise CommandError("Only a dedicated rebuild database can be configured")
        connection.set_schema_to_public()
        password = required("RUNTIME_DB_PASSWORD")
        with connection.cursor() as cursor:
            cursor.execute("SELECT rolsuper, rolcreatedb, rolcreaterole FROM pg_roles WHERE rolname = %s", [ROLE])
            existing = cursor.fetchone()
            if existing and any(existing):
                raise CommandError("Existing runtime role is privileged; refusing to reuse it")
            if existing:
                cursor.execute("SELECT 1 FROM pg_auth_members m JOIN pg_roles r ON r.oid = m.member WHERE r.rolname = %s", [ROLE])
                if cursor.fetchone():
                    raise CommandError("Existing runtime role has memberships; refusing to reuse it")
            if existing is None:
                cursor.execute(sql.SQL("CREATE ROLE {} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT").format(sql.Identifier(ROLE)))
            # Utility statements cannot use server-bound parameters for a password.
            cursor.execute(sql.SQL("ALTER ROLE {} PASSWORD {}").format(sql.Identifier(ROLE), sql.Literal(password)))
            db = sql.Identifier(connection.settings_dict["NAME"])
            cursor.execute(sql.SQL("REVOKE CREATE ON DATABASE {} FROM PUBLIC").format(db))
            cursor.execute(sql.SQL("REVOKE ALL ON DATABASE {} FROM {}").format(db, sql.Identifier(ROLE)))
            cursor.execute(sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(db, sql.Identifier(ROLE)))
            cursor.execute("REVOKE CREATE ON SCHEMA public FROM PUBLIC")
            cursor.execute(sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(sql.Identifier(ROLE)))
            for table in ("directory_company", "directory_companydomain", "django_migrations"):
                cursor.execute(sql.SQL("GRANT SELECT ON TABLE public.{} TO {}").format(sql.Identifier(table), sql.Identifier(ROLE)))
            for schema in Company.objects.exclude(schema_name="public").values_list("schema_name", flat=True):
                cursor.execute(sql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(sql.Identifier(schema), sql.Identifier(ROLE)))
                cursor.execute(sql.SQL("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA {} TO {}").format(sql.Identifier(schema), sql.Identifier(ROLE)))
                cursor.execute(sql.SQL("GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA {} TO {}").format(sql.Identifier(schema), sql.Identifier(ROLE)))
                cursor.execute(sql.SQL("REVOKE INSERT, UPDATE, DELETE ON TABLE {}.django_migrations FROM {}").format(sql.Identifier(schema), sql.Identifier(ROLE)))
        self.stdout.write("Configured rebuild runtime role; no credential values printed. Re-run after provisioning new tenant schemas.")
