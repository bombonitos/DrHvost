from django.db import migrations

def update_tashetova_email(apps, schema_editor):
    Vet = apps.get_model('clinic', 'Vet')
    Vet.objects.filter(last_name='Ташетова', first_name='Айгуль').update(
        email='aigul.tashetova.vetclinic@gmail.com'
    )

class Migration(migrations.Migration):
    dependencies = [
        ('clinic', '0010_update_vet_emails'),
    ]

    operations = [
        migrations.RunPython(update_tashetova_email),
    ] 