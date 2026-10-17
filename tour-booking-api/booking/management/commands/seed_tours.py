from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from booking.models import Tour

TOURS = [
    ("Бурабай на выходные", "Астана", "45000", 20),
    ("Чарын и Кольсай", "Алматы", "38000", 30),
    ("Шымкент — Туркестан", "Шымкент", "52000", 15),
    ("Стамбул, 5 дней", "Алматы", "320000", 10),
]


class Command(BaseCommand):
    help = "Заполняет базу демо-турами"

    def handle(self, *args, **options):
        for i, (title, city, price, seats) in enumerate(TOURS, start=1):
            Tour.objects.get_or_create(
                title=title,
                defaults=dict(city=city, price=Decimal(price), seats_total=seats, seats_available=seats,
                              starts_at=timezone.now() + timedelta(days=7 * i)),
            )
        self.stdout.write(self.style.SUCCESS(f"Туров в базе: {Tour.objects.count()}"))
