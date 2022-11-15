# Generated by Django 4.1.1 on 2022-10-26 10:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('dealership', '0002_alter_dealership_group'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='Category Name')),
            ],
        ),
        migrations.CreateModel(
            name='AssociatedCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='category.category', verbose_name='Category')),
                ('dealership', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dealership.dealership', verbose_name='Dealership')),
            ],
        ),
    ]