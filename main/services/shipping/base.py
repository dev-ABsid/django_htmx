from abc import ABC, abstractmethod
from typing import Dict, Any

class ShippingServiceBase(ABC):
    @abstractmethod
    def track_shipment(self, tracking_number: str) -> Dict[str, Any]:
        """Track a shipment"""
        pass

    @abstractmethod
    def create_booking(self, booking_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a booking"""
        pass