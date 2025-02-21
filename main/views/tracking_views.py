from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_http_methods
from ..models import Booking
from ..services.shipping.easyship import EasyShipService
import json, logging

logger = logging.getLogger(__name__)

@require_http_methods(["GET"])
def track_shipment(request, easyship_id):
    try:
        shipment_id = request.GET.get('shipment_id', easyship_id)
        booking = get_object_or_404(Booking, easyship_id=shipment_id)
        easyship_service = EasyShipService()
        tracking_info = easyship_service.track_shipment(shipment_id)
        
        # Add logging
        logger.info("Tracking info received: %s", json.dumps(tracking_info, indent=2))
        
        if request.htmx:
            return render(request, 'partials/tracking_detail.html', {
                'booking': booking,
                'tracking': tracking_info
            })
            
        return render(request, 'tracking/detail.html', {
            'booking': booking,
            'tracking': tracking_info.get('tracking', {})
        })
    except Exception as e:
        logger.error("Tracking error: %s", str(e))
        if request.htmx:
            return HttpResponseBadRequest(str(e))
        return JsonResponse({'error': str(e)}, status=400)
    
def track_search(request):
    """Search tracking page"""
    return render(request, 'tracking/search.html')
