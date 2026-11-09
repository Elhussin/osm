import getpass
import os
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from directory.provisioning import provision_company


class Command(BaseCommand):
    help = "Provision a company and first owner using an explicit retry key; deployment role only."

    def add_arguments(self, parser):
        parser.add_argument("--name", required=True)
        parser.add_argument("--domain", required=True)
        parser.add_argument("--owner", required=True)
        parser.add_argument("--email", default="")
        parser.add_argument("--operation-key", required=True)

    def handle(self, **options):
        if not connection.settings_dict["NAME"].startswith("optics_rebuild_"):
            raise CommandError("A dedicated rebuild database is required")
        password = os.environ.get("OSM_REBUILD_OWNER_PASSWORD") or getpass.getpass("New owner password: ")
        connection.set_schema_to_public()
        try:
            company = provision_company(name=options["name"], domain=options["domain"], username=options["owner"], password=password, email=options["email"], operation_key=options["operation_key"])
        except Exception:
            raise CommandError("Provisioning failed; company remains unavailable. Resolve the failure and retry with the same operation key.") from None
        self.stdout.write(f"Company {company.pk} is ready at {options['domain']}; no password values printed.")
