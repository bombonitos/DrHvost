from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from clinic.models import Vet, Pet, Appointment
from datetime import date, time

class Command(BaseCommand):
    help = 'Создает тестовые данные для приложения'

    def handle(self, *args, **kwargs):
        # Создаем тестового пользователя-врача
        vet_user, created = User.objects.get_or_create(
            username='vet',
            defaults={
                'email': 'vet@example.com',
                'is_staff': True
            }
        )
        if created:
            vet_user.set_password('vet123')
            vet_user.save()
            self.stdout.write(self.style.SUCCESS(f'Создан пользователь-врач: {vet_user.username}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Пользователь-врач уже существует: {vet_user.username}'))

        # Создаем врача
        vet, created = Vet.objects.get_or_create(
            user=vet_user,
            defaults={
                'first_name': 'Иван',
                'last_name': 'Петров',
                'otchestvo': 'Сергеевич',
                'specialty': 'Терапевт',
                'phone_number': '+7 (999) 123-45-67',
                'available': True
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Создан врач: {vet.name}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Врач уже существует: {vet.name}'))

        # Создаем тестового пользователя-клиента
        client_user, created = User.objects.get_or_create(
            username='client',
            defaults={
                'email': 'client@example.com'
            }
        )
        if created:
            client_user.set_password('client123')
            client_user.save()
            self.stdout.write(self.style.SUCCESS(f'Создан пользователь-клиент: {client_user.username}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Пользователь-клиент уже существует: {client_user.username}'))

        # Создаем питомца
        pet, created = Pet.objects.get_or_create(
            owner=client_user,
            name='Барсик',
            defaults={
                'species': 'cat',
                'gender': 'male',
                'breed': 'Сибирская',
                'age': 3,
                'owner_name': 'Анна Иванова',
                'contact_phone': '+7 (999) 765-43-21',
                'vet': vet
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Создан питомец: {pet.name}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Питомец уже существует: {pet.name}'))

        # Создаем запись на прием
        appointment, created = Appointment.objects.get_or_create(
            pet=pet,
            vet=vet,
            date=date.today(),
            time=time(hour=10, minute=0),
            defaults={
                'description': 'Плановый осмотр',
                'status': 'pending'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Создана запись на прием: {appointment}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Запись на прием уже существует: {appointment}'))

        self.stdout.write(self.style.SUCCESS('Тестовые данные успешно созданы')) 