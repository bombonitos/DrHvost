from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django import forms
from .models import Pet, Appointment, Vet, BlogPost
from datetime import date, time

class RegisterForm(UserCreationForm):
    email = forms.EmailField()
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class PetForm(forms.ModelForm):
    class Meta:
        model = Pet
        fields = ['name', 'species', 'gender', 'breed', 'age', 'owner_name', 'contact_phone']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'species': forms.Select(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'breed': forms.TextInput(attrs={'class': 'form-control'}),
            'age': forms.NumberInput(attrs={'class': 'form-control'}),
            'owner_name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
        }

class AppointmentForm(forms.ModelForm):
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user  # Сохраняем пользователя
        self.fields['pet'].queryset = Pet.objects.filter(owner=user)
        self.fields['vet'].queryset = Vet.objects.filter(available=True)
        self.fields['date'].widget = forms.DateInput(attrs={'type': 'date', 'min': date.today().isoformat()})
        self.fields['description'].widget = forms.Textarea(attrs={'rows': 4})
        
        # Настраиваем поле времени
        self.fields['time'].widget = forms.Select(attrs={'class': 'form-control'})
        self.fields['time'].choices = [(t.strftime('%H:%M'), d) for t, d in Appointment.TIME_CHOICES]

    class Meta:
        model = Appointment
        fields = ['pet', 'vet', 'date', 'time', 'description']
        widgets = {
            'pet': forms.Select(attrs={'class': 'form-control'}),
            'vet': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        vet = cleaned_data.get('vet')
        appointment_date = cleaned_data.get('date')
        appointment_time = cleaned_data.get('time')

        if vet and appointment_date and appointment_time:
            # Проверяем, есть ли уже запись на это время
            existing_appointment = Appointment.objects.filter(
                vet=vet,
                date=appointment_date,
                time=appointment_time,
                status='pending'  # Проверяем только активные записи
            ).exists()

            if existing_appointment:
                raise forms.ValidationError('Это время уже занято. Пожалуйста, выберите другое время.')

        return cleaned_data

    def clean_pet(self):
        pet = self.cleaned_data['pet']
        if pet.owner != self.user:
            raise forms.ValidationError('Вы не можете записать чужого питомца.')
        return pet

class VetLoginForm(AuthenticationForm):
    username = forms.CharField(label='Логин', widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput(attrs={'class': 'form-control'}))

class BlogPostForm(forms.ModelForm):
    class Meta:
        model = BlogPost
        fields = ['title', 'content', 'image']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите заголовок статьи'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Введите содержание статьи', 'rows': 10}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }
