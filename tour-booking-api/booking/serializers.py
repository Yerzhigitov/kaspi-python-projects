from rest_framework import serializers

from .models import Booking, Tour


class TourSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tour
        fields = ["id", "title", "city", "price", "starts_at", "seats_total", "seats_available"]


class BookingSerializer(serializers.ModelSerializer):
    tour = TourSerializer(read_only=True)

    class Meta:
        model = Booking
        fields = ["id", "tour", "seats", "total_price", "status", "created_at"]


class BookingCreateSerializer(serializers.Serializer):
    tour_id = serializers.IntegerField()
    seats = serializers.IntegerField(min_value=1, max_value=10)
