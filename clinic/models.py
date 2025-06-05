from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import datetime, time
from django.dispatch import receiver
from django.db.models.signals import post_save


class Vet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='vet', null=True)
    first_name = models.CharField(max_length=50, default='')
    last_name = models.CharField(max_length=50, default='')
    otchestvo = models.CharField(max_length=50, blank=True, null=True)
    specialty = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    available = models.BooleanField(default=True)
    email = models.EmailField(null=True, blank=True)
    photo = models.ImageField(upload_to='vet_photos/', blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def name(self):
        if self.otchestvo:
            return f"{self.last_name} {self.first_name} {self.otchestvo}"
        return f"{self.last_name} {self.first_name}"


class Pet(models.Model):
    SPECIES_CHOICES = [
        ('dog', 'Собака'),
        ('cat', 'Кошка'),
        ('bird', 'Птица'),
        ('rodent', 'Грызун'),
        ('reptile', 'Рептилия'),
        ('other', 'Другое'),
    ]

    GENDER_CHOICES = [
        ('male', 'Самец'),
        ('female', 'Самка'),
    ]

    name = models.CharField(max_length=100, verbose_name='Кличка')
    species = models.CharField(max_length=20, choices=SPECIES_CHOICES, verbose_name='Вид')
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, verbose_name='Пол')
    breed = models.CharField(max_length=100, verbose_name='Порода')
    age = models.IntegerField(verbose_name='Возраст')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pets', verbose_name='Владелец')
    owner_name = models.CharField(max_length=100, verbose_name='Имя владельца')
    contact_phone = models.CharField(max_length=20, verbose_name='Контактный телефон')
    photo = models.ImageField(upload_to='pets/', null=True, blank=True, verbose_name='Фото питомца')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.get_species_display()})"

    class Meta:
        verbose_name = 'Питомец'
        verbose_name_plural = 'Питомцы'
        ordering = ['-created_at']


class Appointment(models.Model):
    TIME_CHOICES = [
        (time(hour=9, minute=0), '09:00'),
        (time(hour=10, minute=0), '10:00'),
        (time(hour=11, minute=0), '11:00'),
        (time(hour=12, minute=0), '12:00'),
        (time(hour=13, minute=0), '13:00'),
        (time(hour=14, minute=0), '14:00'),
        (time(hour=15, minute=0), '15:00'),
        (time(hour=16, minute=0), '16:00'),
        (time(hour=17, minute=0), '17:00'),
    ]

    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='appointments')
    vet = models.ForeignKey('Vet', on_delete=models.CASCADE, related_name='appointments')
    date = models.DateField()
    time = models.TimeField(choices=TIME_CHOICES)
    description = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Ожидает'),
        ('completed', 'Завершен'),
        ('cancelled', 'Отменен')
    ], default='pending')

    class Meta:
        ordering = ['date', 'time']
        constraints = [
            models.UniqueConstraint(
                fields=['vet', 'date', 'time'],
                condition=models.Q(status='pending'),
                name='unique_active_appointment'
            )
        ]

    def __str__(self):
        return f"{self.pet.name} - {self.vet} - {self.date} {self.time}"


class BlogPost(models.Model):
    title = models.CharField(max_length=200, verbose_name='Заголовок')
    content = models.TextField(verbose_name='Содержание')
    image = models.ImageField(upload_to='blog_images/', verbose_name='Изображение')
    author = models.ForeignKey('Vet', on_delete=models.CASCADE, related_name='blog_posts', verbose_name='Автор')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Статья блога'
        verbose_name_plural = 'Статьи блога'

    def __str__(self):
        return self.title


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    def __str__(self):
        return f"Профиль {self.user.username}"


# Автоматическое создание профиля при создании пользователя
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    profile = getattr(instance, 'profile', None)
    if profile:
        instance.profile.save()