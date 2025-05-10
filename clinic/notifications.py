from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from datetime import timedelta
from django.utils import timezone
from .models import Appointment
import logging

logger = logging.getLogger(__name__)

def send_appointment_confirmation(appointment):
    """
    Отправка подтверждения записи на прием.
    """
    try:
        subject = "Подтверждение записи в ветеринарную клинику Dr. Хвост"
        from_email = "drhvost.vetclinic@gmail.com"
        
        # Получатели — и пользователь, и врач
        to = [
            appointment.pet.owner.email,  # email пользователя
            appointment.vet.user.email    # email врача
        ]

        context = {
            'pet_name': appointment.pet.name,
            'date': appointment.date,
            'time': appointment.time.strftime('%H:%M'),
            'vet_name': appointment.vet.name,
            'owner_name': appointment.pet.owner.get_full_name() or appointment.pet.owner.username,
        }

        text_content = render_to_string('clinic/email/appointment_confirmation.txt', context)
        html_content = render_to_string('clinic/email/appointment_confirmation.html', context)

        msg = EmailMultiAlternatives(subject, text_content, from_email, to)
        msg.attach_alternative(html_content, "text/html")

        msg.send(fail_silently=False)  # Ожидаем ошибок, если что-то пойдет не так
        logger.info(f"Email sent to {', '.join(to)}")  # Логируем успешную отправку
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        raise

def send_appointment_reminder(appointment):
    """
    Отправка напоминания за день до приема.
    """
    try:
        subject = "Напоминание о записи в ветеринарную клинику Dr. Хвост"
        from_email = "drhvost.vetclinic@gmail.com"

        # Получатели — и пользователь, и врач
        to = [
            appointment.pet.owner.email,  # email пользователя
            appointment.vet.user.email    # email врача
        ]

        context = {
            'pet_name': appointment.pet.name,
            'date': appointment.date,
            'time': appointment.time.strftime('%H:%M'),
            'vet_name': appointment.vet.name,
            'owner_name': appointment.pet.owner.get_full_name() or appointment.pet.owner.username,
        }

        text_content = render_to_string('clinic/email/appointment_reminder.txt', context)
        html_content = render_to_string('clinic/email/appointment_reminder.html', context)

        msg = EmailMultiAlternatives(subject, text_content, from_email, to)
        msg.attach_alternative(html_content, "text/html")

        msg.send(fail_silently=False)  # Ожидаем ошибок, если что-то пойдет не так
        logger.info(f"Reminder email sent to {', '.join(to)}")  # Логируем успешную отправку
    except Exception as e:
        logger.error(f"Error sending reminder email: {e}")
        raise
