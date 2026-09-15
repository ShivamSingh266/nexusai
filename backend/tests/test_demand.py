from pathlib import Path

from app.core.demand import DemandSignalStore


DATASET = (
    Path(__file__).resolve().parents[2]
    / "datasets"
    / "processed"
    / "skill_demand_history_2.csv"
)


def test_contextual_lookup_preserves_specific_record() -> None:
    store = DemandSignalStore.from_csv(DATASET)

    signal = store.get(
        "SKILL_0254",
        district="Mumbai City",
        sector="IT/Software - Data & AI",
        period="2025-09",
    )

    assert signal.demand == 0.2895


def test_different_context_returns_different_signal() -> None:
    store = DemandSignalStore.from_csv(DATASET)

    data_ai = store.get(
        "SKILL_0254",
        district="Mumbai City",
        sector="IT/Software - Data & AI",
        period="2025-09",
    )

    cybersecurity = store.get(
        "SKILL_0254",
        district="Mumbai City",
        sector="IT/Software - Cybersecurity",
        period="2025-09",
    )

    assert data_ai.demand == 0.2895
    assert cybersecurity.demand == 0.0109
    assert data_ai.demand != cybersecurity.demand


def test_missing_trend_is_neutral() -> None:
    store = DemandSignalStore.from_csv(DATASET)

    signal = store.get(
        "SKILL_0254",
        district="Mumbai City",
        sector="IT/Software - Data & AI",
        period="2025-10",
    )

    assert signal.demand == 0.0
    assert signal.trend_multiplier == 1.0


def test_unknown_skill_returns_neutral_signal() -> None:
    store = DemandSignalStore.from_csv(DATASET)

    signal = store.get("SKILL_DOES_NOT_EXIST")

    assert signal.demand == 1.0
    assert signal.trend_multiplier == 1.0