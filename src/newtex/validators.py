import re

KEBAB_CASE_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def is_kebab_case(name: str) -> bool:
    return bool(KEBAB_CASE_PATTERN.fullmatch(name))


def suggest_kebab_case(name: str) -> str:
    s = name.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s
