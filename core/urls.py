from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda request: redirect('main:booking_list')),  # Redirect root to booking list
    path('', include('main.urls')),  # Include main app URLs
]