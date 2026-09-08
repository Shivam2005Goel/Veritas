import re
from typing import List, Dict, Any, Optional
from models import Fact, Reconciliation

class QAEngine:
    """
    Fact-Grounded Q&A Engine.
    Synthesizes answers across the structured fact knowledge layer rather than
    raw unindexed chunks, providing verifiable citations and reconciliation awareness.
    """

    @classmethod
    def answer_query(cls, query: str, facts: List[Fact], reconciliations: List[Reconciliation]) -> Dict[str, Any]:
        q_lower = query.lower()

        # Score relevance of facts
        scored_facts = []
        for f in facts:
            score = 0
            if f.subject.lower() in q_lower:
                score += 3
            if f.predicate.lower().replace("_", " ") in q_lower or any(w in q_lower for w in f.predicate.split("_")):
                score += 2
            if f.fiscal_period and f.fiscal_period.lower() in q_lower:
                score += 3
            if f.unit and f.unit.lower() in q_lower:
                score += 1
            if any(term in q_lower for term in ["revenue", "turnover", "sales"]) and "revenue" in f.predicate:
                score += 3
            if any(term in q_lower for term in ["gdp", "growth"]) and "gdp" in f.predicate:
                score += 3
            if any(term in q_lower for term in ["inflation", "cpi"]) and "inflation" in f.predicate:
                score += 3
            if any(term in q_lower for term in ["pin", "reach", "network"]) and "pin" in f.predicate:
                score += 3

            if score > 0:
                scored_facts.append((score, f))

        scored_facts.sort(key=lambda x: x[0], reverse=True)
        top_facts = [f for _, f in scored_facts[:5]]

        if not top_facts:
            return {
                "query": query,
                "answer": "No directly verified facts found in the knowledge layer matching this inquiry.",
                "confidence": 0.0,
                "cited_facts": [],
                "reconciliations": []
            }

        # Find relevant cross-document reconciliations for cited facts
        fact_ids = set(f.id for f in top_facts)
        relevant_recs = [
            r for r in reconciliations
            if r.factA.id in fact_ids or r.factB.id in fact_ids
        ]

        # Synthesize answer
        primary_fact = top_facts[0]
        corrob = [r for r in relevant_recs if r.type == "corroboration"]
        reconciled = [r for r in relevant_recs if r.type == "reconciled"]
        contra = [r for r in relevant_recs if r.type == "contradiction"]

        summary_parts = []
        summary_parts.append(
            f"According to verified disclosures for {primary_fact.subject}, {primary_fact.predicate.replace('_', ' ')} is reported as {primary_fact.object} ({primary_fact.doc_id}, Page {primary_fact.page})."
        )

        if corrob:
            c = corrob[0]
            summary_parts.append(
                f" This figure is corroborated across multiple filings: '{c.factA.doc_id}' reports {c.factA.object} while '{c.factB.doc_id}' reports {c.factB.object}, matching once normalized to base currency units."
            )

        if reconciled:
            r = reconciled[0]
            summary_parts.append(
                f" Apparent discrepancies in other documents are reconciled by context ({r.axis_of_difference}): {r.reasoning}"
            )

        if contra:
            k = contra[0]
            summary_parts.append(
                f" Note: A genuine discrepancy exists with {k.factA.object} vs {k.factB.object} ({k.reasoning})."
            )

        answer_text = " ".join(summary_parts)

        return {
            "query": query,
            "answer": answer_text,
            "confidence": 0.95,
            "cited_facts": [
                {
                    "id": f.id,
                    "subject": f.subject,
                    "predicate": f.predicate,
                    "object": f.object,
                    "doc_id": f.doc_id,
                    "page": f.page,
                    "quote": f.quote,
                    "fiscal_period": f.fiscal_period,
                    "scope": f.scope,
                    "is_verified": f.is_verified
                } for f in top_facts
            ],
            "reconciliations": [
                {
                    "id": r.id,
                    "type": r.type,
                    "reasoning": r.reasoning,
                    "doc_a": r.factA.doc_id,
                    "doc_b": r.factB.doc_id
                } for r in relevant_recs[:3]
            ]
        }
