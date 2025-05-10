from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('doctors/', views.doctors, name='doctors'),
    path('contacts/', views.contacts, name='contacts'),
    path('profile/', views.profile, name='profile'),
    path('vet-profile/', views.vet_profile, name='vet_profile'),
    path('booking/', views.booking, name='booking'),
    path('add-pet/', views.add_pet, name='add_pet'),
    path('get-available-times/', views.get_available_times, name='get_available_times'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='clinic/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/edit-pet/<int:pet_id>/', views.edit_pet, name='edit_pet'),
    path('profile/delete-pet/<int:pet_id>/', views.delete_pet, name='delete_pet'),
]
