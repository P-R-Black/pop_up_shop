# Generated by Django 5.1.3 on 2025-05-17 00:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pop_accounts', '0009_alter_popupcustomer_favorite_brand'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='popuppasswordresetrequestlog',
            options={'verbose_name': 'PopUpPasswordResetRequestLog', 'verbose_name_plural': 'PopUpPasswordResetRequestLog'},
        ),
        migrations.RemoveField(
            model_name='popupcustomer',
            name='open_bids',
        ),
        migrations.RemoveField(
            model_name='popupcustomer',
            name='past_bids',
        ),
    ]
