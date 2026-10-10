"""Cross-cutting security checks that span several apps."""
import logging

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

User = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.fixture
def make_user():
    def _make(email, role=User.Role.PATIENT):
        return User.objects.create_user(email=email, password="StrongPass123!", name=email.split("@")[0], role=role)
    return _make


def client_for(user=None):
    client = APIClient()
    if user:
        client.force_authenticate(user)
    return client


PROTECTED_ENDPOINTS = [
    ("get", "/api/auth/profile/"), ("get", "/api/patients/me/"), ("get", "/api/medicines/"),
    ("get", "/api/chat/conversations/"), ("get", "/api/reports/upload/"), ("get", "/api/hospitals/nearby/"),
    ("get", "/api/emergency/info/"), ("get", "/api/emergency/contacts/"), ("get", "/api/health/tips/"),
    ("get", "/api/health/categories/"), ("post", "/api/voice/speak/"), ("get", "/api/doctor/patients/"),
    ("get", "/api/admin/users/"), ("get", "/api/admin/stats/"),
]


@pytest.mark.parametrize("method,url", PROTECTED_ENDPOINTS)
def test_every_private_endpoint_rejects_anonymous_requests(method, url):
    response = getattr(client_for(), method)(url)
    assert response.status_code == 401
    assert response.json()["success"] is False


def test_users_cannot_read_each_others_data(make_user):
    from apps.chat.models import Conversation
    from apps.medicines.models import Medicine
    from apps.reports.models import MedicalReport

    owner, intruder = make_user("owner@example.com"), make_user("intruder@example.com")
    medicine = Medicine.objects.create(user=owner, name="Private")
    conversation = Conversation.objects.create(user=owner, title="Private chat")
    report = MedicalReport.objects.create(
        user=owner, file=SimpleUploadedFile("a.pdf", b"%PDF-1.4"), original_filename="a.pdf", file_type="PDF", file_size=8
    )
    client = client_for(intruder)
    assert client.get(f"/api/medicines/{medicine.id}/").status_code == 404
    assert client.get(f"/api/chat/conversations/{conversation.id}/").status_code == 404
    assert client.get(f"/api/reports/{report.id}/").status_code == 404
    assert client.post(f"/api/reports/{report.id}/process/").status_code == 404
    assert client.post(f"/api/medicines/{medicine.id}/taken/").status_code == 404


def test_cannot_self_register_as_privileged_role():
    response = client_for().post(
        "/api/auth/register/",
        {"name": "Eve", "email": "eve@example.com", "password": "StrongPass123!", "role": "ADMIN", "is_staff": True},
        format="json",
    )
    assert response.status_code == 201
    user = User.objects.get(email="eve@example.com")
    assert user.role == User.Role.PATIENT and not user.is_staff and not user.is_superuser


def test_profile_update_cannot_escalate_role(make_user):
    user = make_user("p@example.com")
    client_for(user).put("/api/auth/profile/", {"role": "ADMIN", "is_active": True, "name": "P"}, format="json")
    user.refresh_from_db()
    assert user.role == User.Role.PATIENT


def test_responses_never_include_password_fields(make_user):
    user = make_user("pw@example.com")
    body = client_for(user).get("/api/auth/profile/").json()
    assert "password" not in str(body).lower()


def test_report_upload_rejects_disguised_and_oversized_files(make_user):
    client = client_for(make_user("up@example.com"))
    fake_png = SimpleUploadedFile("evil.png", b"<script>alert(1)</script>", content_type="image/png")
    assert client.post("/api/reports/upload/", {"file": fake_png}, format="multipart").status_code == 400
    exe = SimpleUploadedFile("run.exe", b"MZ" + b"0" * 20, content_type="application/octet-stream")
    assert client.post("/api/reports/upload/", {"file": exe}, format="multipart").status_code == 400
    big = SimpleUploadedFile("big.pdf", b"%PDF-1.4" + b"0" * (10 * 1024 * 1024 + 1), content_type="application/pdf")
    assert client.post("/api/reports/upload/", {"file": big}, format="multipart").status_code == 400


def test_error_responses_use_the_standard_envelope_without_stack_traces(make_user):
    response = client_for(make_user("e@example.com")).get("/api/medicines/99999/")
    body = response.json()
    assert response.status_code == 404
    assert body["success"] is False and body["error"]["code"]
    assert "Traceback" not in str(body)


def test_failed_logins_are_logged_without_credentials(make_user, caplog):
    make_user("log@example.com")
    with caplog.at_level(logging.INFO, logger="apps.security"):
        client_for().post("/api/auth/login/", {"email": "log@example.com", "password": "wrong-password-1"}, format="json")
        client_for().post("/api/auth/login/", {"email": "log@example.com", "password": "StrongPass123!"}, format="json")
    text = " ".join(record.getMessage() + str(record.__dict__.get("client_ip")) for record in caplog.records)
    assert "Login failed." in text and "Login succeeded." in text
    assert "wrong-password-1" not in text and "StrongPass123!" not in text and "log@example.com" not in text


def test_login_is_rate_limited():
    from django.core.cache import cache

    cache.clear()
    client = client_for()
    codes = [client.post("/api/auth/login/", {"email": "x@example.com", "password": "nope-nope-1"}, format="json").status_code for _ in range(12)]
    cache.clear()
    assert 429 in codes


def test_doctor_cannot_read_chats_or_reports_of_a_granted_patient(make_user):
    from apps.patients.models import PatientAccessGrant

    patient, doctor = make_user("pt@example.com"), make_user("dr@example.com", User.Role.DOCTOR)
    PatientAccessGrant.objects.create(patient=patient, doctor=doctor)
    client = client_for(doctor)
    assert client.get("/api/doctor/patients/").status_code == 200
    assert client.get("/api/chat/conversations/").json()["data"] == []
    assert client.get("/api/reports/upload/").status_code == 403
