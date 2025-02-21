from django.shortcuts import render
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_http_methods
from django.template.loader import render_to_string
from datetime import datetime
import logging
from ..utils.helpers import get_calendar_weeks

logger = logging.getLogger(__name__)

DUMMY_BOOKINGS = [
    {
        "id": "1",
        "tracking_number": "TRK123456",
        "destination": "New York, USA",
        "status": "pending",
        "scheduled_date": None
    },
    {
        "id": "2",
        "tracking_number": "TRK789012",
        "destination": "London, UK",
        "status": "pending",
        "scheduled_date": None
    },
    {
        "id": "3",
        "tracking_number": "TRK345678",
        "destination": "Tokyo, Japan",
        "status": "pending",
        "scheduled_date": None
    }
]


def schedule_view(request):
    """Display the schedule using global dummy bookings."""
    current_date = datetime.now()
    weeks = get_calendar_weeks(current_date)
    return render(request, 'schedule/calendar.html', {
        'bookings': DUMMY_BOOKINGS,
        'weeks': weeks,
        'current_date': current_date
    })

@require_http_methods(["POST"])
def update_schedule(request, booking_id):
    """Update a booking schedule using global dummy bookings."""
    try:
        week_id = request.POST.get('week_id')
        if not week_id:
            return HttpResponseBadRequest("Week ID is required")

        bookings_dict = {booking["id"]: booking for booking in DUMMY_BOOKINGS}

        if booking_id in bookings_dict:
            bookings_dict[booking_id]["status"] = "scheduled"
            bookings_dict[booking_id]["scheduled_date"] = week_id

        current_date = datetime.now()
        weeks = get_calendar_weeks(current_date)

        calendar_html = render_to_string('schedule/calendar_content.html', {
            'weeks': weeks,
            'bookings': DUMMY_BOOKINGS,
            'current_date': current_date
        })

        pending_html = render_to_string('schedule/pending_packages.html', {
            'bookings': DUMMY_BOOKINGS
        })

        return JsonResponse({
            'calendar_html': calendar_html,
            'pending_html': pending_html
        })

    except Exception as e:
        logger.error(f"Error updating schedule: {str(e)}")
        return JsonResponse({'status': 'error', 'error': str(e)}, status=400)

@require_http_methods(["GET"])
def pending_packages(request):
    """Return pending packages partial using global dummy bookings."""
    return render(request, 'schedule/pending_packages.html', {
        'bookings': DUMMY_BOOKINGS
    })

@require_http_methods(["POST"])
def reset_calendar(request):
    """Reset the global dummy booking data to its initial state."""
    global DUMMY_BOOKINGS
    # Reinitialize the dummy bookings
    DUMMY_BOOKINGS = [
        {
            "id": "1",
            "tracking_number": "TRK123456",
            "destination": "New York, USA",
            "status": "pending",
            "scheduled_date": None
        },
        {
            "id": "2",
            "tracking_number": "TRK789012",
            "destination": "London, UK",
            "status": "pending",
            "scheduled_date": None
        },
        {
            "id": "3",
            "tracking_number": "TRK345678",
            "destination": "Tokyo, Japan",
            "status": "pending",
            "scheduled_date": None
        }
    ]
    
    current_date = datetime.now()
    weeks = get_calendar_weeks(current_date)
    
    calendar_html = render_to_string('schedule/calendar_content.html', {
        'weeks': weeks,
        'bookings': DUMMY_BOOKINGS,
        'current_date': current_date
    })
    pending_html = render_to_string('schedule/pending_packages.html', {
        'bookings': DUMMY_BOOKINGS
    })
    
    return JsonResponse({
        'calendar_html': calendar_html,
        'pending_html': pending_html
    })


def change_month(request):
    """Handle month navigation while using global dummy bookings."""
    try:
        direction = request.GET.get('direction')
        current_date_str = request.GET.get('current_date')
        
        current_date = datetime.strptime(current_date_str, '%Y-%m')
        
        if direction == 'prev':
            if current_date.month == 1:
                new_date = current_date.replace(year=current_date.year - 1, month=12, day=1)
            else:
                new_date = current_date.replace(month=current_date.month - 1, day=1)
        else:
            if current_date.month == 12:
                new_date = current_date.replace(year=current_date.year + 1, month=1, day=1)
            else:
                new_date = current_date.replace(month=current_date.month + 1, day=1)
        
        logger.info(f"Navigating {direction}: {current_date_str} -> {new_date.strftime('%Y-%m')}")
        
        weeks = get_calendar_weeks(new_date)
        
        return render(request, 'schedule/calendar_content.html', {
            'weeks': weeks,
            'bookings': DUMMY_BOOKINGS,
            'current_date': new_date 
        })
    
    except Exception as e:
        logger.error(f"Error changing month: {str(e)}")
        return HttpResponseBadRequest(f"Error changing month: {str(e)}")

