import uuid

from django.test import TestCase

from registrations.models import Registration, RegistrationStatus
from events.models import Event, EventStatus
from categories.models import CategoryRule
from weighings.services import record_weighing_with_rules, OutOfRangeDecision


class WeighingFlowTests(TestCase):
    def setUp(self):
        self.event = Event.objects.create(
            id=uuid.uuid4(),
            organization_id=uuid.uuid4(),
            name="Open",
            start_date="2025-01-01",
            end_date="2025-01-02",
            status=EventStatus.OPEN,
        )
        self.reg = Registration.objects.create(
            id=uuid.uuid4(),
            event_id=self.event.id,
            athlete_id=uuid.uuid4(),
            organization_id=uuid.uuid4(),
            status=RegistrationStatus.PENDING,
            is_confirmed=True,
            category_code_requested="CAT1",
        )
        self.rule = CategoryRule.objects.create(
            sex="M",
            class_code="ADULT",
            category_code="CAT1",
            min_weight=60,
            max_weight=70,
            is_active=True,
        )

    def test_requires_confirmed_registration(self):
        self.reg.is_confirmed = False
        self.reg.save(update_fields=["is_confirmed"])
        with self.assertRaises(ValueError):
            record_weighing_with_rules(self.reg, weight=65, sex="M", class_code="ADULT", decision_if_out_of_range=OutOfRangeDecision.REMATCH)

    def test_rematch_out_of_range_applies_penalty_and_final_category(self):
        CategoryRule.objects.create(
            sex="M",
            class_code="ADULT",
            category_code="CAT2",
            min_weight=70,
            max_weight=80,
            is_active=True,
        )
        weighing = record_weighing_with_rules(
            self.reg,
            weight=72,
            sex="M",
            class_code="ADULT",
            decision_if_out_of_range=OutOfRangeDecision.REMATCH,
        )
        self.reg.refresh_from_db()
        self.assertIsNotNone(weighing)
        self.assertEqual(self.reg.category_code_final, "CAT2")
        self.assertTrue(self.reg.was_rematched)
        self.assertEqual(self.reg.event_penalty_points, -1)
        self.assertEqual(self.reg.status, RegistrationStatus.WEIGHED)

    def test_disqualify_out_of_range_blocks_registration(self):
        result = record_weighing_with_rules(
            self.reg,
            weight=75,  # out of range and no matching rule (CAT2 not created here)
            sex="M",
            class_code="ADULT",
            decision_if_out_of_range=OutOfRangeDecision.DISQUALIFY,
        )
        self.reg.refresh_from_db()
        self.assertIsNone(result)
        self.assertTrue(self.reg.disqualified)
        self.assertEqual(self.reg.disqualified_reason, "WEIGHT_OUT_OF_RANGE")
        self.assertEqual(self.reg.status, RegistrationStatus.BLOCKED)

