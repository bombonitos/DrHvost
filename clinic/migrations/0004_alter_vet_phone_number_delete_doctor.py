# Generated by Django 5.2 on 2025-05-09 00:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clinic', '0003_doctor'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vet',
            name='phone_number',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.DeleteModel(
            name='Doctor',
        ),
    ]
