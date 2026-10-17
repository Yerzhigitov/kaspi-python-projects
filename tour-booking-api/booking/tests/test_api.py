from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APITestCase

from booking.models import Booking, Tour


class BaseCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user("ali", password="pass12345")
        self.other = User.objects.create_user("dana", password="pass12345")
        self.tour = Tour.objects.create(
            title="Бурабай", city="Астана", price=Decimal("45000.00"),
            starts_at=timezone.now() + timedelta(days=10), seats_total=3, seats_available=3,
        )
        self.client.force_authenticate(self.user)

    def book(self, seats=1, key=None, tour=None):
        headers = {"HTTP_IDEMPOTENCY_KEY": key} if key else {}
        return self.client.post("/api/bookings/", {"tour_id": (tour or self.tour).id, "seats": seats}, **headers)


class TourTests(BaseCase):
    def test_list_is_public_and_filterable(self):
        Tour.objects.create(title="Чарын", city="Алматы", price=Decimal("38000"),
                            starts_at=timezone.now() + timedelta(days=5), seats_total=5, seats_available=0)
        self.client.force_authenticate(None)
        r = self.client.get("/api/tours/", {"city": "Алматы"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual([t["title"] for t in r.data["results"]], ["Чарын"])
        r = self.client.get("/api/tours/", {"has_seats": "true", "max_price": "50000"})
        self.assertEqual([t["title"] for t in r.data["results"]], ["Бурабай"])


class BookingTests(BaseCase):
    def test_booking_reserves_seats_and_counts_price(self):
        r = self.book(seats=2)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["total_price"], "90000.00")
        self.tour.refresh_from_db()
        self.assertEqual(self.tour.seats_available, 1)

    def test_cannot_overbook(self):
        self.book(seats=3)
        r = self.book(seats=1)
        self.assertEqual(r.status_code, 409)

    def test_cannot_book_started_tour(self):
        self.tour.starts_at = timezone.now() - timedelta(hours=1)
        self.tour.save()
        self.assertEqual(self.book().status_code, 409)

    def test_requires_auth(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.book().status_code, 401)

    def test_idempotency_key(self):
        r1 = self.book(seats=1, key="req-1")
        r2 = self.book(seats=1, key="req-1")
        self.assertEqual(r1.data["id"], r2.data["id"])
        self.tour.refresh_from_db()
        self.assertEqual(self.tour.seats_available, 2)

    def test_pay_and_cancel_returns_seats(self):
        booking_id = self.book(seats=2).data["id"]
        self.assertEqual(self.client.post(f"/api/bookings/{booking_id}/pay/").data["status"], "paid")
        self.assertEqual(self.client.post(f"/api/bookings/{booking_id}/cancel/").data["status"], "cancelled")
        self.tour.refresh_from_db()
        self.assertEqual(self.tour.seats_available, 3)
        self.assertEqual(self.client.post(f"/api/bookings/{booking_id}/pay/").status_code, 409)

    def test_user_sees_only_own_bookings(self):
        own = self.book().data["id"]
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get("/api/bookings/").data["count"], 0)
        self.assertEqual(self.client.post(f"/api/bookings/{own}/cancel/").status_code, 404)

    def test_list_has_no_n_plus_one(self):
        for _ in range(3):
            self.book()
        # 1 запрос на COUNT для пагинации + 1 на брони вместе с турами (select_related)
        with self.assertNumQueries(2):
            self.client.get("/api/bookings/")
