"""Gemeinsame Fixtures: die Mini-Instanz, an der jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ski_scenario import Szenario  # noqa: E402


@pytest.fixture
def mini():
    """Kaufpreis B = 4, der Auftrag endet nach genau 4 Tagen. Handrechnung: Break-even mietet an den Tagen 1 bis 3 (3) und kauft am Tag 4 (4): 7 statt 4, Quotient 7/4."""
    return Szenario(4, "fest", 4)
