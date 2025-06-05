from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Vet, Pet, Appointment, BlogPost
from .forms import AppointmentForm, PetForm
from datetime import datetime, timedelta
from django.core.files.uploadedfile import SimpleUploadedFile


class PetModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass',
            email='test@example.com'
        )

        self.vet = Vet.objects.create(
            user=self.user,
            first_name='Test',
            last_name='Vet',
            specialty='General',
            available=True
        )

    def test_pet_creation(self):
        pet = Pet.objects.create(
            owner=self.user,
            name='TestPet',
            species='dog',
            breed='TestBreed',
            age=5,
            vet=self.vet,
            owner_name='Test Owner',
            contact_phone='+7999999999'
        )

        self.assertEqual(pet.name, 'TestPet')
        self.assertEqual(pet.species, 'dog')
        self.assertEqual(pet.breed, 'TestBreed')
        self.assertEqual(pet.age, 5)
        self.assertEqual(pet.owner, self.user)
        self.assertEqual(pet.vet, self.vet)


class AppointmentModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )

        self.vet = Vet.objects.create(
            user=self.user,
            first_name='Test',
            last_name='Vet',
            specialty='General'
        )

        self.pet = Pet.objects.create(
            owner=self.user,
            name='TestPet',
            species='dog',
            breed='TestBreed',
            age=5,
            vet=self.vet,
            owner_name='Test Owner',
            contact_phone='+7999999999'
        )

    def test_appointment_creation(self):
        appointment = Appointment.objects.create(
            pet=self.pet,
            vet=self.vet,
            date=datetime.now().date(),
            time=datetime.strptime('10:00', '%H:%M').time(),
            description='Test appointment'
        )

        self.assertEqual(appointment.pet, self.pet)
        self.assertEqual(appointment.vet, self.vet)
        self.assertEqual(appointment.description, 'Test appointment')
        self.assertEqual(appointment.status, 'pending')


class ViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )
        self.client.login(username='testuser', password='testpass')

        # Создаем тестовое изображение для ветеринара
        image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'',
            content_type='image/jpeg'
        )

        self.vet = Vet.objects.create(
            user=self.user,
            first_name='Test',
            last_name='Vet',
            specialty='General',
            available=True,
            photo=image
        )

        self.pet = Pet.objects.create(
            owner=self.user,
            name='TestPet',
            species='dog',
            breed='TestBreed',
            age=5,
            vet=self.vet,
            owner_name='Test Owner',
            contact_phone='+7999999999'
        )

        # Создаем тестовую статью блога
        self.blog_post = BlogPost.objects.create(
            title='Test Post',
            content='Test Content',
            author=self.vet
        )

    def test_home_page(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'clinic/home.html')

    def test_booking_page(self):
        response = self.client.get(reverse('booking'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'clinic/booking.html')


class FormsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )

        # Создаем тестовое изображение для ветеринара
        image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'',
            content_type='image/jpeg'
        )

        self.vet = Vet.objects.create(
            user=self.user,
            first_name='Test',
            last_name='Vet',
            specialty='General',
            available=True,
            photo=image
        )

        self.pet = Pet.objects.create(
            owner=self.user,
            name='TestPet',
            species='dog',
            breed='TestBreed',
            age=5,
            vet=self.vet,
            owner_name='Test Owner',
            contact_phone='+7999999999'
        )

    def test_appointment_form(self):
        form_data = {
            'pet': self.pet.id,
            'vet': self.vet.id,
            'date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
            'time': '10:00',
            'description': 'Test appointment'
        }
        form = AppointmentForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())

    def test_pet_form(self):
        form_data = {
            'name': 'TestPet',
            'species': 'dog',
            'gender': 'male',
            'breed': 'TestBreed',
            'age': 5,
            'owner_name': 'Test Owner',
            'contact_phone': '+7999999999'
        }
        form = PetForm(data=form_data)
        self.assertTrue(form.is_valid())