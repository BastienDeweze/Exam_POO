# Generated by Django 3.2.3 on 2021-06-04 09:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('articles', '0007_article_thumbnail'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article',
            name='thumbnail',
            field=models.ImageField(blank=True, default='mediafiles\\articles\\logo.png', upload_to='articles'),
        ),
    ]
