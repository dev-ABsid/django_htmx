from django.urls import path
from .views import booking_views, tracking_views, schedule_views

app_name = 'main'

# Booking URLs
booking_patterns = [
    path('bookings/', booking_views.booking_list, name='booking_list'),
    path('bookings/create/', booking_views.create_booking, name='create_booking'),
    path('bookings/<str:easyship_id>/', booking_views.booking_detail, name='booking_detail'),
]

# Tracking URLs
tracking_patterns = [
    path('track/', tracking_views.track_search, name='track_search'),
    path('track/<str:easyship_id>/', tracking_views.track_shipment, name='track_shipment'),
]

# Schedule URLs
schedule_patterns = [
    path('schedule/', schedule_views.schedule_view, name='schedule'),
    path('schedule/change-month/', schedule_views.change_month, name='change_month'),
    path('schedule/update/<str:booking_id>/', schedule_views.update_schedule, name='update_schedule'),
    path('schedule/pending-packages/', schedule_views.pending_packages, name='pending_packages'),
    path('reset_calendar/', schedule_views.reset_calendar, name='reset_calendar'),
]

# all URLs
urlpatterns = booking_patterns + tracking_patterns + schedule_patterns