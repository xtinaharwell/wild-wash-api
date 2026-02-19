# Generated migration to clean up duplicate empty phone values

from django.db import migrations, models

def clean_phone_values(apps, schema_editor):
    """Convert empty phone strings to NULL to allow UNIQUE constraint"""
    User = apps.get_model('users', 'User')
    User.objects.filter(phone='').update(phone=None)

def reverse_clean(apps, schema_editor):
    """Reverse: convert NULL phone values back to empty string"""
    User = apps.get_model('users', 'User')
    User.objects.filter(phone__isnull=True).update(phone='')

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_add_staff_types'),
    ]

    operations = [
        # First alter the field to allow NULL
        migrations.AlterField(
            model_name='user',
            name='phone',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        # Then clean the data
        migrations.RunPython(clean_phone_values, reverse_clean),
    ]
