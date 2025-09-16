from django.core.management.base import BaseCommand
from api.models import Client

SAMPLE_CLIENTS = [
    {"name": "Alice Johnson", "email": "alice@example.com", "phone": "+1-202-555-0101"},
    {"name": "Bob Smith", "email": "bob@example.com", "phone": "+1-202-555-0102"},
    {"name": "Carol Lee", "email": "carol@example.com", "phone": "+1-202-555-0103"},
    {"name": "Diego Pérez", "email": "diego@example.com", "phone": "+34-600-555-010"},
    {"name": "Eve Müller", "email": "eve@example.com", "phone": "+49-30-555-0104"},
]

class Command(BaseCommand):
    help = "Seed the database with sample clients"

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true', help='Delete all existing clients before seeding')

    def handle(self, *args, **options):
        reset = options.get('reset', False)
        if reset:
            count = Client.objects.count()
            Client.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Deleted {count} existing clients"))

        created = 0
        skipped = 0
        for c in SAMPLE_CLIENTS:
            obj, was_created = Client.objects.get_or_create(email=c["email"], defaults={
                "name": c["name"],
                "phone": c.get("phone", ""),
            })
            if was_created:
                created += 1
            else:
                # Update name/phone if different to keep data fresh
                changed = False
                if obj.name != c["name"]:
                    obj.name = c["name"]
                    changed = True
                if obj.phone != c.get("phone", ""):
                    obj.phone = c.get("phone", "")
                    changed = True
                if changed:
                    obj.save()
                skipped += 1
        self.stdout.write(self.style.SUCCESS(f"Seed complete: {created} created, {skipped} existing"))
