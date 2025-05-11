from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .forms import RegisterForm, PetForm, AppointmentForm
from .models import Pet, Appointment, Vet
from datetime import datetime
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def home(request):
    vets = Vet.objects.filter(available=True)
    return render(request, 'clinic/home.html', {'vets': vets})

def about(request):
    return render(request, 'about.html')

def doctors(request):
    vets = Vet.objects.filter(available=True)
    specialties = Vet.objects.filter(available=True).values_list('specialty', flat=True).distinct()
    return render(request, 'doctors.html', {
        'vets': vets,
        'specialties': specialties
    })

def contacts(request):
    return render(request, 'contacts.html')

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            logger.info(f'Создан новый пользователь: {user.username}')
            login(request, user)
            return redirect('home')
    else:
        form = RegisterForm()
    return render(request, 'clinic/register.html', {'form': form})

@login_required
def logout_view(request):
    if request.method == 'POST':
        logout(request)
        messages.success(request, 'Вы успешно вышли из системы.')
        return redirect('home')
    return render(request, 'clinic/logout.html')

@login_required
def profile(request):
    pets = Pet.objects.filter(owner=request.user)
    appointments = Appointment.objects.filter(pet__owner=request.user).order_by('-date', '-time')
    now = datetime.now()

    upcoming_appointments = []
    past_appointments = []

    for appointment in appointments:
        if appointment.date > now.date() or (appointment.date == now.date() and appointment.time > now.time()):
            upcoming_appointments.append(appointment)
        else:
            past_appointments.append(appointment)

    return render(request, 'clinic/profile.html', {
        'pets': pets,
        'upcoming_appointments': upcoming_appointments,
        'past_appointments': past_appointments,
        'vets': Vet.objects.filter(available=True),
        'now': now
    })

@login_required
def add_pet(request):
    if request.method == 'POST':
        form = PetForm(request.POST)
        if form.is_valid():
            pet = form.save(commit=False)
            pet.owner = request.user
            pet.save()
            messages.success(request, 'Питомец успешно добавлен!')
            return redirect('profile')
    else:
        form = PetForm()
    return render(request, 'clinic/add_pet.html', {'form': form})

@login_required
def edit_pet(request, pet_id):
    pet = get_object_or_404(Pet, id=pet_id, owner=request.user)
    if request.method == 'POST':
        form = PetForm(request.POST, instance=pet)
        if form.is_valid():
            form.save()
            messages.success(request, 'Информация о питомце обновлена!')
            return redirect('profile')
    else:
        form = PetForm(instance=pet)
    return render(request, 'clinic/edit_pet.html', {'form': form, 'pet': pet})

@login_required
def delete_pet(request, pet_id):
    pet = get_object_or_404(Pet, id=pet_id, owner=request.user)
    if request.method == 'POST':
        pet.delete()
        messages.success(request, 'Питомец удален из вашего профиля.')
        return redirect('profile')
    return render(request, 'clinic/delete_pet.html', {'pet': pet})

@login_required
def booking(request):
    if request.method == 'POST':
        form = AppointmentForm(request.user, request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.pet = form.cleaned_data['pet']
            appointment.vet = form.cleaned_data['vet']
            appointment.save()


            from datetime import datetime, timedelta
            from django.utils.timezone import make_aware
            from clinic.tasks import send_appointment_reminder

            # дата и время приема
            appointment_datetime = datetime.combine(appointment.date, appointment.time)
            reminder_time = make_aware(appointment_datetime - timedelta(days=1))  # за 24 часа до

            # планируем задачу
            send_appointment_reminder.apply_async(
                args=[appointment.id],
                eta=reminder_time
            )


            # Получаем email пользователя и отправляем подтверждение
            user_email = request.user.email
            send_appointment_confirmation(user_email, appointment)

            logger.info(f"Создана новая запись: {appointment.date} {appointment.time} - {appointment.pet.name} к врачу {appointment.vet.name}")
            messages.success(request, 'Запись успешно создана!')
            return redirect('profile')
        else:
            logger.error(f"Ошибка валидации формы: {form.errors}")
    else:
        form = AppointmentForm(request.user)

    return render(request, 'clinic/booking.html', {
        'form': form,
        'vets': Vet.objects.filter(available=True)
    })

def send_appointment_confirmation(user_email, appointment):
    """Отправка письма с подтверждением записи"""
    subject = 'Подтверждение записи на прием'
    message = f'''
Здравствуйте!

Вы успешно записались на прием в нашу ветеринарную клинику. Ниже указаны детали вашей записи:

📅 Дата: {appointment.date.strftime("%d.%m.%Y")}
⏰ Время: {appointment.time.strftime("%H:%M")}
👩‍⚕️ Врач: {appointment.vet.name}
🐾 Питомец: {appointment.pet.name}

Если у вас возникнут вопросы или потребуется перенести запись, пожалуйста, свяжитесь с нами заранее.

С уважением,  
Команда ветеринарной клиники DrHvost
'''
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [user_email]

    try:
        send_mail(subject, message, from_email, recipient_list, fail_silently=False)
    except Exception as e:
        logger.error(f"Ошибка при отправке письма: {e}")
        raise


@login_required
def get_available_times(request):
    vet_id = request.GET.get('vet_id')
    date_str = request.GET.get('date')

    if not vet_id or not date_str:
        return JsonResponse({'error': 'Не указан врач или дата'}, status=400)

    try:
        vet = Vet.objects.get(id=vet_id)
        appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()

        booked_times = Appointment.objects.filter(
            vet=vet,
            date=appointment_date
        ).values_list('time', flat=True)

        all_times = Appointment.TIME_CHOICES

        available_times = []
        for time_obj, display_time in all_times:
            if time_obj not in booked_times:
                available_times.append({
                    'value': time_obj.strftime('%H:%M'),
                    'display': display_time
                })

        return JsonResponse({'available_times': available_times})

    except Exception as e:
        logger.error(f"Ошибка в get_available_times: {str(e)}")
        return JsonResponse({'error': 'Ошибка при получении доступного времени'}, status=500)

@login_required
def vet_profile(request):
    try:
        vet = Vet.objects.filter(user=request.user).first()
        if not vet:
            messages.error(request, 'У вас нет доступа к профилю врача.')
            return redirect('home')

        now = datetime.now()
        appointments = Appointment.objects.filter(vet=vet).order_by('date', 'time')

        upcoming = []
        past = []
        for appt in appointments:
            if appt.date > now.date() or (appt.date == now.date() and appt.time > now.time()):
                upcoming.append(appt)
            else:
                past.append(appt)

        upcoming_by_date = {}
        past_by_date = {}
        for appt in upcoming:
            upcoming_by_date.setdefault(appt.date, []).append(appt)
        for appt in past:
            past_by_date.setdefault(appt.date, []).append(appt)

        return render(request, 'clinic/vet_profile.html', {
            'vet': vet,
            'upcoming_appointments': upcoming,
            'past_appointments': past,
            'upcoming_by_date': upcoming_by_date,
            'past_by_date': past_by_date
        })
    except Exception as e:
        logger.error(f"Ошибка в vet_profile: {str(e)}")
        messages.error(request, 'Ошибка при загрузке профиля врача.')
        return redirect('home')

@login_required
def create_appointment(request):
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.patient = request.user
            appointment.save()
            messages.success(request, 'Вы успешно записались на прием!')
            return redirect('appointments')
    else:
        form = AppointmentForm()
    return render(request, 'clinic/create_appointment.html', {'form': form})
