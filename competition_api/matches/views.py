from django.contrib import messages
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.utils import timezone

from brackets.models import BracketFormat
from matches.models import Match, MatchStatus, WinMethod
from matches.services import record_match_result, advance_single_elimination


def _user_is_table_official(user):
    role = getattr(user, "role", None)
    return role in {"TABLE_OFFICIAL", "OPERATIONS"}


@require_http_methods(["GET", "POST"])
def mesa_matches(request):
    if not request.user.is_authenticated or not _user_is_table_official(request.user):
        return HttpResponseForbidden("Acesso restrito a oficiais de mesa/operacional.")

    if request.method == "POST":
        match_id = request.POST.get("match_id")
        winner_side = request.POST.get("winner_side")
        win_method = request.POST.get("win_method")
        notes = request.POST.get("notes", "")

        match = get_object_or_404(Match, id=match_id, status=MatchStatus.SCHEDULED)

        if winner_side not in {"blue", "white"}:
            messages.error(request, "Selecione o lado vencedor (azul/branco).")
            return HttpResponseRedirect(reverse("matches:mesa"))
        try:
            win_method_enum = WinMethod(win_method)
        except Exception:
            messages.error(request, "Método de vitória inválido.")
            return HttpResponseRedirect(reverse("matches:mesa"))

        winner_athlete_id = match.blue_athlete_id if winner_side == "blue" else match.white_athlete_id
        if not winner_athlete_id:
            messages.error(request, "Lado vencedor sem atleta definido.")
            return HttpResponseRedirect(reverse("matches:mesa"))

        record_match_result(
            match,
            winner_athlete_id=winner_athlete_id,
            win_method=win_method_enum,
            finished_by_user_id=getattr(request.user, "id", None),
            notes=notes,
        )

        bracket = match.bracket
        if bracket and bracket.format == BracketFormat.SINGLE_ELIMINATION:
            advance_single_elimination(bracket, match)

        messages.success(request, "Resultado registrado com sucesso.")
        return HttpResponseRedirect(reverse("matches:mesa"))

    # GET
    qs = Match.objects.filter(status=MatchStatus.SCHEDULED).select_related("bracket")
    event_id = request.GET.get("event_id")
    class_code = request.GET.get("class_code")
    sex = request.GET.get("sex")
    category_code = request.GET.get("category_code")
    bracket_id = request.GET.get("bracket_id")

    if event_id:
        qs = qs.filter(bracket__event_id=event_id)
    if class_code:
        qs = qs.filter(bracket__class_code=class_code)
    if sex:
        qs = qs.filter(bracket__sex=sex)
    if category_code:
        qs = qs.filter(bracket__category_code=category_code)
    if bracket_id:
        qs = qs.filter(bracket_id=bracket_id)

    matches = qs.order_by("bracket__event_id", "bracket__category_code", "round_number", "match_number")
    win_methods = list(WinMethod)

    return render(
        request,
        "matches/mesa.html",
        {
            "matches": matches,
            "win_methods": win_methods,
            "filters": {
                "event_id": event_id or "",
                "class_code": class_code or "",
                "sex": sex or "",
                "category_code": category_code or "",
                "bracket_id": bracket_id or "",
            },
        },
    )


def _apply_match_filters(qs, request):
    event_id = request.GET.get("event_id")
    class_code = request.GET.get("class_code")
    sex = request.GET.get("sex")
    category_code = request.GET.get("category_code")
    belt_group = request.GET.get("belt_group")
    bracket_id = request.GET.get("bracket_id")

    if event_id:
        qs = qs.filter(bracket__event_id=event_id)
    if class_code:
        qs = qs.filter(bracket__class_code=class_code)
    if sex:
        qs = qs.filter(bracket__sex=sex)
    if category_code:
        qs = qs.filter(bracket__category_code=category_code)
    if belt_group:
        qs = qs.filter(bracket__belt_group=belt_group)
    if bracket_id:
        qs = qs.filter(bracket_id=bracket_id)

    filters = {
        "event_id": event_id or "",
        "class_code": class_code or "",
        "sex": sex or "",
        "category_code": category_code or "",
        "belt_group": belt_group or "",
        "bracket_id": bracket_id or "",
    }
    return qs, filters


@require_http_methods(["GET"])
def acompanhamento(request):
    # Read-only board
    qs_all = Match.objects.select_related("bracket")
    qs_all, filters = _apply_match_filters(qs_all, request)

    next_matches = (
        qs_all.filter(status=MatchStatus.SCHEDULED)
        .order_by("bracket__event_id", "bracket__category_code", "round_number", "match_number")[:12]
    )
    recent_matches = (
        qs_all.filter(status__in=[MatchStatus.FINISHED, MatchStatus.WALKOVER])
        .order_by("-finished_at", "-round_number", "-match_number")[:12]
    )

    return render(
        request,
        "matches/acompanhamento.html",
        {
            "filters": filters,
            "event_name": filters.get("event_id") or "-",
            "now_time": timezone.localtime().strftime("%H:%M:%S"),
            "next_matches": next_matches,
            "recent_matches": recent_matches,
            "current_match": None,  # só exibe se o backend sinalizar (mantemos None)
        },
    )


@require_http_methods(["GET"])
def organizacao_mesas(request):
    qs = Match.objects.filter(status=MatchStatus.SCHEDULED).select_related("bracket")
    qs, filters = _apply_match_filters(qs, request)
    matches = qs.order_by("bracket__event_id", "bracket__category_code", "round_number", "match_number")
    return render(request, "matches/mesas.html", {"matches": matches, "filters": filters})
