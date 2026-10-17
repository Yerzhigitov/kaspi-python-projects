from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q


class Tour(models.Model):
    title = models.CharField(max_length=200)
    city = models.CharField(max_length=100, db_index=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    starts_at = models.DateTimeField(db_index=True)
    seats_total = models.PositiveIntegerField()
    seats_available = models.PositiveIntegerField()

    class Meta:
        ordering = ["starts_at"]
        constraints = [
            # Инвариант на уровне БД: мест не может стать больше, чем всего, или меньше нуля.
            models.CheckConstraint(check=Q(seats_available__lte=F("seats_total")), name="seats_available_lte_total"),
        ]

    def __str__(self):
        return f"{self.title} ({self.city})"


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Ожидает оплаты"
        PAID = "paid", "Оплачено"
        CANCELLED = "cancelled", "Отменено"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="bookings")
    tour = models.ForeignKey(Tour, on_delete=models.PROTECT, related_name="bookings")
    seats = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    idempotency_key = models.CharField(max_length=64, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            # Ключ уникален в рамках пользователя: чужой ключ не может «украсть» бронь.
            models.UniqueConstraint(fields=["user", "idempotency_key"], name="unique_user_idempotency_key"),
        ]

    def __str__(self):
        return f"Booking #{self.pk} {self.tour} x{self.seats} [{self.status}]"
