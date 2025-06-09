from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .forms import RegisterForm, PetForm, AppointmentForm, BlogPostForm, VetLoginForm, ChangeUsernameForm, ChangeEmailForm, AvatarUploadForm
from .models import Pet, Appointment, Vet, BlogPost, UserProfile
from datetime import datetime
from django.core.mail import send_mail, EmailMultiAlternatives
from email.mime.image import MIMEImage
from django.conf import settings
import logging
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)

def home(request):
    vets = Vet.objects.all()
    recommended_posts = BlogPost.objects.order_by('-created_at')[:3]  # Получаем 3 последние статьи
    return render(request, 'clinic/home.html', {
        'vets': vets,
        'recommended_posts': recommended_posts
    })

def about(request):
    return render(request, 'clinic/about.html')

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
    if not request.user.is_authenticated:
        return redirect('login')
    
    pets = Pet.objects.filter(owner=request.user)
    # Получаем все записи пользователя, включая отмененные
    appointments = Appointment.objects.filter(pet__owner=request.user).order_by('-date', '-time')
    
    # Добавляем отладочную информацию
    logger.info(f"Найдено записей: {appointments.count()}")
    for appt in appointments:
        logger.info(f"Запись {appt.id}: дата={appt.date}, время={appt.time}, статус={appt.status}")
    
    upcoming_appointments = []
    past_appointments = []
    now = datetime.now()
    
    for appointment in appointments:
        # Если запись в будущем или сегодня, добавляем в предстоящие
        if appointment.date > now.date() or (appointment.date == now.date() and appointment.time > now.time()):
            upcoming_appointments.append(appointment)
            logger.info(f"Добавлена предстоящая запись {appointment.id} со статусом {appointment.status}")
        else:
            # Если запись в прошлом и её статус 'pending', меняем на 'completed'
            if appointment.status == 'pending':
                appointment.status = 'completed'
                appointment.save()
            past_appointments.append(appointment)
            logger.info(f"Добавлена прошедшая запись {appointment.id} со статусом {appointment.status}")
    
    # Группируем записи по датам
    upcoming_by_date = {}
    past_by_date = {}
    
    # Добавляем все предстоящие записи в группу, включая отмененные
    for appointment in upcoming_appointments:
        date_key = appointment.date
        if date_key not in upcoming_by_date:
            upcoming_by_date[date_key] = []
        upcoming_by_date[date_key].append(appointment)
        logger.info(f"Запись {appointment.id} добавлена в upcoming_by_date для даты {date_key}")
    
    # Добавляем все прошедшие записи в группу
    for appointment in past_appointments:
        date_key = appointment.date
        if date_key not in past_by_date:
            past_by_date[date_key] = []
        past_by_date[date_key].append(appointment)
        logger.info(f"Запись {appointment.id} добавлена в past_by_date для даты {date_key}")
    
    # Сортируем даты
    upcoming_by_date = dict(sorted(upcoming_by_date.items()))
    past_by_date = dict(sorted(past_by_date.items(), reverse=True))
    
    context = {
        'pets': pets,
        'upcoming_appointments': upcoming_appointments,
        'past_appointments': past_appointments,
        'upcoming_by_date': upcoming_by_date,
        'past_by_date': past_by_date,
        'vets': Vet.objects.filter(available=True),
        'now': now
    }
    
    return render(request, 'clinic/profile.html', context)

