from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from clinic.models import Vet

class Command(BaseCommand):
    help = 'Creates user accounts for existing vets'

    def handle(self, *args, **options):
        vets = Vet.objects.filter(user__isnull=True)
        for vet in vets:
            # Создаем имя пользователя из имени врача (транслитерация)
            username = vet.name.lower().replace(' ', '_')
            
            # Создаем пользователя
            user = User.objects.create_user(
                username=username,
                password='changeme123',  # Временный пароль
                email=''
            )
            
            # Связываем врача с пользователем
            vet.user = user
            vet.save()
            
            self.stdout.write(self.style.SUCCESS(
                f'Successfully created user for vet: {vet.name} (username: {username})'
            )) 