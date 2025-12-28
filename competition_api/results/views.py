from django.contrib import messages
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from results.models import OfficialResult
from results.services import generate_official_results_for_event
from matches.models import MatchStatus, Match


@require_http_methods(["GET", "POST"])
def oficiais(request):
    event_id = request.GET.get("event_id") or request.POST.get("event_id")
    results = []
    scheduled_count = None

    if request.method == "POST":
        if not event_id:
            messages.error(request, "Informe o event_id para gerar resultados oficiais.")
        else:
            scheduled_count = Match.objects.filter(
                bracket__event_id=event_id, status=MatchStatus.SCHEDULED
            ).count()
            if scheduled_count and scheduled_count > 0:
                messages.error(request, "Existem lutas SCHEDULED. Finalize antes de gerar resultados oficiais.")
            else:
                try:
                    generate_official_results_for_event(event_id)
                    messages.success(request, "Resultados oficiais gerados com sucesso.")
                except Exception as exc:
                    messages.error(request, f"Não foi possível gerar resultados oficiais: {exc}")

    if event_id:
        results = OfficialResult.objects.filter(event_id=event_id).order_by("category_code", "placement")
        if scheduled_count is None:
            scheduled_count = Match.objects.filter(
                bracket__event_id=event_id, status=MatchStatus.SCHEDULED
            ).count()

    return render(
        request,
        "results/oficiais.html",
        {
            "event_id": event_id or "",
            "results": results,
            "scheduled_count": scheduled_count,
        },
    )

