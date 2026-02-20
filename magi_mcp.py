import asyncio
import os
from mcp.server.fastmcp import FastMCP
from magi_core.providers.openai import OpenAIProvider
from magi_core.providers.ollama import OllamaProvider
from magi_core.logic.casper import CasperEngine
from magi_core.prompts import MAGI_SYSTEM_PROMPTS


# Initialize FastMCP Server
mcp = FastMCP("MAGI System")


async def _get_provider(model: str = "gpt-4o", local: bool = False):
    if local:
        return OllamaProvider(model=model)
    return OpenAIProvider(model=model, api_key=os.getenv("OPENAI_API_KEY"))


@mcp.tool()
async def consult_magi(prompt: str, model: str = "gpt-4o", local: bool = False) -> str:
    """
    Consult the MAGI System for a consensus decision on a complex matter.

    Args:
        prompt: The question or scenario to analyze.
        model: The model to use (default: gpt-4o).
        local: Whether to use local Ollama (default: False).
    """
    provider = await _get_provider(model, local)
    # Judge uses the same provider for now
    judge = provider

    engine = CasperEngine(judge_provider=judge)

    # Parallel Execution
    tasks = [
        provider.generate(prompt, MAGI_SYSTEM_PROMPTS["MELCHIOR"]),
        provider.generate(prompt, MAGI_SYSTEM_PROMPTS["BALTHASAR"]),
        provider.generate(prompt, MAGI_SYSTEM_PROMPTS["CASPER"]),
    ]

    melchior, balthasar, casper = await asyncio.gather(*tasks)

    decision = await engine.deliberate(melchior, balthasar, casper)

    return f"""
# MAGI SYSTEM DECISION
**Decision**: {decision.decision}
**Confidence**: {decision.confidence_score}%
**Main Ruling**: {decision.main_ruling}

## Reasoning
{decision.reasoning}

## Individual Opinions
- **MELCHIOR (Science)**: {melchior.content[:200]}...
- **BALTHASAR (Mother)**: {balthasar.content[:200]}...
- **CASPER (Woman)**: {casper.content[:200]}...

## Appendices
""" + "\n".join(
        [f"- {a}" for a in decision.appendices]
    )


if __name__ == "__main__":
    mcp.run()
