from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class SupplierRecord:
    supplier_id: str
    annual_spend_eur: float
    activity_quantity: float | None
    activity_factor_kgco2e: float | None
    spend_factor_kgco2e_per_eur: float
    reported_emissions_kgco2e: float | None
    climate_hazard: float
    water_stress: float
    biodiversity_pressure: float
    human_rights_risk: float
    evidence_completeness: float
    remediation_open: bool = False

    def validate(self) -> None:
        if not self.supplier_id or self.annual_spend_eur < 0:
            raise ValueError("supplier_id and non-negative spend are required")
        for name in ("climate_hazard", "water_stress", "biodiversity_pressure", "human_rights_risk", "evidence_completeness"):
            value = getattr(self, name)
            if not 0 <= value <= 1:
                raise ValueError(f"{name} must be between 0 and 1")
        if (self.activity_quantity is None) != (self.activity_factor_kgco2e is None):
            raise ValueError("activity quantity and factor must be provided together")


class SustainabilityEngine:
    def __init__(self, suppliers: Iterable[SupplierRecord]):
        self.suppliers = tuple(suppliers)
        if not self.suppliers:
            raise ValueError("at least one supplier is required")
        for supplier in self.suppliers:
            supplier.validate()

    def emissions(self, supplier: SupplierRecord) -> dict[str, object]:
        if supplier.reported_emissions_kgco2e is not None:
            value, method, quality, uncertainty = supplier.reported_emissions_kgco2e, "supplier-reported", "A", 0.10
        elif supplier.activity_quantity is not None:
            value = supplier.activity_quantity * supplier.activity_factor_kgco2e
            method, quality, uncertainty = "activity-based", "B", 0.25
        else:
            value = supplier.annual_spend_eur * supplier.spend_factor_kgco2e_per_eur
            method, quality, uncertainty = "spend-based", "C", 0.50
        return {
            "kgco2e": round(value, 2),
            "method": method,
            "quality_tier": quality,
            "range_kgco2e": [round(value * (1 - uncertainty), 2), round(value * (1 + uncertainty), 2)],
        }

    def assess(self, supplier_id: str) -> dict[str, object]:
        supplier = next((x for x in self.suppliers if x.supplier_id == supplier_id), None)
        if supplier is None:
            raise KeyError(supplier_id)
        footprint = self.emissions(supplier)
        environmental = (supplier.climate_hazard + supplier.water_stress + supplier.biodiversity_pressure) / 3
        uncertainty = 1 - supplier.evidence_completeness
        components = {
            "environmental": environmental,
            "human_rights": supplier.human_rights_risk,
            "evidence_uncertainty": uncertainty,
            "remediation": 0.9 if supplier.remediation_open else 0.1,
        }
        score = 100 * (0.35 * environmental + 0.35 * supplier.human_rights_risk + 0.2 * uncertainty + 0.1 * components["remediation"])
        reasons = [key.upper() for key, value in components.items() if value >= 0.6]
        return {
            "supplier_id": supplier_id,
            "priority_score": round(score, 1),
            "priority_band": "critical" if score >= 70 else "high" if score >= 50 else "medium" if score >= 30 else "low",
            "components": {key: round(value, 3) for key, value in components.items()},
            "reason_codes": reasons,
            "emissions": footprint,
        }

    def action_queue(self) -> list[dict[str, object]]:
        actions = []
        for supplier in self.suppliers:
            assessment = self.assess(supplier.supplier_id)
            action = "verify evidence"
            if supplier.human_rights_risk >= 0.7:
                action = "initiate enhanced human-rights due diligence"
            elif supplier.water_stress >= 0.7:
                action = "request site-level water mitigation plan"
            elif assessment["emissions"]["quality_tier"] == "C":
                action = "request supplier-specific activity data"
            actions.append(assessment | {"recommended_action": action})
        return sorted(actions, key=lambda row: row["priority_score"], reverse=True)

    def scenario(self, renewable_uplift: float) -> dict[str, float]:
        if not 0 <= renewable_uplift <= 1:
            raise ValueError("renewable_uplift must be between 0 and 1")
        baseline = sum(self.emissions(x)["kgco2e"] for x in self.suppliers)
        avoided = baseline * renewable_uplift * 0.35
        return {"baseline_kgco2e": round(baseline, 2), "avoided_kgco2e": round(avoided, 2), "residual_kgco2e": round(baseline - avoided, 2)}

    def records(self) -> list[dict[str, object]]:
        return [asdict(x) for x in self.suppliers]


def demo_engine() -> SustainabilityEngine:
    return SustainabilityEngine([
        SupplierRecord("wafer-chem-a", 2_000_000, 800_000, 1.8, 0.6, None, 0.35, 0.75, 0.45, 0.25, 0.8),
        SupplierRecord("assembly-b", 1_300_000, None, None, 0.72, None, 0.70, 0.50, 0.60, 0.78, 0.4, True),
        SupplierRecord("logistics-c", 600_000, None, None, 0.31, 160_000, 0.25, 0.30, 0.20, 0.20, 0.95),
    ])

