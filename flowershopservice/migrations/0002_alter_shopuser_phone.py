# Generated by Django 5.1.7 on 2025-03-29 10:15

import phone_field.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('flowershopservice', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shopuser',
            name='phone',
            field=phone_field.models.PhoneField(blank=True, help_text='Телефон', max_length=31, unique=True),
        ),
    ]
