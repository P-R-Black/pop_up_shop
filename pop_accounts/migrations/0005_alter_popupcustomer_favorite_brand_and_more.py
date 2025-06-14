# Generated by Django 5.1.3 on 2025-05-29 17:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pop_accounts', '0004_alter_popupcustomer_favorite_brand_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='popupcustomer',
            name='favorite_brand',
            field=models.CharField(choices=[('adidas', 'Adidas'), ('Asics', 'asics'), ('balenciaga', 'Balenciaga'), ('brooks', 'Brooks'), ('fear_of_god ', 'Fear of God'), ('gucci', 'Gucci'), ('jordan', 'Jordan'), ('new_balance', 'New Balance'), ('nike', 'Nike'), ('prada', 'Prada'), ('puma', 'Puma'), ('reebok', 'Reebok'), ('saucony', 'Saucony'), ('yeezy', 'Yeezy')], default='nike', max_length=100),
        ),
        migrations.AlterField(
            model_name='popupcustomeraddress',
            name='prefix',
            field=models.CharField(blank=True, choices=[('mr', 'Mr.'), ('mrs', 'Mrs.'), ('ms', 'Ms.'), ('miss', 'Miss.'), ('dr', 'Dr.'), ('prof', 'Prof.')], default='', max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='popupcustomeraddress',
            name='suffix',
            field=models.CharField(blank=True, choices=[('jr', 'Jr.'), ('sr', 'Sr.'), ('ii', 'II'), ('iii', 'III'), ('iv', 'IV'), ('cpa', 'CPA'), ('md', 'M.D.'), ('PhD', 'PhD.')], default='', max_length=10, null=True),
        ),
    ]
