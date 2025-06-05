from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('doctors/', views.doctors, name='doctors'),
    path('contacts/', views.contacts, name='contacts'),
    path('profile/', views.profile_dashboard, name='profile'),
    path('vet-profile/', views.vet_profile, name='vet_profile'),
    path('booking/', views.booking, name='booking'),
    path('add-pet/', views.add_pet, name='add_pet'),
    path('get-available-times/', views.get_available_times, name='get_available_times'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='clinic/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/edit-pet/<int:pet_id>/', views.edit_pet, name='edit_pet'),
    path('profile/delete-pet/<int:pet_id>/', views.delete_pet, name='delete_pet'),
    path('appointments/create/', views.create_appointment, name='create_appointment'),
    path('appointments/<int:appointment_id>/cancel/', views.cancel_appointment, name='cancel_appointment'),
    path('blog/', views.blog_list, name='blog_list'),
    path('blog/create/', views.blog_create, name='blog_create'),
    path('blog/<int:post_id>/', views.blog_detail, name='blog_detail'),
    path('blog/<int:post_id>/edit/', views.blog_edit, name='blog_edit'),
    path('profile/dashboard/', views.profile_dashboard, name='profile_dashboard'),
    path('profile/tab/info/', views.profile_info_tab, name='profile_info_tab'),
    path('profile/tab/pets/', views.profile_pets_tab, name='profile_pets_tab'),
    path('profile/tab/upcoming/', views.profile_upcoming_tab, name='profile_upcoming_tab'),
    path('profile/tab/history/', views.profile_history_tab, name='profile_history_tab'),
    path('profile/change-password/', views.profile_change_password, name='profile_change_password'),
    path('profile/reset-password/', auth_views.PasswordResetView.as_view(template_name='clinic/password_reset_form.html'), name='profile_reset_password'),
    path('profile/reset-password/done/', auth_views.PasswordResetDoneView.as_view(template_name='clinic/password_reset_done.html'), name='password_reset_done'),
    path('profile/reset-password/confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='clinic/password_reset_confirm.html'), name='password_reset_confirm'),
    path('profile/reset-password/complete/', auth_views.PasswordResetCompleteView.as_view(template_name='clinic/password_reset_complete.html'), name='password_reset_complete'),
    path('profile/change-username/', views.change_username, name='change_username'),
    path('profile/change-email/', views.change_email, name='change_email'),
]

