import uuid

from django.test import TestCase

from events.models import Event, EventStatus
from registrations.models import Registration, RegistrationStatus
from matches.models import MatchStatus, WinMethod
from matches.services import record_match_result, fight_points, void_match
from brackets.models import Bracket, BracketFormat
from brackets.services import generate_brackets_for_event


class MatchesFlowTests(TestCase):
    def setUp(self):
        self.event = Event.objects.create(
            id=uuid.uuid4(),
            organization_id=uuid.uuid4(),
            name="Open",
            start_date="2025-01-01",
            end_date="2025-01-02",
            status=EventStatus.CLOSED,
        )
        self.regs = []
        for i in range(4):
            self.regs.append(
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
        self.brackets = generate_brackets_for_event(self.event.id, format_by_category={"CAT1": BracketFormat.SINGLE_ELIMINATION})
        self.bracket = self.brackets[0]
        self.match1 = self.bracket.matches.filter(round_number=1, match_number=1).first()
        self.match2 = self.bracket.matches.filter(round_number=1, match_number=2).first()
        self.final = self.bracket.matches.filter(round_number=2, match_number=1).first()

    def test_record_result_sets_points(self):
        match = record_match_result(
            self.match1,
            winner_athlete_id=self.match1.blue_athlete_id,
            win_method=WinMethod.IPPON,
            finished_by_user_id=uuid.uuid4(),
        )
        self.assertEqual(match.status, MatchStatus.FINISHED)
        self.assertEqual(match.fight_points_winner, fight_points(WinMethod.IPPON))

    def test_cannot_record_twice(self):
        record_match_result(
            self.match1,
            winner_athlete_id=self.match1.blue_athlete_id,
            win_method=WinMethod.IPPON,
            finished_by_user_id=uuid.uuid4(),
        )
        self.match1.refresh_from_db()
        with self.assertRaises(ValueError):
            record_match_result(
                self.match1,
                winner_athlete_id=self.match1.blue_athlete_id,
                win_method=WinMethod.WO,
                finished_by_user_id=uuid.uuid4(),
            )

    def test_void_changes_status(self):
        void_match(self.match1, reason="Erro de súmula", finished_by_user_id=uuid.uuid4())
        self.match1.refresh_from_db()
        self.assertEqual(self.match1.status, MatchStatus.WALKOVER)

