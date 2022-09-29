# Generated by Django 4.1.1 on 2022-09-29 09:45

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dealership', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('isActive', models.BooleanField(verbose_name='Is Active')),
                ('firstName', models.CharField(max_length=50, verbose_name='First Name')),
                ('lastName', models.CharField(max_length=50, verbose_name='Last Name')),
                ('email', models.CharField(max_length=50, verbose_name='Email')),
                ('dealership', models.ManyToManyField(related_name='userprofile_dealership_id', to='dealership.dealership')),
                ('user', models.ManyToManyField(related_name='userprofile_user_id', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]