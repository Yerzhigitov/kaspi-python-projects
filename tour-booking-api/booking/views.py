from django.shortcuts import get_object_or_404
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from . import services
from .filters import TourFilter
from .models import Booking, Tour
from .serializers import BookingCreateSerializer, BookingSerializer, TourSerializer


class TourViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tour.objects.all()
    serializer_class = TourSerializer
    filterset_class = TourFilter
    ordering_fields = ["price", "starts_at"]


class BookingViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Пользователь видит только свои брони; select_related убирает N+1 запросов к турам.
        return Booking.objects.filter(user=self.request.user).select_related("tour")

    def create(self, request):
        data = BookingCreateSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        try:
            booking = services.create_booking(
                request.user,
                data.validated_data["tour_id"],
                data.validated_data["seats"],
                request.headers.get("Idempotency-Key"),
            )
        except services.BookingError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response(BookingSerializer(booking).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def pay(self, request, pk=None):
        return self._transition(services.pay_booking, pk)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        return self._transition(services.cancel_booking, pk)

    def _transition(self, func, pk):
        get_object_or_404(self.get_queryset(), pk=pk)
        try:
            booking = func(pk, self.request.user)
        except services.BookingError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response(BookingSerializer(booking).data)
