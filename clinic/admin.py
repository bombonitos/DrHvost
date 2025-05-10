from django.contrib import admin
from .models import Pet, Appointment, Vet

@admin.register(Vet)
class VetAdmin(admin.ModelAdmin):
    list_display = ('name', 'specialty', 'available')
    list_filter = ('specialty', 'available')
    search_fields = ('first_name', 'last_name', 'specialty')

@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):
    list_display = ('name', 'species', 'breed', 'age', 'owner_name', 'contact_phone')
    list_filter = ('species', 'gender')
    search_fields = ('name', 'owner_name', 'contact_phone')

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('pet', 'vet', 'date', 'time', 'status')
    list_filter = ('date', 'status', 'vet')
    search_fields = ('pet__name', 'vet__name', 'description')