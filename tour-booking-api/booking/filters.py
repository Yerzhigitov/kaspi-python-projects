import django_filters

from .models import Tour


class TourFilter(django_filters.FilterSet):
    city = django_filters.CharFilter(lookup_expr="iexact")
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr="lte")
    date_from = django_filters.DateFilter(field_name="starts_at", lookup_expr="date__gte")
    date_to = django_filters.DateFilter(field_name="starts_at", lookup_expr="date__lte")
    has_seats = django_filters.BooleanFilter(method="filter_has_seats")

    class Meta:
        model = Tour
        fields = ["city"]

    def filter_has_seats(self, queryset, name, value):
        return queryset.filter(seats_available__gt=0) if value else queryset
