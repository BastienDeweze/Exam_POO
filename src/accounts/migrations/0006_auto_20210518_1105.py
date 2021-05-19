# Generated by Django 3.2.3 on 2021-05-18 09:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_delete_useraccount'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='city',
            field=models.CharField(default='0000', max_length=4, verbose_name='zip code'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='reduction_threshold',
            field=models.IntegerField(default=10, verbose_name='Seuil de réduction'),
        ),
    ]
