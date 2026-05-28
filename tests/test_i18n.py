# tests/test_i18n.py
from config.settings import BERNE_REGION_NAMES_FR, CDI_LABELS_FR


def test_fr_region_names_has_all_berne_regions():
    from config.settings import BERNE_REGION_IDS
    assert set(BERNE_REGION_NAMES_FR.keys()) == BERNE_REGION_IDS


def test_fr_cdi_labels_has_all_levels():
    assert set(CDI_LABELS_FR.keys()) == set(range(6))


def test_fr_region_34_is_mittelland():
    assert BERNE_REGION_NAMES_FR[34] == "Mittelland bernois"


def test_fr_cdi_label_0_is_no_drought():
    assert CDI_LABELS_FR[0] == "Pas de sécheresse"


from src.i18n.strings import t, get_cdi_labels, get_region_names


def test_t_returns_german_for_de():
    assert t("section_lage", "de") == "Lage"


def test_t_returns_french_for_fr():
    assert t("section_lage", "fr") == "Situation"


def test_t_falls_back_for_unknown_lang():
    assert t("section_lage", "it") == "Lage"


def test_t_returns_key_for_unknown_key():
    assert t("__nonexistent__", "de") == "__nonexistent__"


def test_get_cdi_labels_de():
    labels = get_cdi_labels("de")
    assert labels[0] == "Keine Trockenheit"


def test_get_cdi_labels_fr():
    labels = get_cdi_labels("fr")
    assert labels[0] == "Pas de sécheresse"


def test_get_region_names_de():
    names = get_region_names("de")
    assert names[34] == "Berner Mittelland"


def test_get_region_names_fr():
    names = get_region_names("fr")
    assert names[34] == "Mittelland bernois"
