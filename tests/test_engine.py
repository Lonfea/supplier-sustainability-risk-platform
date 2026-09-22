import pytest

from sustainability.engine import SupplierRecord, SustainabilityEngine, demo_engine


def test_emission_method_hierarchy():
    engine = demo_engine()
    rows = {row.supplier_id: row for row in engine.suppliers}
    assert engine.emissions(rows["logistics-c"])["quality_tier"] == "A"
    assert engine.emissions(rows["wafer-chem-a"])["quality_tier"] == "B"
    assert engine.emissions(rows["assembly-b"])["quality_tier"] == "C"


def test_action_queue_is_descending_and_explainable():
    queue = demo_engine().action_queue()
    scores = [row["priority_score"] for row in queue]
    assert scores == sorted(scores, reverse=True)
    assert all(row["recommended_action"] and row["components"] for row in queue)


def test_scenario_is_conservative_and_bounded():
    result = demo_engine().scenario(0.5)
    assert 0 < result["avoided_kgco2e"] < result["baseline_kgco2e"]
    with pytest.raises(ValueError):
        demo_engine().scenario(1.2)


def test_invalid_partial_activity_data_rejected():
    bad = SupplierRecord("bad", 1, 1, None, 1, None, 0, 0, 0, 0, 1)
    with pytest.raises(ValueError):
        SustainabilityEngine([bad])

