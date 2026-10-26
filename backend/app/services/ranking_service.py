from typing import List, Dict, Any, Optional
from app.services.cost_service import compute_tco
from app.services.compliance_service import audit_compliance

def calculate_evaluations(
    rfq: Dict[str, Any],
    vendors_map: Dict[str, Dict[str, Any]],
    quotations: List[Dict[str, Any]],
    weights: Dict[str, float],
    max_budget_limit: Optional[float] = None,
    max_lead_time_days: Optional[int] = None,
    min_warranty_months: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Deterministically computes scores, Landed Cost, TCO, delivery, warranty, compliance, risk, and rank.
    Fast in-memory recalculation without re-extracting quotations.
    """
    if not quotations:
        return []

    preliminary = []
    for q in quotations:
        vendor = vendors_map.get(q["vendor_id"])
        if not vendor:
            continue
        
        hidden_fee = float(q.get("hidden_fee", 0.0))
        tco_data = compute_tco(
            base_quote_amount=q["total_quote_amount"],
            shipping_fee=q.get("shipping_fee", 0.0),
            tax_amount=q.get("tax_amount", 0.0),
            quote_lead_time=q["lead_time_days"],
            rfq_deadline=rfq["deadline_days"],
            quote_warranty_months=q["warranty_months"],
            rfq_min_warranty=rfq.get("min_warranty_months", 12),
            hidden_fee=hidden_fee
        )
        
        audit_res = audit_compliance(vendor, q, rfq)
        preliminary.append({
            "vendor": vendor,
            "quotation": q,
            "tco_data": tco_data,
            "audit": audit_res
        })

    if not preliminary:
        return []

    # Minimum landed cost and minimum TCO across suppliers for relative normalization
    min_tco = min(p["tco_data"]["total_tco"] for p in preliminary)

    w_price = float(weights.get("price", 0.40))
    w_delivery = float(weights.get("delivery", 0.25))
    w_quality = float(weights.get("quality", 0.20))
    w_compliance = float(weights.get("compliance", 0.15))
    
    # Normalize weights if sum != 1.0
    w_sum = w_price + w_delivery + w_quality + w_compliance
    if w_sum > 0:
        w_price /= w_sum
        w_delivery /= w_sum
        w_quality /= w_sum
        w_compliance /= w_sum

    evaluations = []
    for p in preliminary:
        vendor = p["vendor"]
        q = p["quotation"]
        tco_data = p["tco_data"]
        tco = tco_data["total_tco"]
        landed_cost = tco_data["landed_cost"]
        audit = p["audit"]
        
        # 1. Price Score (best TCO gets 100, higher price proportionally lower)
        price_score = round(100.0 * (min_tco / tco), 2)

        # 2. Delivery Score
        rfq_deadline = max(1, rfq["deadline_days"])
        delay = max(0, q["lead_time_days"] - rfq_deadline)
        speed_factor = max(0.0, 1.0 - (delay / rfq_deadline))
        on_time_factor = float(vendor.get("historical_on_time_rate", 90.0)) / 100.0
        delivery_score = round(100.0 * speed_factor * on_time_factor, 2)

        # 3. Quality & Reputation Score
        rating = float(vendor.get("rating", 4.0))
        tier_bonus = 30.0 if vendor.get("tier") == "Tier-1" else 20.0
        quality_score = round((rating / 5.0) * 70.0 + tier_bonus, 2)

        # 4. Compliance Score
        compliance_score = float(audit["score"])

        # 5. Composite Score
        composite_score = round(
            (w_price * price_score) +
            (w_delivery * delivery_score) +
            (w_quality * quality_score) +
            (w_compliance * compliance_score),
            2
        )

        # Warnings and flag evaluations
        warnings = list(audit["warnings"]) + list(audit["issues"])
        
        # Check what-if constraints
        is_disqualified = False
        if max_budget_limit is not None and landed_cost > max_budget_limit:
            warnings.append(f"Exceeds what-if budget filter (${landed_cost:,.2f} > ${max_budget_limit:,.2f})")
            is_disqualified = True
        if max_lead_time_days is not None and q["lead_time_days"] > max_lead_time_days:
            warnings.append(f"Exceeds what-if lead time filter ({q['lead_time_days']}d > {max_lead_time_days}d)")
            is_disqualified = True
        if min_warranty_months is not None and q["warranty_months"] < min_warranty_months:
            warnings.append(f"Fails what-if warranty filter ({q['warranty_months']}m < {min_warranty_months}m)")
            is_disqualified = True

        # Build structured 7 dimensions:
        delivery_dim = {
            "quoted_days": q["lead_time_days"],
            "variance_days": q["lead_time_days"] - rfq["deadline_days"],
            "sla_passed": q["lead_time_days"] <= rfq["deadline_days"],
            "on_time_rate": vendor.get("historical_on_time_rate", 95.0)
        }

        warranty_dim = {
            "quoted_months": q["warranty_months"],
            "required_months": rfq.get("min_warranty_months", 12),
            "deficit_months": max(0, rfq.get("min_warranty_months", 12) - q["warranty_months"]),
            "passed": q["warranty_months"] >= rfq.get("min_warranty_months", 12)
        }

        compliance_dim = {
            "passed": audit["passed"],
            "score": audit["score"],
            "iso_certs": vendor.get("iso_certs", []),
            "esg_score": vendor.get("esg_score", 70.0),
            "issues": audit["issues"],
            "warnings": audit["warnings"]
        }

        risk_dim = {
            "level": audit["risk_level"],
            "score": audit["risk_score"],
            "factors": warnings
        }

        evaluations.append({
            "vendor_id": vendor["id"],
            "vendor_name": vendor["name"],
            "vendor_code": vendor["code"],
            "quotation_id": q["id"],
            "quote_reference": q.get("quote_reference", ""),
            "landed_cost": landed_cost,
            "tco": tco,
            "tco_data": tco_data,
            "delivery": delivery_dim,
            "warranty": warranty_dim,
            "compliance": compliance_dim,
            "risk": risk_dim,
            "score": composite_score,
            "price_score": price_score,
            "delivery_score": delivery_score,
            "quality_score": quality_score,
            "compliance_score": compliance_score,
            "composite_score": composite_score,
            "compliance_passed": audit["passed"],
            "is_disqualified": is_disqualified,
            "flag_warnings": warnings,
            "evidence": audit["evidence"]
        })

    # Sort deterministically:
    # 1. Non-disqualified before disqualified
    # 2. Higher composite score
    # 3. Lower TCO (tie-break)
    # 4. Vendor ID (deterministic fallback)
    evaluations.sort(
        key=lambda x: (
            0 if not x["is_disqualified"] else 1,
            -x["composite_score"],
            x["tco"],
            x["vendor_id"]
        )
    )

    for idx, ev in enumerate(evaluations):
        ev["rank"] = idx + 1

    return evaluations
