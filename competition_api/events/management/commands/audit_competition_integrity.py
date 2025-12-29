from django.core.management.base import BaseCommand
from django.db import ProgrammingError
from django.db.models import Count, Q

from brackets.models import Bracket, BracketFormat
from matches.models import Match
from registrations.models import Registration


class Command(BaseCommand):
    help = "Auditoria read-only do domínio Competition (brackets, matches, registrations)."

    def handle(self, *args, **options):
        lines = []

        # Duplicatas de Bracket
        try:
            dup_brackets = (
                Bracket.objects.values(
                    "event_id", "category_code", "class_code", "sex", "belt_group"
                )
                .annotate(c=Count("id"))
                .filter(c__gt=1)
            )
            if dup_brackets:
                lines.append("## Problemas críticos")
                lines.append("Brackets duplicados (event, category, class, sex, belt_group):")
                for row in dup_brackets:
                    lines.append(
                        f"- event={row['event_id']} cat={row['category_code']} class={row['class_code']} sex={row['sex']} belt_group={row['belt_group']} count={row['c']}"
                    )
            else:
                lines.append("## Resumo")
                lines.append("- Nenhuma duplicata de Bracket na tupla (event, category, class, sex, belt_group).")
            schema_ok = True
        except ProgrammingError:
            schema_ok = False
            lines.append("## Problemas críticos")
            lines.append("- Auditoria de Brackets não executada: schema desatualizado (aplique migrations de brackets).")

        # Registrations com snapshot incompleto
        if schema_ok:
            bad_regs = Registration.objects.filter(
                is_confirmed=True
            ).filter(Q(class_code__isnull=True) | Q(sex__isnull=True) | Q(belt_snapshot__isnull=True))
            if bad_regs.exists():
                lines.append("\n## Problemas críticos")
                lines.append("Inscrições confirmadas com snapshot incompleto (class_code/sex/belt_snapshot nulos):")
                for r in bad_regs[:50]:
                    lines.append(f"- reg_id={r.id} event={r.event_id} athlete={r.athlete_id}")
                if bad_regs.count() > 50:
                    lines.append(f"... (+{bad_regs.count()-50} adicionais)")

        # Matches órfãos ou phase inválida
        orphan_matches = Match.objects.filter(bracket__isnull=True)
        bad_phase = Match.objects.exclude(
            phase__in=["MAIN", "REPECHAGE", "BRONZE", "FINAL"]
        )
        if orphan_matches.exists() or bad_phase.exists():
            lines.append("\n## Problemas críticos")
            if orphan_matches.exists():
                lines.append("Matches órfãos (sem bracket):")
                for m in orphan_matches[:50]:
                    lines.append(f"- match_id={m.id}")
                if orphan_matches.count() > 50:
                    lines.append(f"... (+{orphan_matches.count()-50} adicionais)")
            if bad_phase.exists():
                lines.append("Matches com phase inválida:")
                for m in bad_phase[:50]:
                    lines.append(f"- match_id={m.id} phase={m.phase}")
                if bad_phase.count() > 50:
                    lines.append(f"... (+{bad_phase.count()-50} adicionais)")
        else:
            lines.append("\n- Matches sem órfãos e phases válidas.")

        # Repescagem incompleta (heurística)
        rep_incomplete = []
        rep_brackets = []
        if schema_ok:
            rep_brackets = Bracket.objects.filter(format=BracketFormat.ELIMINATION_WITH_REPECHAGE)
            for b in rep_brackets:
                has_rep = b.matches.filter(phase="REPECHAGE").exists()
                has_bronze = b.matches.filter(phase="BRONZE").count() >= 2
                if not has_rep or not has_bronze:
                    rep_incomplete.append((b.id, has_rep, has_bronze))
        if rep_incomplete:
            lines.append("\n## Avisos")
            lines.append("Brackets ELIMINATION_WITH_REPECHAGE sem repescagem/bronzes completos:")
            for bid, rep_ok, bronze_ok in rep_incomplete:
                lines.append(f"- bracket_id={bid} repescagem={rep_ok} bronzes={bronze_ok}")
        elif schema_ok:
            lines.append("\n- Repescagem: nenhuma inconformidade encontrada (ou não há brackets neste formato).")

        # Output
        self.stdout.write("\n".join(lines))

