from typing import List, Dict, Any

def audit_compliance(
    vendor: Dict[str, Any],
    quotation: Dict[str, Any],
    rfq: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Deterministic compliance and risk audit.
    Evaluates:
      1. ISO Certifications (Mandatory vs Held)
      2. ESG Score vs Minimum Baseline
      3. Warranty Term vs RFQ Specification
      4. Lead Time SLA vs Mandatory Deadline
      5. Commercial Payment Terms
    Returns:
      passed: bool
      score: float (0.0 to 100.0)
      risk_level: "LOW" | "MEDIUM" | "HIGH"
      risk_score: float (0.0 to 100.0)
      issues: List[str]
      warnings: List[str]
      evidence: List[str]
    """
    issues: List[str] = []
    warnings: List[str] = []
    evidence: List[str] = []
    score: float = 100.0
    risk_score: float = 5.0  # Base operational risk

    # 1. ISO Certifications Check
    required_iso = rfq.get("required_iso_certs", [])
    vendor_iso = vendor.get("iso_certs", [])
    for cert in required_iso:
        if cert in vendor_iso:
            evidence.append(f"Verified compliance: Vendor holds mandatory {cert} certification")
        else:
            issue_msg = f"Missing mandatory certification: {cert}"
            issues.append(issue_msg)
            evidence.append(f"Non-compliance finding: {issue_msg}")
            score -= 20.0
            risk_score += 25.0

    # 2. ESG Score Check
    min_esg = float(rfq.get("min_esg_score", 60.0))
    vendor_esg = float(vendor.get("esg_score", 0.0))
    if vendor_esg >= min_esg:
        evidence.append(f"ESG audit passed: Score {vendor_esg:.1f} meets requirement (min {min_esg:.1f})")
    else:
        issue_msg = f"Vendor ESG score {vendor_esg:.1f} is below mandatory threshold {min_esg:.1f}"
        issues.append(issue_msg)
        evidence.append(f"Risk finding: {issue_msg}")
        score -= 25.0
        risk_score += 20.0

    # 3. Warranty Requirements
    rfq_warranty = int(rfq.get("min_warranty_months", 12))
    quote_warranty = int(quotation.get("warranty_months", 0))
    if quote_warranty >= rfq_warranty:
        evidence.append(f"Warranty terms: {quote_warranty} months exceeds minimum requirement of {rfq_warranty} months")
    else:
        diff_w = rfq_warranty - quote_warranty
        issue_msg = f"Quoted warranty {quote_warranty} months falls short of requirement ({rfq_warranty} months by {diff_w}mo)"
        issues.append(issue_msg)
        evidence.append(f"Warranty deficit: {issue_msg}")
        score -= 15.0
        risk_score += 15.0

    # 4. Lead Time / Deadline Check
    rfq_deadline = int(rfq.get("deadline_days", 30))
    quote_lead_time = int(quotation.get("lead_time_days", 0))
    if quote_lead_time <= rfq_deadline:
        evidence.append(f"SLA Delivery: {quote_lead_time} days meets {rfq_deadline}-day requirement ({rfq_deadline - quote_lead_time}d buffer)")
    else:
        diff_lt = quote_lead_time - rfq_deadline
        issue_msg = f"Quoted delivery of {quote_lead_time} days exceeds {rfq_deadline}-day SLA by {diff_lt} days"
        issues.append(issue_msg)
        evidence.append(f"SLA breach: {issue_msg}")
        score -= min(30.0, 5.0 * diff_lt)
        risk_score += min(35.0, 6.0 * diff_lt)

    # 5. Hidden Surcharges / Fine Print Check (if present in quotation)
    hidden_fee = float(quotation.get("hidden_fee", 0.0))
    if hidden_fee > 0:
        warning_msg = f"Unbundled fine-print surcharge detected: ${hidden_fee:,.2f} added to landed cost"
        warnings.append(warning_msg)
        evidence.append(f"Quotation Conflict: {warning_msg}")
        score -= 15.0
        risk_score += 20.0

    # 6. Payment Terms Check
    payment_terms = str(quotation.get("payment_terms", "Net 30")).lower()
    allowed_terms = ["net 30", "net 45", "net 60", "net 90"]
    if payment_terms in allowed_terms:
        evidence.append(f"Commercial terms: {quotation.get('payment_terms')} conforms to standard corporate accounting")
    else:
        warning_msg = f"Non-standard payment terms '{quotation.get('payment_terms')}', requires treasury pre-approval"
        warnings.append(warning_msg)
        evidence.append(warning_msg)
        score -= 5.0
        risk_score += 10.0

    # Historical on-time track record evidence
    on_time = float(vendor.get("historical_on_time_rate", 90.0))
    evidence.append(f"Historical Supplier Reliability: {on_time:.1f}% on-time fulfillment record")
    if on_time < 90.0:
        risk_score += (90.0 - on_time) * 1.5

    score = max(0.0, min(100.0, round(score, 1)))
    risk_score = max(0.0, min(100.0, round(risk_score, 1)))
    
    if risk_score <= 25.0:
        risk_level = "LOW"
    elif risk_score <= 55.0:
        risk_level = "MEDIUM"
    else:
        risk_level = "HIGH"

    passed = len(issues) == 0

    return {
        "passed": passed,
        "score": score,
        "risk_level": risk_level,
        "risk_score": risk_score,
        "issues": issues,
        "warnings": warnings,
        "evidence": evidence
    }
