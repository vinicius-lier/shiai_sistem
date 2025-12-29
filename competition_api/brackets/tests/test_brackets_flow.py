import uuid

from django.test import TestCase

from events.models import Event, EventStatus
from registrations.models import Registration, RegistrationStatus
from brackets.services import generate_brackets_for_event, compute_round_robin_standings
from brackets.models import BracketFormat
from matches.services import record_match_result
from matches.models import WinMethod


class BracketsFlowTests(TestCase):
    def setUp(self):
        self.event = Event.objects.create(
            id=uuid.uuid4(),
            organization_id=uuid.uuid4(),
            name="Open",
            start_date="2025-01-01",
            end_date="2025-01-02",
            status=EventStatus.CLOSED,
        )

    def _create_regs(self, category_code, n):
        regs = []
        for _ in range(n):
            regs.append(
                Registration.objects.create(
                    id=uuid.uuid4(),
                    event_id=self.event.id,
                    athlete_id=uuid.uuid4(),
                    organization_id=uuid.uuid4(),
                    status=RegistrationStatus.APPROVED,
                    is_confirmed=True,
                    disqualified=False,
                    category_code_final=category_code,
                    class_code="SUB-13",
                    sex="M",
                    belt_snapshot="BRANCA",
                )
            )
        return regs

    def test_generate_bracket_single_elim_with_4(self):
        self._create_regs("CAT1", 4)
        brackets = generate_brackets_for_event(self.event.id, format_by_category={"CAT1": BracketFormat.SINGLE_ELIMINATION})
        self.assertEqual(len(brackets), 1)
        bracket = brackets[0]
        matches = bracket.matches.order_by("round_number", "match_number")
        self.assertEqual(matches.count(), 3)  # 2 semis + 1 final

    def test_round_robin_standings_with_head_to_head(self):
        regs = self._create_regs("CAT2", 3)
        brackets = generate_brackets_for_event(self.event.id, format_by_category={"CAT2": BracketFormat.ROUND_ROBIN})
        bracket = brackets[0]
        matches = list(bracket.matches.all())

        # three matches pairwise
        m1 = matches[0]
        m1.blue_athlete_id = regs[0].athlete_id
        m1.white_athlete_id = regs[1].athlete_id
        m1.save(update_fields=["blue_athlete_id", "white_athlete_id"])
        record_match_result(m1, winner_athlete_id=regs[0].athlete_id, win_method=WinMethod.IPPON)

        m2 = matches[1]
        m2.blue_athlete_id = regs[1].athlete_id
        m2.white_athlete_id = regs[2].athlete_id
        m2.save(update_fields=["blue_athlete_id", "white_athlete_id"])
        record_match_result(m2, winner_athlete_id=regs[1].athlete_id, win_method=WinMethod.WAZA_ARI)

        m3 = matches[2]
        m3.blue_athlete_id = regs[2].athlete_id
        m3.white_athlete_id = regs[0].athlete_id
        m3.save(update_fields=["blue_athlete_id", "white_athlete_id"])
        record_match_result(m3, winner_athlete_id=regs[2].athlete_id, win_method=WinMethod.YUKO)

        standings = compute_round_robin_standings(bracket)
        self.assertEqual(len(standings), 3)
        # wins are all 1, so tiebreaker by fight_points then head-to-head
        wins = [s["wins"] for s in standings]
        self.assertTrue(all(w == 1 for w in wins))
        # ensure ordering is deterministic with head-to-head resolution path
        self.assertEqual(sorted([s["athlete_id"] for s in standings]), sorted([r.athlete_id for r in regs]))

