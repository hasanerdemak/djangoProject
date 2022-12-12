# Generated by Django 4.1.1 on 2022-12-09 09:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dealership', '0007_alter_dealership_group'),
        ('category', '0006_associatedcategory_is_active'),
    ]

    operations = [
        migrations.AlterField(
            model_name='associatedcategory',
            name='category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='associated_categories', to='category.category', verbose_name='Category'),
        ),
        migrations.AlterField(
            model_name='associatedcategory',
            name='dealership',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='associated_categories', to='dealership.dealership', verbose_name='Dealership'),
        ),
    ]