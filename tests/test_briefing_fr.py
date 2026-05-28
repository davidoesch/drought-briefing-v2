# tests/test_briefing_fr.py
from src.briefing.text_blocks_fr import (
    LAGE_BLOCKS,
    ENTWICKLUNG_BLOCKS,
    EINORDNUNG_BLOCKS,
    DATENGRUNDLAGE_BLOCKS,
)


def test_fr_lage_blocks_has_both_modes():
    assert "behoerden" in LAGE_BLOCKS
    assert "bulletin" in LAGE_BLOCKS


def test_fr_lage_blocks_has_all_cdi_levels():
    for mode in ("behoerden", "bulletin"):
        assert set(LAGE_BLOCKS[mode].keys()) == set(range(6))


def test_fr_entwicklung_blocks_has_both_modes():
    assert "behoerden" in ENTWICKLUNG_BLOCKS
    assert "bulletin" in ENTWICKLUNG_BLOCKS


def test_fr_einordnung_blocks_has_both_modes():
    assert "behoerden" in EINORDNUNG_BLOCKS
    assert "bulletin" in EINORDNUNG_BLOCKS


def test_fr_datengrundlage_blocks_has_both_modes():
    assert "behoerden" in DATENGRUNDLAGE_BLOCKS
    assert "bulletin" in DATENGRUNDLAGE_BLOCKS


def test_fr_blocks_contain_french_word():
    assert "sécheresse" in LAGE_BLOCKS["bulletin"][0].lower() or \
           "sécheresse" in LAGE_BLOCKS["bulletin"][1].lower()
