BELT_ORDER = [
    "BRANCA",
    "P_CINZA",
    "CINZA",
    "P_AZUL",
    "AZUL",
    "P_AMARELA",
    "AMARELA",
    "P_LARANJA",
    "LARANJA",
    "VERDE",
    "ROXA",
    "MARROM",
    "PRETA",
]

BELT_INDEX = {name: idx for idx, name in enumerate(BELT_ORDER)}


def normalize_belt(belt: str) -> str | None:
    if not belt:
        return None
    belt = belt.strip().upper().replace(".", "_").replace(" ", "_")
    return belt


def resolve_belt_group(class_code: str, sex: str, belt: str) -> int | None:
    belt_norm = normalize_belt(belt)
    if belt_norm not in BELT_INDEX:
        return None

    cls = canonical_class_code(class_code)
    if not cls or not sex:
        return None
    sex = sex.upper()

    def in_range(min_b, max_b):
        return BELT_INDEX[belt_norm] >= BELT_INDEX[min_b] and BELT_INDEX[belt_norm] <= BELT_INDEX[max_b]

    # Grupo 1: BRANCA -> CINZA / P_CINZA -> P_AZUL (AULAO; SUB-9/10/11)
    if cls in {"AULAO", "SUB-9", "SUB-10", "SUB-11"} and in_range("BRANCA", "P_AZUL"):
        if BELT_INDEX[belt_norm] <= BELT_INDEX["P_AZUL"]:
            # Grupo 1 inicia em Branca até P_AZUL inclusive
            # Grupo 2 vai até P_LARANJA, mas 1 cobre BRANCA..P_AZUL; decisão final no allowed set
            pass
    # Grupo 2: BRANCA -> P_LARANJA (SUB-9/10/11)
    if cls in {"SUB-9", "SUB-10", "SUB-11"} and in_range("BRANCA", "P_LARANJA"):
        return 2 if BELT_INDEX[belt_norm] > BELT_INDEX["P_AZUL"] else 1

    # Grupo 1 fallback (AULAO)
    if cls == "AULAO" and in_range("BRANCA", "P_AZUL"):
        return 1

    # Grupo 3: BRANCA -> AZUL (SUB-13)
    if cls == "SUB-13" and in_range("BRANCA", "AZUL"):
        return 3
    # Grupo 4: BRANCA -> LARANJA (SUB-13)
    if cls == "SUB-13" and in_range("BRANCA", "LARANJA"):
        return 4

    # Grupo 5: BRANCA -> P_AMARELA (SUB-15)
    if cls == "SUB-15" and in_range("BRANCA", "P_AMARELA"):
        return 5
    # Grupo 6: BRANCA -> VERDE (SUB-15)
    if cls == "SUB-15" and in_range("BRANCA", "VERDE"):
        return 6 if BELT_INDEX[belt_norm] > BELT_INDEX["P_AMARELA"] else 5

    # Grupo 7: Adulto Formação (SUB-18/21/SENIOR/VETERANO)
    if cls in {"SUB-18", "SUB-21", "SENIOR", "VETERANO"}:
        if sex == "F" and in_range("BRANCA", "LARANJA"):
            return 7
        if sex == "M" and in_range("BRANCA", "VERDE"):
            return 7
        # Grupo 8: Adulto Avançado
        if sex == "F" and in_range("VERDE", "PRETA"):
            return 8
        if sex == "M" and in_range("ROXA", "PRETA"):
            return 8

    return None


def allowed_groups_for_class(class_code: str) -> set[int]:
    cls = canonical_class_code(class_code)
    if cls == "AULAO":
        return {1}
    if cls in {"SUB-9", "SUB-10", "SUB-11"}:
        return {1, 2}
    if cls == "SUB-13":
        return {3, 4}
    if cls == "SUB-15":
        return {5, 6}
    if cls in {"SUB-18", "SUB-21", "SENIOR", "VETERANO"}:
        return {7, 8}
    return set()


def canonical_class_code(class_code: str) -> str | None:
    if not class_code:
        return None
    c = class_code.strip().upper()
    if c in {"AULAO", "FESTIVAL", "CHUPETINHA"}:
        return "AULAO"
    if c in {"ADULTO", "SENIOR", "SÊNIOR"}:
        return "SENIOR"
    if c in {"MASTER", "VETERANO"}:
        return "VETERANO"
    return c

