# Generated by Django 3.2.12 on 2022-03-28 12:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myprofile', '0002_alter_inventory_itemcount'),
    ]

    operations = [
        migrations.AddField(
            model_name='orders',
            name='dateCreated',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='orders',
            name='dateModified',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
    ]
