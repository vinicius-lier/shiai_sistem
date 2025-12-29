import uuid

from django.test import TestCase

from events.models import Event, EventStatus
from registrations.models import Registration, RegistrationStatus
from brackets.services import generate_brackets_for_event
from brackets.models import BracketFormat
from matches.models import MatchStatus


class BestOf3Tests(TestCase):
    def setUp(self):
        self.event = Event.objects.create(
            id=uuid.uuid4(),
            organization_id=uuid.uuid4(),
            name="Open",
            start_date="2025-01-01",
            end_date="2025-01-02",
            status=EventStatus.CLOSED,
        )

    def test_best_of_3_created_for_two_athletes(self):
        regs = []
        for _ in range(2):
            regs.append(
                Registration.objects.create(
                    id=uuid.uuid4(),
                    event_id=self.event.id,
                    athlete_id=uuid.uuid4(),
                    organization_id=uuid.uuid4(),
                    status=RegistrationStatus.APPROVED,
                    is_confirmed=True,
                    disqualified=False,
                    category_code_final="CAT1",
                    class_code="SUB-13",
                    sex="M",
                    belt_snapshot="BRANCA",
                )
            )
        brackets = generate_brackets_for_event(self.event.id, format_by_category={"CAT1": BracketFormat.BEST_OF_3})
        bracket = brackets[0]
        matches = bracket.matches.order_by("match_number")
        self.assertEqual(matches.count(), 3)
        self.assertTrue(all(m.status == MatchStatus.SCHEDULED for m in matches))

