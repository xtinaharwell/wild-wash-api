# Generated migration for washer and folder workflow

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('orders', '0015_order_delivery_requested'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='washer',
            field=models.ForeignKey(
                blank=True,
                help_text='Staff member who washed the order',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='washed_orders',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='washed_at',
            field=models.DateTimeField(
                blank=True,
                help_text='Timestamp when order was washed',
                null=True
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='folder',
            field=models.ForeignKey(
                blank=True,
                help_text='Staff member who folded the order',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='folded_orders',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='folded_at',
            field=models.DateTimeField(
                blank=True,
                help_text='Timestamp when order was folded',
                null=True
            ),
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(
                choices=[
                    ('requested', 'Requested'),
                    ('picked', 'Picked Up'),
                    ('in_progress', 'In Progress'),
                    ('washed', 'Washed'),
                    ('ready', 'Ready for Delivery'),
                    ('delivered', 'Delivered'),
                    ('cancelled', 'Cancelled'),
                    ('pending_assignment', 'Pending Assignment')
                ],
                default='requested',
                max_length=20
            ),
        ),
    ]
