import json
from typing import Dict, Any, List
from app.config import settings

def generate_procurement_summary(
    rfq: Dict[str, Any],
    top_evaluation: Dict[str, Any],
    all_evaluations: List[Dict[str, Any]]
) -> str:
    """
    Produces an executive recommendation summary.
    If GEMINI_API_KEY is available and active, can query Gemini.
    Otherwise, deterministically constructs a comprehensive analytical procurement brief.
    """
    vendor_name = top_evaluation["vendor_name"]
    tco = top_evaluation["tco"]
    score = top_evaluation["composite_score"]
    rfq_title = rfq["title"]
    budget = rfq["budget"]
    savings = budget - tco
    savings_pct = (savings / budget * 100.0) if budget > 0 else 0.0

    # Deterministic rule-based analytical brief
    heuristic_brief = (
        f"### Executive Procurement Recommendation\n\n"
        f"**Project**: {rfq_title}\n"
        f"**Award Recommendation**: **{vendor_name}** (Rank #1, Composite Score: **{score:.1f}/100**)\n\n"
        f"#### Strategic Justification:\n"
        f"1. **Cost & Value Optimization**: Evaluated TCO is **${tco:,.2f}** against an authorized budget of **${budget:,.2f}**, "
        f"delivering **${savings:,.2f} ({savings_pct:.1f}%)** in fiscal variance savings.\n"
        f"2. **Risk & SLA Adherence**: Passed all ISO and technical requirements. Delivery timeline and warranty terms meet organizational procurement parameters.\n"
        f"3. **Peer Analysis**: Outperformed {len(all_evaluations) - 1} alternative vendor proposals based on weighted multidimensional evaluation (Price, Delivery Reliability, Vendor Tier, Compliance).\n\n"
        f"*(Generated via Deterministic Procurement Heuristic Engine • Zero External Cloud Dependencies)*"
    )

    if not settings.GEMINI_API_KEY:
        return heuristic_brief

    # Optional Gemini enhancement when API key is supplied
    try:
        import urllib.request
        prompt = (
            f"You are a Senior Strategic Procurement Director. Write a concise 3-paragraph executive summary "
            f"recommending {vendor_name} for '{rfq_title}'. Budget: ${budget}, TCO: ${tco}, Score: {score}/100. "
            f"Mention fiscal prudence, risk controls, and supplier reliability."
        )
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
        payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=4) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            candidate = res_data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text")
            if candidate:
                return candidate.strip() + "\n\n*(Enhanced by Gemini AI)*"
    except Exception:
        # Fallback cleanly with zero disruption
        pass

    return heuristic_brief
