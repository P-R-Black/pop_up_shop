# Generated by Django 5.1.3 on 2025-06-25 00:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auction', '0004_alter_winnerreservation_unique_together_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='popupproduct',
            name='buy_now_end',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='popupproduct',
            name='buy_now_start',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
