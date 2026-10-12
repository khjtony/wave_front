"""Shared fixtures: the toy model's bundle is computed once per test session."""

import pytest

from models.toy.two_power import model as toy

TOY_ENDINGS = ["TAKEOVER", "SETTLED", "CONTAINED", "COEXIST", "HORIZON"]
TOY_COALITIONS = [["INC"], ["CH"], ["CH", "INC"]]


@pytest.fixture(scope="session")
def toy_bundle():
    """The toy rendered as in docs/visualizer.md section 9: coalition {INC} and ending
    TAKEOVER first (so the page opens on them), every other ending and coalition after."""
    from wavefront.viz import bundle

    return bundle(toy, coalitions=TOY_COALITIONS, endings=TOY_ENDINGS, max_relax=1)
