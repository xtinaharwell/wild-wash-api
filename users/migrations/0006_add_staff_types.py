# Generated migration for staff type roles

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_user_pickup_address'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='staff_type',
            field=models.CharField(
                choices=[('general', 'General Staff'), ('washer', 'Washer'), ('folder', 'Folder')],
                default='general',
                help_text='Type of staff: General, Washer, or Folder',
                max_length=20
            ),
        ),
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(
                choices=[('customer', 'Customer'), ('rider', 'Rider'), ('admin', 'Admin'), ('staff', 'Staff'), ('washer', 'Washer'), ('folder', 'Folder')],
                default='customer',
                max_length=20
            ),
        ),
    ]
