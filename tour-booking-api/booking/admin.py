from django.contrib import admin

from .models import Booking, Tour


@admin.register(Tour)
class TourAdmin(admin.ModelAdmin):
    list_display = ["title", "city", "price", "starts_at", "seats_available", "seats_total"]
    list_filter = ["city"]
    search_fields = ["title", "city"]


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "tour", "seats", "total_price", "status", "created_at"]
    list_filter = ["status"]
    list_select_related = ["user", "tour"]
