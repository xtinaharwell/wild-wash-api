"""
Django management command to initialize default spin algorithms.

Run with: python manage.py init_algorithms
"""

from django.core.management.base import BaseCommand
from casino.models import SpinAlgorithmConfiguration
from casino.algorithms import get_all_algorithms


class Command(BaseCommand):
    help = 'Initialize default spin algorithm configurations'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Initializing spin algorithms...'))
        
        # Get all available algorithms
        algorithms = get_all_algorithms()
        
        # Create or update configurations
        for i, algo_info in enumerate(algorithms):
            config, created = SpinAlgorithmConfiguration.objects.get_or_create(
                name=f"{algo_info['name']} - Default",
                defaults={
                    'algorithm_key': algo_info['key'],
                    'description': algo_info['description'],
                    'is_active': (i == 0),  # Make first one active by default
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created: {config.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'→ Already exists: {config.name}')
                )
        
        self.stdout.write(self.style.SUCCESS('\nAlgorithm initialization complete!'))
        
        # Show current active algorithm
        active = SpinAlgorithmConfiguration.objects.filter(is_active=True).first()
        if active:
            self.stdout.write(
                self.style.SUCCESS(f'Active algorithm: {active.name}')
            )
