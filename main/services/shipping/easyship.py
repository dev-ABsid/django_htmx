from typing import Dict, Any, Optional
import requests
from django.conf import settings
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)

class EasyShipService:
    def __init__(self):
        self.api_key = "prod_iY6935Ab/CrSlWa2SmLLvCn72EBwi0fsRQWdd8+DZKE="
        self.base_url = "https://public-api.easyship.com"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "accept": "application/json"
        }

    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to EasyShip API"""
        try:
            # If data contains datetime objects, convert them to ISO format strings
            if data and isinstance(data, dict):
                data = self._prepare_data(data)
            logger.info("Making API request: %s %s", method, endpoint)
            logger.info("Request data: %s", json.dumps(data, indent=2))
            response = requests.request(
                method=method,
                url=f"{self.base_url}{endpoint}",
                json=data,
                headers=self.headers,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"EasyShip API error: {str(e)}")

    def _prepare_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data for API request by converting datetime objects to ISO format strings"""
        prepared_data = {}
        for key, value in data.items():
            if isinstance(value, datetime):
                prepared_data[key] = value.isoformat()
            elif isinstance(value, dict):
                prepared_data[key] = self._prepare_data(value)
            elif isinstance(value, list):
                prepared_data[key] = [
                    self._prepare_data(item) if isinstance(item, dict) else item 
                    for item in value
                ]
            else:
                prepared_data[key] = value
        return prepared_data

    def create_booking(self, booking_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new shipping booking"""
        try:
            logger.info("Creating a booking with data: %s", json.dumps(booking_data, indent=2))

            response = self._make_request(
                "POST", 
                "/2024-09/shipments", 
                booking_data
            )

            logger.info("Raw API Response: %s", json.dumps(response, indent=2))

            # The API returns a single shipment under the "shipment" key
            shipment = response.get("shipment")
            if not shipment:
                raise Exception("No shipment in response")
                
            courier_service = shipment.get("courier_service", {})
            
            return {
                "id": shipment.get("easyship_shipment_id"),
                "tracking_number": shipment.get("tracking_page_url"),
                "courier_tracking_numbers": shipment.get("trackings", []),
                "status": shipment.get("shipment_state"),
                "label_url": None,  # Set appropriate field if available
                "selected_courier": {
                    "id": courier_service.get("courier_id"),
                    "name": courier_service.get("name"),
                    "service_name": courier_service.get("umbrella_name")
                } if courier_service else None,
                "documents": shipment.get("shipping_documents", []),
                "created_at": shipment.get("created_at"),
                "updated_at": shipment.get("updated_at")
            }
        except Exception as e:
            raise Exception(f"Failed to create booking: {str(e)}")

    def track_shipment(self, shipment_id: str) -> Dict[str, Any]:
        """Get tracking information for a shipment"""
        try:
            print(shipment_id)
            response = self._make_request(
                "GET",
                f"/2024-09/shipments/trackings?easyship_shipment_id={shipment_id}"
            )
            return response
        except Exception as e:
            raise Exception(f"Failed to get tracking: {str(e)}")

    def get_rates(self, booking_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get shipping rates for a potential booking"""
        try:
            response = self._make_request(
                "POST", 
                "/2024-09/rates", 
                booking_data
            )
            return response
        except Exception as e:
            raise Exception(f"Failed to get rates: {str(e)}")

    def void_label(self, shipment_id: str) -> Dict[str, Any]:
        """Void a shipping label"""
        try:
            response = self._make_request(
                "POST", 
                f"/2024-09/shipments/{shipment_id}/void"
            )
            return response
        except Exception as e:
            raise Exception(f"Failed to void label: {str(e)}")

    def get_label(self, shipment_id: str) -> Dict[str, Any]:
        """Get shipping label"""
        try:
            response = self._make_request(
                "GET", 
                f"/2024-09/shipments/{shipment_id}/label"
            )
            return response
        except Exception as e:
            raise Exception(f"Failed to get label: {str(e)}")