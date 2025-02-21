from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from ..models import Booking
from ..services.shipping.easyship import EasyShipService
import json, logging, pprint
from dateutil.parser import isoparse
from datetime import datetime

logger = logging.getLogger(__name__)


def booking_list(request):
    """Display list of bookings with HTMX support for live updates"""
    bookings = Booking.objects.all().order_by('-created_at')

    bookings_data = list(bookings.values())
    logger.info("Bookings Data:\n%s", pprint.pformat(bookings_data))


    if request.htmx:
        return render(request, 'partials/booking_list.html', {'bookings': bookings})
    return render(request, 'booking/list.html', {'bookings': bookings})

def booking_detail(request, easyship_id):
    """Display detailed booking information"""
    booking = get_object_or_404(Booking, easyship_id=easyship_id)
    if request.htmx:
        return render(request, 'partials/booking_detail.html', {'booking': booking})
    return render(request, 'booking/detail.html', {'booking': booking})

@ensure_csrf_cookie
def create_booking(request):
    """Handle booking creation – both form display and submission.
    Builds a JSON payload matching the working curl request.
    """
    if request.method == "GET":
        return render(request, "booking/create.html")
    
    try:
        data = {}

        def set_nested_value(container, keys, value):
            """
            Recursively set a value in container given a list of keys.
            If a key is numeric, it is treated as a list index.
            """
            key = keys[0]
            if key.isdigit():
                index = int(key)
                if not isinstance(container, list):
                    container = []
                while len(container) <= index:
                    container.append({})
                if len(keys) == 1:
                    container[index] = value
                else:
                    if not isinstance(container[index], (dict, list)):
                        container[index] = {}
                    set_nested_value(container[index], keys[1:], value)
            else:
                if len(keys) == 1:
                    container[key] = value
                else:
                    next_key = keys[1]
                    if next_key.isdigit():
                        if key not in container or not isinstance(container[key], list):
                            container[key] = []
                    else:
                        if key not in container or not isinstance(container[key], dict):
                            container[key] = {}
                    set_nested_value(container[key], keys[1:], value)

        # Build nested structure from POST data.
        for full_key, value in request.POST.items():
            if full_key == "csrfmiddlewaretoken":
                continue
            if full_key.startswith("[") and full_key.endswith("]"):
                key_parts = full_key[1:-1].split("][")
                set_nested_value(data, key_parts, value.strip())
            else:
                data[full_key] = value.strip()

        # Process parcels
        if "parcels" in data:
            for parcel in data["parcels"]:
                if "total_actual_weight" in parcel:
                    parcel["total_actual_weight"] = float(parcel["total_actual_weight"])
                if "box" in parcel:
                    if parcel["box"].strip() in ("{}", ""):
                        parcel["box"] = None
                    else:
                        try:
                            parcel["box"] = json.loads(parcel["box"])
                        except json.JSONDecodeError:
                            parcel["box"] = None
                if "items" in parcel:
                    for item in parcel["items"]:
                        if "dimensions" in item:
                            for dim in item["dimensions"]:
                                item["dimensions"][dim] = float(item["dimensions"][dim])
                        if "actual_weight" in item:
                            item["actual_weight"] = float(item["actual_weight"])
                        if "declared_customs_value" in item:
                            item["declared_customs_value"] = float(item["declared_customs_value"])
                        if "quantity" in item:
                            item["quantity"] = int(item["quantity"])
                        for bool_field in ["contains_battery_pi966", "contains_battery_pi967", "contains_liquids"]:
                            if bool_field in item:
                                item[bool_field] = (item[bool_field] == "on")
                        # Convert empty category to null.
                        if "category" in item and item["category"] == "":
                            item["category"] = None
                        # Default empty SKU to "sku".
                        if "sku" in item and item["sku"] == "":
                            item["sku"] = "sku"

        required_address_fields = [
            "line_1", "city", "state", "postal_code",
            "country_alpha2", "contact_name", "company_name",
            "contact_phone", "contact_email"
        ]
        for addr in ["origin_address", "destination_address"]:
            addr_data = data.get(addr, {})
            for field in required_address_fields:
                if not addr_data.get(field):
                    raise ValueError(f"{addr} is missing required field: {field}")

        # Insurance section.
        if "insurance" not in data:
            data["insurance"] = {"is_insured": False}
        else:
            data["insurance"].setdefault("is_insured", False)
        data["insurance"]["is_insured"] = (data["insurance"]["is_insured"] == "on")

        if "order_data" in data and "order_created_at" in data["order_data"]:
            try:
                dt = datetime.strptime(data["order_data"]["order_created_at"], "%Y-%m-%dT%H:%M")
                data["order_data"]["order_created_at"] = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            except Exception as e:
                raise ValueError("Invalid order_created_at format")

        # Courier settings.
        if "courier_settings" not in data:
            data["courier_settings"] = {"allow_fallback": False, "apply_shipping_rules": True}
        else:
            data["courier_settings"].setdefault("allow_fallback", False)
            data["courier_settings"]["allow_fallback"] = (data["courier_settings"].get("allow_fallback") == "on")
            data["courier_settings"]["apply_shipping_rules"] = (
                data["courier_settings"].get("apply_shipping_rules") == "on" or 
                data["courier_settings"].get("apply_shipping_rules") is True
            )

        # Shipping settings.
        if "shipping_settings" not in data:
            data["shipping_settings"] = {
                "additional_services": {"qr_code": "none"},
                "units": {"weight": "kg", "dimensions": "cm"},
                "buy_label": False,
                "buy_label_synchronous": False,
                "printing_options": {
                    "format": "png",
                    "label": "4x6",
                    "commercial_invoice": "A4",
                    "packing_slip": "4x6"
                }
            }
        else:
            data["shipping_settings"].setdefault("additional_services", {"qr_code": "none"})
            data["shipping_settings"].setdefault("units", {"weight": "kg", "dimensions": "cm"})
            data["shipping_settings"].setdefault("buy_label", False)
            data["shipping_settings"].setdefault("buy_label_synchronous", False)
            data["shipping_settings"].setdefault("printing_options", {
                "format": "png",
                "label": "4x6",
                "commercial_invoice": "A4",
                "packing_slip": "4x6"
            })
            # Convert checkbox values.
            data["shipping_settings"]["buy_label"] = (data["shipping_settings"].get("buy_label") == "on")
            data["shipping_settings"]["buy_label_synchronous"] = (data["shipping_settings"].get("buy_label_synchronous") == "on")

        # Incoterms default.
        data.setdefault("incoterms", "DDU")

        # Log and send payload.
        logger.info("Creating booking with data: %s", json.dumps(data, indent=2))
        easyship_service = EasyShipService()
        response = easyship_service.create_booking(data)
        
        booking = Booking(
            easyship_id=response["id"],
            
            # Origin Address
            origin_line_1=data["origin_address"]["line_1"],
            origin_line_2=data["origin_address"].get("line_2"),
            origin_state=data["origin_address"]["state"],
            origin_city=data["origin_address"]["city"],
            origin_postal_code=data["origin_address"]["postal_code"],
            origin_country_alpha2=data["origin_address"]["country_alpha2"],
            origin_company_name=data["origin_address"]["company_name"],
            origin_contact_name=data["origin_address"]["contact_name"],
            origin_contact_phone=data["origin_address"]["contact_phone"],
            origin_contact_email=data["origin_address"]["contact_email"],
            
            # Destination Address
            destination_line_1=data["destination_address"]["line_1"],
            destination_line_2=data["destination_address"].get("line_2"),
            destination_state=data["destination_address"]["state"],
            destination_city=data["destination_address"]["city"],
            destination_postal_code=data["destination_address"]["postal_code"],
            destination_country_alpha2=data["destination_address"]["country_alpha2"],
            destination_company_name=data["destination_address"]["company_name"],
            destination_contact_name=data["destination_address"]["contact_name"],
            destination_contact_phone=data["destination_address"]["contact_phone"],
            destination_contact_email=data["destination_address"]["contact_email"],
            
            # Regulatory Information
            regulatory_identifiers=data.get("regulatory_identifiers", {}),
            buyer_regulatory_identifiers=data.get("buyer_regulatory_identifiers", {}),
            incoterms=data.get("incoterms"),
            
            # Insurance
            is_insured=data["insurance"]["is_insured"],
            
            # Order Data
            platform_name=data["order_data"].get("platform_name"),
            buyer_selected_courier_name=data["order_data"].get("buyer_selected_courier_name"),
            order_created_at=isoparse(data["order_data"]["order_created_at"]) if data["order_data"].get("order_created_at") else None,
            
            # Courier Settings
            allow_fallback=data["courier_settings"]["allow_fallback"],
            apply_shipping_rules=data["courier_settings"]["apply_shipping_rules"],
            
            shipping_settings=data["shipping_settings"],
            
            parcels=data["parcels"],
            
            status="PENDING",
            tracking_number=None,
            courier_tracking_numbers=None,
            label_url=None,
            courier_name=None,
            selected_courier_id=None,
            selected_courier_service=None,
        )
        booking.save()
        
        if request.htmx:
            return render(request, "partials/booking_created.html", {"booking": booking})
        return JsonResponse({
            "id": booking.easyship_id,
            "status": booking.status,
            "tracking_number": booking.tracking_number
        })
    
    except ValueError as e:
        logger.error("Validation error: %s", str(e))
        if request.htmx:
            return HttpResponseBadRequest(f"Validation error: {str(e)}")
        return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
        logger.error("Error creating booking: %s", str(e), exc_info=True)
        if request.htmx:
            return HttpResponseBadRequest(f"Error creating booking: {str(e)}")
        return JsonResponse({"error": str(e)}, status=400)
