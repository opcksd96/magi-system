import json
from typing import List, Dict, Any
from magi_core.providers.base import ModelProvider
from magi_core.providers.heavy import HeavyProvider


class MardukBenchmarker:
    """
    Evaluation framework for the MAGI system.
    Compares MAGI consensus against single-model baselines.
    """

    def __init__(self, dataset_path: str, provider: ModelProvider):
        with open(dataset_path, "r", encoding="utf-8") as f:
            self.dataset = json.load(f)
        self.provider = provider
        # HeavyProvider for full debate
        self.magi = HeavyProvider(
            advisor_providers=[provider, provider, provider], judge_provider=provider
        )

    async def run_benchmark(self):
        results = []
        for item in self.dataset:
            print(f"Evaluating: {item['title']}...")

            # 1. Baseline (Single Model)
            baseline_resp = await self.provider.generate(item["prompt"])
            baseline_decision = self._extract_simple_decision(baseline_resp.content)

            # 2. MAGI Consensus
            magi_resp = await self.magi.generate(item["prompt"])
            # The HeavyProvider response content starts with "RULING: [DECISION]"
            magi_decision_str = (
                magi_resp.content.split("\n")[0].replace("RULING: ", "").strip()
            )

            results.append(
                {
                    "id": item["id"],
                    "category": item["category"],
                    "baseline": baseline_decision,
                    "magi": magi_decision_str,
                    "expected": item["expected_decision"],
                    "magi_confidence": (
                        magi_resp.raw_response["decision"].confidence_score
                        if "decision" in magi_resp.raw_response
                        else 0
                    ),
                }
            )

        return self._calculate_metrics(results)

    def _extract_simple_decision(self, content: str) -> str:
        content_upper = content.upper()
        # Look for the last occurrence of the keyword to get the final verdict
        verdicts = []
        if "APPROVE" in content_upper:
            verdicts.append(("APPROVE", content_upper.rfind("APPROVE")))
        if "DENY" in content_upper or "DENNY" in content_upper:
            verdicts.append(
                (
                    "DENY",
                    (
                        content_upper.rfind("DENY")
                        if "DENY" in content_upper
                        else content_upper.rfind("DENNY")
                    ),
                )
            )
        if "CONDITIONAL" in content_upper:
            verdicts.append(("CONDITIONAL", content_upper.rfind("CONDITIONAL")))

        if not verdicts:
            return "UNKNOWN"

        # Return the one that appears latest in the text (likely the final conclusion)
        return sorted(verdicts, key=lambda x: x[1])[-1][0]

    def _calculate_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        baseline_hits = sum(1 for r in results if r["baseline"] == r["expected"])
        magi_hits = sum(1 for r in results if r["magi"] == r["expected"])

        return {
            "total_cases": len(results),
            "baseline_accuracy": (baseline_hits / len(results)) * 100,
            "magi_accuracy": (magi_hits / len(results)) * 100,
            "magi_score": (magi_hits - baseline_hits) * 10,  # Weighted improvement
            "avg_confidence": sum(r["magi_confidence"] for r in results) / len(results),
            "raw_results": results,
        }
