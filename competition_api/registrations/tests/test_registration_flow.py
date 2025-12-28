import uuid
from unittest import mock

from django.test import TestCase
from django.utils import timezone

from registrations.models import Registration, RegistrationStatus
from registrations.services import (
    request_registration,
    register_athlete_operational,
    confirm_registration,
)
from events.models import Event, EventStatus
from contracts.core_read_contract import CoreReadContract


class RegistrationFlowTests(TestCase):
    def setUp(self):
        self.event = Event.objects.create(
            id=uuid.uuid4(),
            organization_id=uuid.uuid4(),
            name="Open",
            start_date="2025-01-01",
            end_date="2025-01-02",
            status=EventStatus.OPEN,
        )
        self.org_id = uuid.uuid4()
        self.athlete_id = uuid.uuid4()
        self.user_id = uuid.uuid4()

    def _reader(self):
        reader = mock.Mock(spec=CoreReadContract)
        reader.organization_exists_and_active.return_value = True
        reader.athlete_belongs_to_org.return_value = True
        reader.get_athlete_profile.return_value = {"sex": "M", "belt": "BRANCA"}
        return reader

    def test_request_registration_creates_pending_unconfirmed(self):
        reg = request_registration(
            event=self.event,
            athlete_id=self.athlete_id,
            organization_id=self.org_id,
            class_code="SUB-13",
            requested_by_user_id=self.user_id,
            category_code_requested="CAT1",
            core_reader=self._reader(),
        )
        self.assertFalse(reg.is_confirmed)
        self.assertEqual(reg.status, RegistrationStatus.PENDING)
        self.assertEqual(reg.category_code_requested, "CAT1")

    def test_register_operational_creates_confirmed(self):
        now_before = timezone.now()
        reg = register_athlete_operational(
            event=self.event,
            athlete_id=self.athlete_id,
            organization_id=self.org_id,
            class_code="SUB-13",
            requested_by_user_id=self.user_id,
            category_code_requested="CAT1",
            confirmed_by_user_id=self.user_id,
            core_reader=self._reader(),
        )
        self.assertTrue(reg.is_confirmed)
        self.assertEqual(reg.status, RegistrationStatus.PENDING)
        self.assertIsNotNone(reg.confirmed_at)
        self.assertGreaterEqual(reg.confirmed_at, now_before)

    def test_confirm_registration_sets_flags(self):
        reg = request_registration(
            event=self.event,
            athlete_id=self.athlete_id,
            organization_id=self.org_id,
            requested_by_user_id=self.user_id,
            category_code_requested="CAT1",
            core_reader=self._reader(),
        )
        reg = confirm_registration(reg, confirmed_by_user_id=self.user_id)
        self.assertTrue(reg.is_confirmed)
        self.assertIsNotNone(reg.confirmed_at)
        self.assertEqual(reg.confirmed_by_user_id, self.user_id)

