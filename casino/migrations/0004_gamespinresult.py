# Generated migration for GameSpinResult model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('casino', '0003_spinalgorithmconfiguration'),
    ]

    operations = [
        migrations.CreateModel(
            name='GameSpinResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('game_type', models.CharField(
                    choices=[
                        ('spin_the_wheel', 'Spin The Wheel'),
                        ('crash_game', 'Crash Game'),
                        ('pump_game', 'Pump The Coin'),
                    ],
                    default='spin_the_wheel',
                    max_length=20
                )),
                ('spin_cost', models.DecimalField(decimal_places=2, max_digits=10)),
                ('result_label', models.CharField(help_text="e.g., '2x', '0.5x', 'LOSE'", max_length=50)),
                ('multiplier', models.DecimalField(decimal_places=2, max_digits=5)),
                ('winnings', models.DecimalField(decimal_places=2, max_digits=12)),
                ('net_profit', models.DecimalField(decimal_places=2, default='0.00', max_digits=12)),
                ('is_win', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('wallet', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='spin_results', to='casino.gamewallet')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='gamespinresult',
            index=models.Index(fields=['wallet', 'created_at'], name='casino_game_wallet_created_idx'),
        ),
        migrations.AddIndex(
            model_name='gamespinresult',
            index=models.Index(fields=['wallet', 'game_type', 'created_at'], name='casino_game_wallet_type_idx'),
        ),
        migrations.AddIndex(
            model_name='gamespinresult',
            index=models.Index(fields=['is_win'], name='casino_game_is_win_idx'),
        ),
    ]
