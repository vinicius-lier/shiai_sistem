import uuid
from unittest import mock

from django.test import TestCase

from registrations.models import Registration, RegistrationStatus
from registrations.services import register_athlete
from events.models import Event, EventStatus
from contracts.core_read_contract import CoreReadContract
from adapters.exceptions import CoreUnavailableError


class RegisterAthleteBoundaryTests(TestCase):
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

    def _mock_reader(self, org_ok=True, athlete_ok=True, raises=None):
        reader = mock.Mock(spec=CoreReadContract)
        if raises:
            reader.organization_exists_and_active.side_effect = raises
            reader.athlete_belongs_to_org.side_effect = raises
            reader.get_athlete_profile.side_effect = raises
        else:
            reader.organization_exists_and_active.return_value = org_ok
            reader.athlete_belongs_to_org.return_value = athlete_ok
            reader.get_athlete_profile.return_value = {"sex": "M", "belt": "BRANCA"}
        return reader

    def test_fails_when_org_missing_or_inactive(self):
        reader = self._mock_reader(org_ok=False, athlete_ok=True)
        with self.assertRaises(ValueError):
            register_athlete(self.event, self.athlete_id, self.org_id, class_code="SUB-13", core_reader=reader)
        reader.organization_exists_and_active.assert_called_once_with(self.org_id)
        reader.athlete_belongs_to_org.assert_not_called()
        self.assertEqual(Registration.objects.count(), 0)

    def test_fails_when_athlete_not_in_org(self):
        reader = self._mock_reader(org_ok=True, athlete_ok=False)
        with self.assertRaises(ValueError):
            register_athlete(self.event, self.athlete_id, self.org_id, class_code="SUB-13", core_reader=reader)
        reader.organization_exists_and_active.assert_called_once_with(self.org_id)
        reader.athlete_belongs_to_org.assert_called_once_with(self.athlete_id, self.org_id)
        self.assertEqual(Registration.objects.count(), 0)

    def test_fails_fast_when_core_unavailable(self):
        reader = self._mock_reader(raises=CoreUnavailableError("Core down"))
        with self.assertRaises(CoreUnavailableError):
            register_athlete(self.event, self.athlete_id, self.org_id, class_code="SUB-13", core_reader=reader)
        reader.organization_exists_and_active.assert_called_once_with(self.org_id)
        self.assertEqual(Registration.objects.count(), 0)

    def test_success_does_not_write_to_core(self):
        reader = self._mock_reader(org_ok=True, athlete_ok=True)
        registration = register_athlete(self.event, self.athlete_id, self.org_id, class_code="SUB-13", core_reader=reader)
        reader.organization_exists_and_active.assert_called_once_with(self.org_id)
        reader.athlete_belongs_to_org.assert_called_once_with(self.athlete_id, self.org_id)
        self.assertEqual(Registration.objects.count(), 1)
        self.assertEqual(registration.status, RegistrationStatus.PENDING)

