# Generated by Django 3.2.3 on 2021-05-17 20:49

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('commandes', '0002_panier_price'),
    ]

    operations = [
        migrations.AlterField(
            model_name='panier',
            name='quantity',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(1)], verbose_name='Quantité'),
        ),
    ]
