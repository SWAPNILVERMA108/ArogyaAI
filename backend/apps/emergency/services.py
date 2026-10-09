import os
import re
from urllib.parse import urlencode

from django.db import IntegrityError, transaction
from rest_framework.exceptions import ValidationError

from common.exceptions.api import Conflict

from .models import EmergencyContact


EMERGENCY_GUIDANCE = [
    "If someone may be in immediate danger, call emergency services now; do not wait for an app response.",
    "Tell the dispatcher your precise location, a callback number, and what is happening.",
    "Follow the emergency dispatcher's instructions and seek immediate professional help.",
    "If it is safe, ask a nearby trusted person to stay with the person who needs help.",
]


class EmergencyService:
    @staticmethod
    def information():
        configured_number = os.environ.get("EMERGENCY_SERVICES_NUMBER", "").strip()
        uses_india_default = not configured_number
        number = configured_number or "112"
        dialable_number = re.sub(r"[^0-9+*#]", "", number)
        if not dialable_number or not any(char.isdigit() for char in dialable_number):
            number = ""
            call_uri = ""
        else:
            call_uri = f"tel:{dialable_number}"
        information_url = os.environ.get("EMERGENCY_SERVICES_INFO_URL", "").strip()
        if not information_url and uses_india_default:
            information_url = "https://112.gov.in/"
        return {
            "emergency_number": number,
            "emergency_label": os.environ.get("EMERGENCY_SERVICES_LABEL", "").strip()
            or ("India emergency services" if uses_india_default else "Local emergency services"),
            "call_uri": call_uri,
            "information_url": information_url,
            "nearby_facilities_endpoint": "/api/hospitals/nearby/",
            "disclaimer": (
                "ArogyaAI is not an emergency response service and cannot dispatch help. "
                "Call local emergency services directly; use your local number if outside India."
            ),
            "guidance": EMERGENCY_GUIDANCE,
        }

    @staticmethod
    def create_contact(user, validated_data):
        try:
            with transaction.atomic():
                return EmergencyContact.objects.create(user=user, **validated_data)
        except IntegrityError as exc:
            raise Conflict("Only one emergency contact can be marked as primary.") from exc

    @staticmethod
    def update_contact(contact, validated_data):
        for field, value in validated_data.items():
            setattr(contact, field, value)
        try:
            with transaction.atomic():
                contact.save(update_fields=[*validated_data.keys(), "updated_at"])
        except IntegrityError as exc:
            raise Conflict("Only one emergency contact can be marked as primary.") from exc
        return contact

    @staticmethod
    def delete_contact(contact):
        contact.delete()

    @staticmethod
    def create_location_share(latitude, longitude, contact=None):
        latitude = round(float(latitude), 6)
        longitude = round(float(longitude), 6)
        map_url = "https://www.openstreetmap.org/?" + urlencode(
            {"mlat": latitude, "mlon": longitude}
        ) + f"#map=16/{latitude}/{longitude}"
        message = f"I may need help. My current location is: {map_url}"
        contact_data = None
        if contact is not None:
            contact_data = {
                "id": contact.pk,
                "name": contact.name,
                "phone": contact.phone,
                "relationship": contact.relationship,
                "is_primary": contact.is_primary,
                "created_at": contact.created_at,
                "updated_at": contact.updated_at,
            }
        return {
            "share_url": map_url,
            "message": message,
            "contact": contact_data,
            "notice": (
                "Location is not stored and no message is sent automatically. "
                "Review and share the message yourself with the selected contact."
            ),
        }
