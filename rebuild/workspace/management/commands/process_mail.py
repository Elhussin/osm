from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django_tenants.utils import tenant_context
from directory.models import Company
from workspace.mail_worker import process_pending


class Command(BaseCommand):
    help = "Process bounded invitation/reset outboxes for ready companies; run periodically."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=20)

    def handle(self, *args, **options):
        if not 1 <= options["limit"] <= 100:
            raise CommandError("limit must be between 1 and 100")
        connection.set_schema_to_public()
        companies = list(Company.objects.filter(state=Company.State.READY))
        count = 0
        for company in companies:
            with tenant_context(company):
                count += process_pending(options["limit"])
        self.stdout.write(f"Processed {count} mail job(s); no recipient or token output.")
