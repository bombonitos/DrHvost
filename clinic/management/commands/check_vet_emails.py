from django.core.management.base import BaseCommand
from clinic.models import Vet

class Command(BaseCommand):
    help = 'Проверяет email адреса врачей'

    def handle(self, *args, **options):
        vets = Vet.objects.all()
        for vet in vets:
            self.stdout.write(f"Врач: {vet.name}")
            self.stdout.write(f"Email: {vet.email}")
            self.stdout.write("-" * 50) 