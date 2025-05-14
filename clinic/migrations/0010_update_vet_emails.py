from django.db import migrations

def update_vet_emails(apps, schema_editor):
    Vet = apps.get_model('clinic', 'Vet')
    
    # Обновляем email для Айгель Ташетовой
    Vet.objects.filter(last_name='Ташетова', first_name='Айгель').update(
        email='aigul.tashetova.vetclinic@gmail.com'
    )
    
    # Обновляем email для остальных врачей
    vets = Vet.objects.exclude(last_name='Ташетова', first_name='Айгель')
    for vet in vets:
        if not vet.email:
            vet.email = f"{vet.first_name.lower()}.{vet.last_name.lower()}@drhvost.kz"
            vet.save()

class Migration(migrations.Migration):
    dependencies = [
        ('clinic', '0009_delete_service'),
    ]

    operations = [
        migrations.RunPython(update_vet_emails),
    ] 