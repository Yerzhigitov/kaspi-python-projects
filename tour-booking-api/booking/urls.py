from rest_framework.routers import DefaultRouter

from .views import BookingViewSet, TourViewSet

router = DefaultRouter()
router.register("tours", TourViewSet)
router.register("bookings", BookingViewSet, basename="booking")

urlpatterns = router.urls
