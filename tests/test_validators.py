from newtex.validators import is_kebab_case, suggest_kebab_case


def test_is_kebab_case_valid() -> None:
    assert is_kebab_case("exlang-paper") is True


def test_is_kebab_case_invalid() -> None:
    assert is_kebab_case("Exlang_Paper") is False


def test_suggest_kebab_case() -> None:
    assert suggest_kebab_case("  Exlang Paper 2026  ") == "exlang-paper-2026"