@login_required
def add_pet(request):
    if request.method == 'POST':
        form = PetForm(request.POST, request.FILES)
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
        form = PetForm(request.POST, request.FILES, instance=pet)
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
    """Отправка писем с подтверждением записи пациенту и врачу"""
    logger.info(f"Начало отправки писем для записи {appointment.id}")
    
    # Отправка письма пациенту
    subject = 'Подтверждение записи на прием'
    
    # Создаем сообщение
    msg = EmailMultiAlternatives(
        subject=subject,
        body='',  # Пустое тело, так как используем HTML
        from_email=settings.EMAIL_HOST_USER,
        to=[user_email]
    )
    
    # Прикрепляем изображение
    with open('static/images/confirmation.png', 'rb') as f:
        image = MIMEImage(f.read())
        image.add_header('Content-ID', '<confirmation_image>')
        msg.attach(image)
    
    # Рендерим HTML шаблон
    html_content = render_to_string('clinic/email/appointment_confirmation.html', {
        'appointment': appointment
    })
    msg.attach_alternative(html_content, "text/html")
    
    try:
        logger.info(f"Отправка письма пациенту на адрес {user_email}")
        msg.send(fail_silently=False)
        logger.info("Письмо пациенту успешно отправлено")
    except Exception as e:
        logger.error(f"Ошибка при отправке письма пациенту: {e}")

    # Отправка письма врачу
    if appointment.vet.email:
        logger.info(f"Подготовка письма для врача {appointment.vet.name} на адрес {appointment.vet.email}")
        vet_subject = 'Новая запись на приём'
        
        # Создаем сообщение для врача
        vet_msg = EmailMultiAlternatives(
            subject=vet_subject,
            body='',  # Пустое тело, так как используем HTML
            from_email=settings.EMAIL_HOST_USER,
            to=[appointment.vet.email]
        )
        
        # Прикрепляем изображение
        with open('static/images/vet_notification.png', 'rb') as f:
            image = MIMEImage(f.read())
            image.add_header('Content-ID', '<vet_notification_image>')
            vet_msg.attach(image)
        
        # Рендерим HTML шаблон
        vet_html_content = render_to_string('clinic/email/vet_appointment_notification.html', {
            'appointment': appointment
        })
        vet_msg.attach_alternative(vet_html_content, "text/html")

        try:
            logger.info(f"Отправка письма врачу на адрес {appointment.vet.email}")
            vet_msg.send(fail_silently=False)
            logger.info("Письмо врачу успешно отправлено")
        except Exception as e:
            logger.error(f"Ошибка при отправке письма врачу: {e}")
    else:
        logger.warning(f"У врача {appointment.vet.name} не указан email адрес")

def send_appointment_reminder(appointment):
    """Отправка напоминания о приеме"""
    subject = 'Напоминание о приеме'
    
    # Создаем сообщение
    msg = EmailMultiAlternatives(
        subject=subject,
        body='',  # Пустое тело, так как используем HTML
        from_email=settings.EMAIL_HOST_USER,
        to=[appointment.pet.owner.email]
    )
    
    # Прикрепляем изображение
    with open('static/images/reminder.png', 'rb') as f:
        image = MIMEImage(f.read())
        image.add_header('Content-ID', '<reminder_image>')
        msg.attach(image)
    
    # Рендерим HTML шаблон
    html_content = render_to_string('clinic/email/appointment_reminder.html', {
        'appointment': appointment
    })
    msg.attach_alternative(html_content, "text/html")
    
    try:
        msg.send(fail_silently=False)
        logger.info(f"Напоминание о приеме {appointment.id} успешно отправлено")
    except Exception as e:
        logger.error(f"Ошибка при отправке напоминания о приеме {appointment.id}: {e}")

@login_required
def get_available_times(request):
    vet_id = request.GET.get('vet_id')
    date_str = request.GET.get('date')

    if not vet_id or not date_str:
        return JsonResponse({'error': 'Не указан врач или дата'}, status=400)

    try:
        vet = Vet.objects.get(id=vet_id)
        appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()

        # Получаем только активные записи (со статусом pending)
        booked_times = Appointment.objects.filter(
            vet=vet,
            date=appointment_date,
            status='pending'  # Добавляем фильтр по статусу
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
        # Проверяем, является ли пользователь врачом
        if not hasattr(request.user, 'vet'):
            messages.error(request, 'У вас нет доступа к профилю врача.')
            return redirect('home')

        vet = request.user.vet
        now = datetime.now()
        
        # Получаем все записи (включая отмененные)
        appointments = Appointment.objects.filter(vet=vet).order_by('date', 'time')

        upcoming = []
        past = []
        pending_count = 0  # Счетчик для предстоящих записей со статусом "ожидает"
        
        for appt in appointments:
            if appt.date > now.date() or (appt.date == now.date() and appt.time > now.time()):
                upcoming.append(appt)
                if appt.status == 'pending':
                    pending_count += 1
            else:
                # Если запись в прошлом и её статус 'pending', меняем на 'completed'
                if appt.status == 'pending':
                    appt.status = 'completed'
                    appt.save()
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
            'past_by_date': past_by_date,
            'pending_count': pending_count  # Передаем количество предстоящих записей
        })
    except Exception as e:
        logger.error(f"Ошибка в vet_profile: {str(e)}")
        messages.error(request, 'Ошибка при загрузке профиля врача.')
        return redirect('home')

