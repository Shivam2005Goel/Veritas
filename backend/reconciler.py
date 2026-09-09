import uuid
from typing import List, Tuple, Optional
from models import Fact, Reconciliation

class Reconciler:
    """
    Two-stage Cross-Document Reconciliation Engine.
    Stage 1: Candidate Generation via Entity & Predicate Compatibility.
    Stage 2: Verdict Classification into:
             - Corroboration
             - Contradiction
             - Reconciled by Context (Temporal, Unit, Scope)
             - Failure / Ambiguity Analysis (Case 4)
    """

    @classmethod
    def are_entities_compatible(cls, f1: Fact, f2: Fact) -> bool:
        """Determines if two facts refer to the same or compatible entity domain."""
        s1 = f1.subject.lower().strip()
        s2 = f2.subject.lower().strip()
        if s1 == s2:
            return True

        # Fuzzy word containment (e.g. "Tesla" in "Tesla, Inc.", "ZEPHYR" in "ZEPHYR (Research System)")
        import re
        w1 = set(re.findall(r"\w+", s1))
        w2 = set(re.findall(r"\w+", s2))
        # Filter out common corporate/system words
        stop = {"inc", "ltd", "limited", "corp", "corporation", "system", "model", "paper", "research", "the", "of", "and"}
        sig1 = w1 - stop
        sig2 = w2 - stop
        if sig1 and sig2 and (sig1.issubset(sig2) or sig2.issubset(sig1)):
            return True

        # Macro / Public Finance sovereign entities reporting on India
        sovereign_entities = {
            "government of india", "government of india - union budget", "ministry of finance",
            "reserve bank of india", "ministry of statistics and programme implementation",
            "mospi", "rbi", "central statistics office", "niti aayog", "india"
        }
        if s1 in sovereign_entities and s2 in sovereign_entities:
            return True

        return False

    @classmethod
    def are_predicates_compatible(cls, p1: str, p2: str) -> bool:
        """Determines if two predicates refer to the same financial, operational, or macro dimension."""
        if p1 == p2:
            return True
            
        synonym_groups = [
            # Revenues
            {"revenue_from_operations", "revenue_from_operations_consolidated", "revenue_from_operations_standalone", "total_income", "total_revenue", "net_revenue", "turnover", "net_sales"},
            # Net Profits
            {"net_profit", "profit_after_tax", "pat", "profit_for_the_year", "net_income"},
            # Operating Profits / EBITDA
            {"operating_profit_ebitda", "ebitda", "operating_profit", "adjusted_ebitda", "profit_before_tax", "pbt"},
            # Expenses
            {"total_expenses", "total_expenditure", "operating_expenses"},
            # Assets / Cash
            {"cash_and_cash_equivalents", "cash_reserves", "bank_balances"},
            # GDP
            {"real_gdp_growth", "real_gdp_growth_estimate", "gdp_growth_rate", "gdp_growth"},
            # Inflation
            {"cpi_headline_inflation", "headline_inflation", "cpi_inflation", "retail_inflation"},
            # Public Finance / Budget
            {"gross_tax_revenue", "total_revenue_receipts", "centre_net_tax_revenue", "total_receipts", "customs", "corporation_tax", "taxes_on_income"},
            # Scientific / AI Benchmarks
            {"true_positive_rate", "detection_accuracy", "area_under_curve_auc", "temporal_spectral_slope"},
            # Volume & Operational
            {"total_volume", "freight_tonnage", "shipments", "express_parcels"},
            {"total_employees", "employee_count", "headcount", "workforce"}
        ]
        
        for group in synonym_groups:
            if p1 in group and p2 in group:
                return True
                
        return False

    @classmethod
    def reconcile_pair(cls, f1: Fact, f2: Fact) -> Optional[Reconciliation]:
        """Compares two facts and returns a classified Reconciliation verdict if applicable."""
        # Must be different documents
        if f1.doc_id == f2.doc_id:
            return None

        # Must be about the same or compatible resolved entity
        if not cls.are_entities_compatible(f1, f2):
            return None

        # Must be semantically compatible predicates
        if not cls.are_predicates_compatible(f1.predicate, f2.predicate):
            return None

        v1 = f1.normalized_value
        v2 = f2.normalized_value
        if v1 is None or v2 is None:
            return None

        rec_id = f"rec_{uuid.uuid4().hex[:8]}"

        # --- Case 4: Extraction / Verification Failure Check ---
        if not f1.is_verified or not f2.is_verified:
            return Reconciliation(
                id=rec_id,
                type="failure",
                factA=f1,
                factB=f2,
                reasoning="Reasoning failure / Low confidence: Grounding verification failed to locate the exact quote on the cited page. Flagged for review to prevent hallucinated reconciliation.",
                axis_of_difference="verification_mismatch",
                confidence=0.45
            )

        # Check differences across dimensions
        period_diff = (f1.fiscal_period != f2.fiscal_period) or (f1.period_end != f2.period_end)
        scope_diff = (f1.scope != f2.scope) and (f1.scope and f2.scope)
        
        # Relative numeric difference
        base_val = max(abs(v1), abs(v2), 1.0)
        rel_diff = abs(v1 - v2) / base_val

        # --- Case 3: Apparent Contradiction Reconciled by Context ---
        if period_diff:
            return Reconciliation(
                id=rec_id,
                type="reconciled",
                factA=f1,
                factB=f2,
                reasoning=f"Apparent contradiction reconciled by TEMPORAL CONTEXT: '{f1.doc_id}' reports for {f1.fiscal_period or 'period A'} ({f1.object}), whereas '{f2.doc_id}' reports for {f2.fiscal_period or 'period B'} ({f2.object}). The difference of {rel_diff*100:.1f}% represents historical business growth across periods, not an error.",
                axis_of_difference="temporal_period",
                confidence=0.96
            )

        if scope_diff:
            scope_explanation = f"One document reports on a {f1.scope.upper()} basis ({f1.object}), while the second document reports on a {f2.scope.upper()} basis ({f2.object}). Consolidated figures include subsidiary revenues."
            if "macroeconomic" in (f1.scope or "").lower() or "macroeconomic" in (f2.scope or "").lower():
                scope_explanation = f"Methodological difference reconciled: '{f1.doc_id}' provides a {f1.scope.replace('_', ' ')} ({f1.object}), while '{f2.doc_id}' provides a {f2.scope.replace('_', ' ')} ({f2.object}). Projections capture range estimates while point estimates reflect final observed accounts."
            
            return Reconciliation(
                id=rec_id,
                type="reconciled",
                factA=f1,
                factB=f2,
                reasoning=f"Apparent contradiction reconciled by REPORTING SCOPE & METHODOLOGY: {scope_explanation}",
                axis_of_difference="reporting_scope",
                confidence=0.94
            )

        # Same period and same scope: Compare values
        if rel_diff <= 0.02: # Within 2% (rounding differences between crore and million units)
            if f1.unit == "percent":
                formatted_val = f"{v1:.2f}%"
            elif f1.currency == "USD":
                formatted_val = f"${v1/1e9:.2f}B" if v1 >= 1e9 else f"${v1/1e6:.2f}M"
            elif f1.currency == "EUR":
                formatted_val = f"€{v1/1e9:.2f}B" if v1 >= 1e9 else f"€{v1/1e6:.2f}M"
            elif f1.currency == "INR":
                formatted_val = f"~₹{v1/1e7:,.2f} Cr"
            else:
                formatted_val = f"{v1:,.2f} {f1.unit or ''}".strip()

            return Reconciliation(
                id=rec_id,
                type="corroboration",
                factA=f1,
                factB=f2,
                reasoning=f"Corroboration confirmed: Both documents report consistent normalized figures ({formatted_val}) for {f1.fiscal_period or 'the fiscal period'} ({f1.scope}), despite differing document formatting ('{f1.object}' vs '{f2.object}').",
                axis_of_difference="none",
                confidence=0.98
            )
        else:
            return Reconciliation(
                id=rec_id,
                type="contradiction",
                factA=f1,
                factB=f2,
                reasoning=f"Material contradiction detected: Both documents refer to {f1.subject} for the same period ({f1.fiscal_period}) and scope ({f1.scope}), but report substantially conflicting figures ({f1.object} vs {f2.object}, a {rel_diff*100:.1f}% discrepancy).",
                axis_of_difference="unresolved_numerical_conflict",
                confidence=0.92
            )

    @classmethod
    def reconcile_all(cls, facts: List[Fact]) -> List[Reconciliation]:
        """Evaluates candidate fact pairs across different documents."""
        reconciliations: List[Reconciliation] = []
        seen_pairs = set()

        for i in range(len(facts)):
            for j in range(i + 1, len(facts)):
                f1 = facts[i]
                f2 = facts[j]
                
                # Deduplicate comparisons
                pair_key = tuple(sorted([f1.id, f2.id]))
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)

                rec = cls.reconcile_pair(f1, f2)
                if rec:
                    reconciliations.append(rec)

        return reconciliations
