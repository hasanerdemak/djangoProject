# Generated by Django 4.1.1 on 2022-11-11 09:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dealership', '0004_alter_dealership_group'),
        ('category', '0003_alter_associatedcategory_category_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='associatedcategory',
            name='category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='associated_categories', to='category.category', verbose_name='Category'),
        ),
        migrations.AlterField(
            model_name='associatedcategory',
            name='dealership',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='associated_categories', to='dealership.dealership', verbose_name='Dealership'),
        ),
    ]