@login_required
def create_appointment(request):
    if request.method == 'POST':
        form = AppointmentForm(request.user, request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.save()
            messages.success(request, 'Вы успешно записались на прием!')
            return redirect('profile')
    else:
        form = AppointmentForm(request.user)
    return render(request, 'clinic/create_appointment.html', {'form': form})

def blog_list(request):
    search_query = request.GET.get('search', '')
    if search_query:
        posts = BlogPost.objects.filter(title__icontains=search_query)
    else:
        posts = BlogPost.objects.all()
    return render(request, 'clinic/blog/list.html', {'posts': posts})

def blog_detail(request, post_id):
    post = get_object_or_404(BlogPost, id=post_id)
    return render(request, 'clinic/blog/detail.html', {'post': post})

@login_required
def blog_create(request):
    if not hasattr(request.user, 'vet'):
        messages.error(request, 'Только ветеринары могут создавать статьи')
        return redirect('blog_list')
    
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user.vet
            post.save()
            messages.success(request, 'Статья успешно создана')
            return redirect('blog_list')
    else:
        form = BlogPostForm()
    
    return render(request, 'clinic/blog/create.html', {'form': form})

@login_required
def blog_edit(request, post_id):
    post = get_object_or_404(BlogPost, id=post_id)
    
    # Проверяем, что пользователь является автором статьи
    if not request.user.vet or request.user.vet != post.author:
        messages.error(request, 'У вас нет прав для редактирования этой статьи')
        return redirect('blog_detail', post_id=post.id)
    
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, 'Статья успешно обновлена')
            return redirect('blog_detail', post_id=post.id)
    else:
        form = BlogPostForm(instance=post)
    
    return render(request, 'clinic/blog/edit.html', {
        'form': form,
        'post': post
    })

@login_required
def cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Проверяем, что пользователь является владельцем питомца
    if appointment.pet.owner != request.user:
        messages.error(request, 'У вас нет прав для отмены этой записи')
        return redirect('profile')
    
    if request.method == 'POST':
        try:
            appointment.status = 'cancelled'
            appointment.save()
            logger.info(f"Запись {appointment_id} отменена. Статус: {appointment.status}")
            messages.success(request, 'Запись успешно отменена')
        except Exception as e:
            logger.error(f"Ошибка при отмене записи {appointment_id}: {str(e)}")
            messages.error(request, 'Произошла ошибка при отмене записи')
        return redirect('profile')
    
    return render(request, 'clinic/cancel_appointment.html', {'appointment': appointment})

