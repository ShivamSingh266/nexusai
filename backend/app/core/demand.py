from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class DemandSignal:
    """Demand signal for one skill in one market context."""
    demand: float = 1.0
    trend_multiplier: float = 1.0
    district: Optional[str] = None
    sector: Optional[str] = None
    period: Optional[str] = None


def _safe_float(value: str | None, default: float = 0.0) -> float:
    if value is None or value == "":
        return default

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _trend_multiplier(recent_growth: str | None) -> float:
    """
    Provisional conversion until Member 6's forecast/trend contract is wired in.

    Missing growth means neutral trend (1.0).
    Negative growth cannot reduce the multiplier below 0.
    """
    growth = _safe_float(recent_growth, default=0.0)
    return max(0.0, 1.0 + growth)


class DemandSignalStore:
    """
    Context-aware demand lookup.

    Records are indexed by:
        skill_id + district + sector + period

    A skill-only lookup is retained as a fallback by aggregating the
    available contextual records instead of allowing the last CSV row
    to overwrite earlier rows.
    """

    def __init__(self) -> None:
        self._records: dict[tuple[str, str | None, str | None, str | None], DemandSignal] = {}
        self._by_skill: dict[str, list[DemandSignal]] = {}

    @classmethod
    def from_csv(cls, path: str | Path) -> "DemandSignalStore":
        store = cls()

        with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)

            required = {
                "skill_id",
                "district_id",
                "sector",
                "period",
                "demand_score",
                "recent_growth",
            }

            missing = required - set(reader.fieldnames or [])
            if missing:
                raise ValueError(
                    f"Demand CSV is missing required columns: {sorted(missing)}"
                )

            for row in reader:
                skill_id = (row.get("skill_id") or "").strip()
                if not skill_id:
                    continue

                district = (row.get("district_id") or "").strip() or None
                sector = (row.get("sector") or "").strip() or None
                period = (row.get("period") or "").strip() or None

                signal = DemandSignal(
                    demand=_safe_float(row.get("demand_score"), default=0.0),
                    trend_multiplier=_trend_multiplier(row.get("recent_growth")),
                    district=district,
                    sector=sector,
                    period=period,
                )

                key = (skill_id, district, sector, period)
                store._records[key] = signal
                store._by_skill.setdefault(skill_id, []).append(signal)

        return store

    def get(
        self,
        skill_id: str,
        *,
        district: str | None = None,
        sector: str | None = None,
        period: str | None = None,
    ) -> DemandSignal:
        """
        Return the best matching contextual signal.

        Exact context is preferred. If no exact record exists, progressively
        fall back to less-specific records. Finally, aggregate all records
        for the skill.
        """
        skill_id = skill_id.strip()

        candidates = [
            (skill_id, district, sector, period),
            (skill_id, district, sector, None),
            (skill_id, district, None, period),
            (skill_id, None, sector, period),
            (skill_id, district, None, None),
            (skill_id, None, sector, None),
            (skill_id, None, None, period),
        ]

        for key in candidates:
            signal = self._records.get(key)
            if signal is not None:
                return signal

        return self._aggregate_skill(skill_id)

    def _aggregate_skill(self, skill_id: str) -> DemandSignal:
        records = self._by_skill.get(skill_id)

        if not records:
            return DemandSignal()

        demand_values = [record.demand for record in records]
        trend_values = [record.trend_multiplier for record in records]

        return DemandSignal(
            demand=sum(demand_values) / len(demand_values),
            trend_multiplier=sum(trend_values) / len(trend_values),
        )