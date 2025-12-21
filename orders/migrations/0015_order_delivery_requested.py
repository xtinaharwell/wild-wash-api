# Generated migration for delivery request tracking

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0014_orderitem'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='delivery_requested',
            field=models.BooleanField(default=False, help_text='Whether customer has requested delivery'),
        ),
        migrations.AddField(
            model_name='order',
            name='delivery_requested_at',
            field=models.DateTimeField(blank=True, help_text='Timestamp when customer requested delivery', null=True),
        ),
    ]
