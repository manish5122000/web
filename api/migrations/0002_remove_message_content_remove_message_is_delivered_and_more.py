# Generated by Django 5.1.1 on 2024-09-25 09:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='message',
            name='content',
        ),
        migrations.RemoveField(
            model_name='message',
            name='is_delivered',
        ),
        migrations.RemoveField(
            model_name='message',
            name='is_read',
        ),
        migrations.RemoveField(
            model_name='message',
            name='room',
        ),
        migrations.RemoveField(
            model_name='message',
            name='sender',
        ),
    ]
