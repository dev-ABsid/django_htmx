from django.db import models


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TrackingEvent(BaseModel):
    tracking_number = models.CharField(max_length=255, db_index=True)
    status = models.CharField(max_length=255)
    location = models.CharField(max_length=255, null=True, blank=True)
    timestamp = models.DateTimeField()
    message = models.TextField(null=True, blank=True)
    tracking_status = models.CharField(max_length=255, null=True, blank=True)
    booking = models.ForeignKey(
        'Booking', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='tracking_events'
    )


class TrackingInfo(BaseModel):
    tracking_number = models.CharField(max_length=255, unique=True, db_index=True)
    current_status = models.CharField(max_length=255)
    origin_country = models.CharField(max_length=2, null=True, blank=True)
    destination_country = models.CharField(max_length=2, null=True, blank=True)
    estimated_delivery = models.DateTimeField(null=True, blank=True)
    delivery_date = models.DateTimeField(null=True, blank=True)
    carrier = models.CharField(max_length=255, default="EasyShip")
    tracking_link = models.URLField(null=True, blank=True)
    raw_response = models.JSONField(null=True, blank=True)


class Booking(BaseModel):
    easyship_id = models.CharField(max_length=255, unique=True, db_index=True)
    
    # Origin Address
    origin_line_1 = models.CharField(max_length=255)
    origin_line_2 = models.CharField(max_length=255, null=True, blank=True)
    origin_state = models.CharField(max_length=255)
    origin_city = models.CharField(max_length=255)
    origin_postal_code = models.CharField(max_length=255)
    origin_country_alpha2 = models.CharField(max_length=2)
    origin_company_name = models.CharField(max_length=255)
    origin_contact_name = models.CharField(max_length=255)
    origin_contact_phone = models.CharField(max_length=255)
    origin_contact_email = models.EmailField()

    # Destination Address
    destination_line_1 = models.CharField(max_length=255)
    destination_line_2 = models.CharField(max_length=255, null=True, blank=True)
    destination_state = models.CharField(max_length=255)
    destination_city = models.CharField(max_length=255)
    destination_postal_code = models.CharField(max_length=255)
    destination_country_alpha2 = models.CharField(max_length=2)
    destination_company_name = models.CharField(max_length=255)
    destination_contact_name = models.CharField(max_length=255)
    destination_contact_phone = models.CharField(max_length=255)
    destination_contact_email = models.EmailField()

    # Regulatory Information
    regulatory_identifiers = models.JSONField(null=True, blank=True)
    buyer_regulatory_identifiers = models.JSONField(null=True, blank=True)
    incoterms = models.CharField(max_length=255, null=True, blank=True)
    
    # Insurance
    is_insured = models.BooleanField(default=False)
    
    # Order Data
    platform_name = models.CharField(max_length=255, null=True, blank=True)
    buyer_selected_courier_name = models.CharField(max_length=255, null=True, blank=True)
    order_created_at = models.DateTimeField(null=True, blank=True)
    
    # Courier Settings
    allow_fallback = models.BooleanField(default=False)
    apply_shipping_rules = models.BooleanField(default=True)
    
    # Shipping Settings
    shipping_settings = models.JSONField()
    
    # Parcels and Items
    parcels = models.JSONField()
    
    # Shipment Status
    status = models.CharField(max_length=255, default="PENDING")
    tracking_number = models.CharField(max_length=255, null=True, blank=True)
    courier_tracking_numbers = models.JSONField(null=True, blank=True)
    label_url = models.URLField(null=True, blank=True)
    courier_name = models.CharField(max_length=255, null=True, blank=True)
    selected_courier_id = models.CharField(max_length=255, null=True, blank=True)
    selected_courier_service = models.CharField(max_length=255, null=True, blank=True)

    # Response Documents
    documents = models.JSONField(null=True, blank=True)