# Generated by Django 4.1.1 on 2022-11-16 15:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dealership', '0004_alter_dealership_group'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dealership',
            name='group',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.DO_NOTHING, related_name='dealerships', to='dealership.dealershipgroup', verbose_name='Dealership Group'),
        ),
    ]
