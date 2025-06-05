from celery import shared_task
from .models import Appointment
from django.core.mail import send_mail
from django.conf import settings
@shared_task
def send_appointment_reminder(appointment_id):
    try:
        appointment = Appointment.objects.get(id=appointment_id)
        user_email = appointment.pet.owner.email
        pet_name = appointment.pet.name
        vet_name = appointment.vet.name
        time = appointment.time.strftime('%H:%M')

        message = (
            f"Здравствуйте! Напоминаем, что завтра в {time} "
            f"у вас приём с {vet_name} для питомца {pet_name}."
        )
        send_mail(
            'Напоминание о приёме',
            message,
            settings.EMAIL_HOST_USER,
            [user_email],
            fail_silently=False
        )

    except Appointment.DoesNotExist:
        print("Прием не найден.")
