from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.db.utils import ProgrammingError
from directory.models import Company


class Command(BaseCommand):
    help = "Verify the active rebuild runtime connection cannot create schemas or alter the directory."

    def handle(self, **options):
        if not connection.settings_dict["NAME"].startswith("optics_rebuild_"):
            raise CommandError("Only a dedicated rebuild database can be verified")
        connection.set_schema_to_public()
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_user, rolsuper, rolcreatedb, rolcreaterole FROM pg_roles WHERE rolname = current_user")
            name, superuser, createdb, createrole = cursor.fetchone()
            if name != "optics_rebuild_runtime" or any((superuser, createdb, createrole)):
                raise CommandError("The active connection is not the restricted runtime role")
            cursor.execute("SELECT has_schema_privilege(current_user, 'public', 'CREATE'), has_database_privilege(current_user, current_database(), 'CREATE')")
            if any(cursor.fetchone()):
                raise CommandError("Runtime unexpectedly has DDL privileges")
        Company.objects.count()  # Read-only access to the tenant directory is necessary.
        for statement in (
            "CREATE SCHEMA r03_runtime_permission_probe",
            "CREATE TABLE public.r03_runtime_permission_probe (id integer)",
            "UPDATE public.directory_company SET name = name WHERE false",
        ):
            denied = False
            try:
                with transaction.atomic():
                    with connection.cursor() as cursor:
                        cursor.execute(statement)
                    transaction.set_rollback(True)  # Even a failure to restrict creates no lasting object.
            except ProgrammingError as exc:
                if getattr(exc.__cause__, "sqlstate", None) != "42501":
                    raise CommandError("Unexpected error during runtime permission verification") from None
                denied = True
            if not denied:
                raise CommandError("Runtime permission boundary failed")
        self.stdout.write("PASS: runtime reads directory; schema/table creation and directory writes denied.")
