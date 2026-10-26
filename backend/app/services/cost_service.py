from typing import Dict, Any

def compute_tco(
    base_quote_amount: float,
    shipping_fee: float,
    tax_amount: float,
    quote_lead_time: int,
    rfq_deadline: int,
    quote_warranty_months: int,
    rfq_min_warranty: int,
    hidden_fee: float = 0.0
) -> Dict[str, Any]:
    """
    Computes deterministic Landed Cost and Total Cost of Ownership (TCO).
    No random numbers, strictly reproducible arithmetic.
    
    Landed Cost = Base Items + Shipping + Tax - Volume Discount + Hidden/Unbundled Surcharges
    TCO = Landed Cost + SLA Delivery Delay Risk Buffer + Warranty Deficit Buffer
    """
    base = round(float(base_quote_amount), 2)
    shipping = round(float(shipping_fee), 2)
    tax = round(float(tax_amount), 2)
    hidden = round(float(hidden_fee), 2)
    
    # Volume discount rule: 2.5% discount if base >= $100,000, 1.5% if >= $50,000
    if base >= 100000.0:
        volume_discount = round(base * 0.025, 2)
    elif base >= 50000.0:
        volume_discount = round(base * 0.015, 2)
    else:
        volume_discount = 0.0

    # Net Landed Cost (physical procurement expenditure including all shipping and hidden fees)
    landed_cost = round(base + shipping + tax - volume_discount + hidden, 2)

    # Risk-adjusted lead time delay buffer ($200 per day past target deadline)
    delay_days = max(0, quote_lead_time - rfq_deadline)
    lead_time_risk_cost = round(delay_days * 200.0, 2)

    # Warranty deficit risk cost ($250 per missing month of warranty coverage)
    warranty_deficit_months = max(0, rfq_min_warranty - quote_warranty_months)
    warranty_risk_cost = round(warranty_deficit_months * 250.0, 2)

    total_risk_cost = round(lead_time_risk_cost + warranty_risk_cost, 2)

    # Total Cost of Ownership
    total_tco = round(landed_cost + total_risk_cost, 2)

    return {
        "base_amount": base,
        "shipping_fee": shipping,
        "tax_amount": tax,
        "hidden_fee": hidden,
        "volume_discount": volume_discount,
        "net_direct_cost": landed_cost,  # Kept for backward compatibility
        "landed_cost": landed_cost,
        "delay_days": delay_days,
        "lead_time_risk_cost": lead_time_risk_cost,
        "warranty_deficit_months": warranty_deficit_months,
        "warranty_risk_cost": warranty_risk_cost,
        "total_risk_cost": total_risk_cost,
        "total_tco": total_tco
    }
