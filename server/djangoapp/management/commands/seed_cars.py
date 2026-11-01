from django.core.management.base import BaseCommand
from djangoapp.models import CarMake, CarModel

class Command(BaseCommand):
    help = 'Idempotently populate the demonstration car inventory'
    def handle(self, *args, **options):
        for make, model, kind, year in [
            ('Toyota', 'Camry', 'SEDAN', 2023), ('Toyota', 'RAV4', 'SUV', 2023),
            ('Honda', 'Civic', 'SEDAN', 2022), ('Honda', 'CR-V', 'SUV', 2023),
            ('Ford', 'F-150', 'TRUCK', 2023), ('Ford', 'Mustang', 'COUPE', 2023),
            ('BMW', 'X5', 'SUV', 2022), ('Audi', 'A4', 'SEDAN', 2023),
        ]:
            brand, _ = CarMake.objects.get_or_create(name=make, defaults={'description': f'{make} passenger vehicles'})
            CarModel.objects.get_or_create(car_make=brand, name=model, year=year, defaults={'type': kind})
        self.stdout.write(self.style.SUCCESS('Car inventory ready.'))
