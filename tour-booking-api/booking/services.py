"""Бизнес-логика бронирования. Всё, что меняет места, выполняется в транзакции с блокировкой строки тура."""
from typing import Optional

from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import Booking, Tour


class BookingError(Exception):
    pass


def create_booking(user, tour_id: int, seats: int, idempotency_key: Optional[str] = None) -> Booking:
    if idempotency_key:
        existing = Booking.objects.filter(user=user, idempotency_key=idempotency_key).first()
        if existing:
            return existing
    try:
        with transaction.atomic():
            # SELECT ... FOR UPDATE: два одновременных запроса на последнее место
            # выстроятся в очередь, и второй увидит уже уменьшенный остаток.
            tour = Tour.objects.select_for_update().get(pk=tour_id)
            if tour.starts_at <= timezone.now():
                raise BookingError("Тур уже начался")
            if tour.seats_available < seats:
                raise BookingError(f"Осталось мест: {tour.seats_available}")
            tour.seats_available -= seats
            tour.save(update_fields=["seats_available"])
            return Booking.objects.create(
                user=user,
                tour=tour,
                seats=seats,
                total_price=tour.price * seats,
                idempotency_key=idempotency_key,
            )
    except Tour.DoesNotExist:
        raise BookingError("Тур не найден")
    except IntegrityError:
        # Параллельный запрос с тем же ключом успел первым.
        existing = Booking.objects.filter(user=user, idempotency_key=idempotency_key).first()
        if existing is None:
            raise
        return existing


def pay_booking(booking_id: int, user) -> Booking:
    with transaction.atomic():
        booking = Booking.objects.select_for_update().get(pk=booking_id, user=user)
        if booking.status == Booking.Status.PAID:
            return booking
        if booking.status != Booking.Status.PENDING:
            raise BookingError("Оплатить можно только бронь в статусе pending")
        booking.status = Booking.Status.PAID
        booking.save(update_fields=["status"])
        return booking


def cancel_booking(booking_id: int, user) -> Booking:
    with transaction.atomic():
        booking = Booking.objects.select_for_update().get(pk=booking_id, user=user)
        if booking.status == Booking.Status.CANCELLED:
            return booking
        # Блокируем тур, чтобы возврат мест не потерялся при параллельных бронях.
        tour = Tour.objects.select_for_update().get(pk=booking.tour_id)
        tour.seats_available += booking.seats
        tour.save(update_fields=["seats_available"])
        booking.status = Booking.Status.CANCELLED
        booking.save(update_fields=["status"])
        return booking
