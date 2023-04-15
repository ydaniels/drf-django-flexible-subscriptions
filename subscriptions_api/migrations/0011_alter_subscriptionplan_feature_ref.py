# Generated by Django 4.1 on 2023-02-16 09:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions_api', '0010_plancost_min_subscription_quantity'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subscriptionplan',
            name='feature_ref',
            field=models.CharField(blank=True, help_text='Reference to select list of allowed features for this plan', max_length=100, null=True),
        ),
    ]
