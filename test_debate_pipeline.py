import asyncio
from typing import Optional
from magi_core.providers.base import ModelProvider, MagiResponse
from magi_core.providers.heavy import HeavyProvider
from magi_core.utils.logger import SessionLogger


# Mock Provider
class MockProvider(ModelProvider):
    def __init__(self, name, role):
        super().__init__()
        self.name = name
        self.role = role
        self.call_count = 0

    async def generate_raw(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> MagiResponse:
        self.call_count += 1
        content = f"[{self.name}] Response {self.call_count} for role {self.role}. Analysis of: {prompt[:20]}..."
        if "Supreme Judge" in prompt:
            content = """DECISION: APPROVE
CONFIDENCE: 85
RULING: MOCK RULING APPROVED
REASONING: The debate was conclusive.
SUMMARY: The advisors debated well. MELCHIOR analyzed logic, BALTHASAR ethics, and CASPER pragmatics.
            """
        return MagiResponse(
            content=content, model_name="mock-model", provider_name=self.name
        )

    async def health_check(self) -> bool:
        return True


async def test_pipeline():
    print("--- STARTING PIPELINE TEST ---")

    # Setup mocks
    mel = MockProvider("MELCHIOR-1", "scientist")
    bal = MockProvider("BALTHASAR-2", "mother")
    cas = MockProvider("CASPER-3", "woman")

    logger = SessionLogger()

    # Initialize HeavyProvider
    heavy = HeavyProvider(
        advisor_providers=[mel, bal, cas],
        judge_provider=mel,  # Melchior doubles as judge
        logger=logger,
    )

    # Run generation
    print("Running generate...")
    response = await heavy.generate("Should we launch EVA Unit-01?")

    # verification
    print("\n--- RESULTS ---")
    print(f"Total Execution Time: {response.execution_time:.2f}s")
    print(f"Ruling: {response.content}")

    raw = response.raw_response
    history = raw.get("debate_history", [])
    print(f"\nDebate Rounds: {len(history)}")
    for h in history:
        print(
            f"Round {h['round']}: Mel={len(h['mel'])} chars, Bal={len(h['bal'])} chars, Cas={len(h['cas'])} chars"
        )

    phases = raw.get("phases", [])
    print(f"\nPhases: {phases}")

    if len(history) > 0 and "SUMMARY:" in response.content:
        print("\n✅ TEST PASSED: Debate history present and Summary generated.")
    else:
        print("\n❌ TEST FAILED: Missing history or summary.")


if __name__ == "__main__":
    asyncio.run(test_pipeline())