@login_required
def profile_info_tab(request):
    if request.method == 'POST' and request.FILES.get('avatar'):
        form = AvatarUploadForm(request.POST, request.FILES, instance=request.user.userprofile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Аватар успешно обновлен!')
            return redirect('profile')
        else:
            messages.error(request, 'Ошибка при загрузке аватара')
    else:
        form = AvatarUploadForm(instance=request.user.userprofile)
    
    return render(request, 'clinic/profile_tab_info.html', {'form': form})

@login_required
@require_GET
def profile_pets_tab(request):
    pets = request.user.pets.all()
    return render(request, 'clinic/profile_tab_pets.html', {'pets': pets})

@login_required
@require_GET
def profile_upcoming_tab(request):
    from datetime import datetime
    now = datetime.now()
    upcoming_appointments = []
    
    for pet in request.user.pets.all():
        for appointment in pet.appointments.filter(
            date__gte=now.date()
        ).order_by('date', 'time'):
            # Добавляем запись, если она в будущем или сегодня
            if appointment.date > now.date() or (appointment.date == now.date() and appointment.time > now.time()):
                upcoming_appointments.append(appointment)
    
    return render(request, 'clinic/profile_tab_upcoming.html', {
        'upcoming_appointments': upcoming_appointments
    })

@login_required
@require_GET
def profile_history_tab(request):
    from datetime import datetime
    now = datetime.now()
    past_appointments = []
    for pet in request.user.pets.all():
        for appointment in pet.appointments.filter(status__in=['completed', 'cancelled']).order_by('-date', '-time'):
            if appointment.status in ['completed', 'cancelled'] and (appointment.date < now.date() or (appointment.date == now.date() and appointment.time <= now.time())):
                past_appointments.append(appointment)
    return render(request, 'clinic/profile_tab_history.html', {'past_appointments': past_appointments})

@login_required
def profile_dashboard(request):
    return render(request, 'clinic/profile_dashboard.html')

@login_required
def profile_change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Пароль успешно изменён.')
            return redirect('profile')
        else:
            messages.error(request, 'Ошибка при смене пароля. Проверьте правильность введённых данных.')
    else:
        form = PasswordChangeForm(user=request.user)
    
    return render(request, 'clinic/change_password.html', {'form': form})

@login_required
def change_username(request):
    if request.method == 'POST':
        form = ChangeUsernameForm(request.POST)
        if form.is_valid():
            user = request.user
            password = form.cleaned_data['password']
            new_username = form.cleaned_data['new_username']
            
            # Проверяем текущий пароль
            if user.check_password(password):
                user.username = new_username
                user.save()
                messages.success(request, 'Логин успешно изменен')
                return redirect('profile')
            else:
                form.add_error('password', 'Неверный пароль')
    else:
        form = ChangeUsernameForm()
    
    return render(request, 'clinic/change_username.html', {'form': form})

@login_required
def change_email(request):
    if request.method == 'POST':
        form = ChangeEmailForm(request.POST)
        if form.is_valid():
            user = request.user
            password = form.cleaned_data['password']
            new_email = form.cleaned_data['new_email']
            
            # Проверяем текущий пароль
            if user.check_password(password):
                user.email = new_email
                user.save()
                messages.success(request, 'Email успешно изменен')
                return redirect('profile')
            else:
                form.add_error('password', 'Неверный пароль')
    else:
        form = ChangeEmailForm()
    
    return render(request, 'clinic/change_email.html', {'form': form})

def test_email(request):
    try:
        subject = 'Тестовое письмо'
        message = 'Это тестовое письмо для проверки настроек SMTP.'
        from_email = settings.EMAIL_HOST_USER
        recipient_list = ['bombonitos@yandex.ru']
        
        logger.info(f"Попытка отправки письма на {recipient_list}")
        
        send_mail(
            subject,
            message,
            from_email,
            recipient_list,
            fail_silently=False,
        )
        
        logger.info("Письмо успешно отправлено")
        return JsonResponse({'status': 'success', 'message': 'Письмо отправлено'})
    except Exception as e:
        logger.error(f"Ошибка при отправке письма: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)})

@login_required
def upload_avatar(request):
    if request.method == 'POST':
        form = AvatarUploadForm(request.POST, request.FILES, instance=request.user.userprofile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Аватар успешно обновлен!')
            return redirect('profile')
    else:
        form = AvatarUploadForm(instance=request.user.userprofile)
    
    return render(request, 'clinic/profile_tab_info.html', {
        'form': form,
        'show_upload_form': True
    })

@login_required
def delete_account(request):
    if request.method == 'POST':
        password = request.POST.get('password')
        if request.user.check_password(password):
            # Удаляем все связанные данные
            Pet.objects.filter(owner=request.user).delete()
            Appointment.objects.filter(pet__owner=request.user).delete()
            UserProfile.objects.filter(user=request.user).delete()
            
            # Удаляем пользователя
            user = request.user
            logout(request)
            user.delete()
            
            messages.success(request, 'Ваш аккаунт успешно удален.')
            return redirect('home')
        else:
            messages.error(request, 'Неверный пароль.')
    
    return render(request, 'clinic/delete_account.html')

@login_required
def vet_cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Проверяем, что пользователь является врачом и это его запись
    if not hasattr(request.user, 'vet') or appointment.vet != request.user.vet:
        messages.error(request, 'У вас нет прав для отмены этой записи')
        return redirect('vet_profile')
    
    if request.method == 'POST':
        appointment.status = 'cancelled'
        appointment.save()
        
        # Отправляем уведомление владельцу питомца
        try:
            subject = 'Отмена записи на приём'
            message = f'''
Здравствуйте!

Ваша запись на приём была отменена врачом.

Детали записи:
📅 Дата: {appointment.date.strftime("%d.%m.%Y")}
⏰ Время: {appointment.time.strftime("%H:%M")}
👩‍⚕️ Врач: {appointment.vet.name}
🐾 Питомец: {appointment.pet.name}

Если у вас возникли вопросы, пожалуйста, свяжитесь с нами.

С уважением,  
Команда ветеринарной клиники DrHvost
'''
            from_email = settings.EMAIL_HOST_USER
            recipient_list = [appointment.pet.owner.email]
            
            send_mail(subject, message, from_email, recipient_list, fail_silently=False)
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления об отмене записи: {e}")
        
        messages.success(request, 'Запись успешно отменена')
        return redirect('vet_profile')
    
    return redirect('vet_profile')
