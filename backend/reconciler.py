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
    def are_predicates_compatible(cls, p1: str, p2: str) -> bool:
        """Determines if two predicates refer to the same financial/operational dimension."""
        if p1 == p2:
            return True
        revenue_group = {"revenue_from_operations", "revenue_from_operations_consolidated", "revenue_from_operations_standalone", "total_income"}
        if p1 in revenue_group and p2 in revenue_group:
            return True
        gdp_group = {"real_gdp_growth", "real_gdp_growth_estimate", "gdp_growth_rate"}
        if p1 in gdp_group and p2 in gdp_group:
            return True
        inflation_group = {"cpi_headline_inflation", "headline_inflation", "cpi_inflation"}
        if p1 in inflation_group and p2 in inflation_group:
            return True
        return False

    @classmethod
    def reconcile_pair(cls, f1: Fact, f2: Fact) -> Optional[Reconciliation]:
        """Compares two facts and returns a classified Reconciliation verdict if applicable."""
        # Must be different documents
        if f1.doc_id == f2.doc_id:
            return None

        # Must be about the same resolved entity
        if f1.subject.lower() != f2.subject.lower():
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
            formatted_val = f"{v1:.2f}%" if f1.unit == "percent" else f"~₹{v1/1e7:,.2f} Cr"
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
