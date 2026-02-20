import asyncio
import os
from magi_core.providers.ollama_provider import OllamaProvider
from magi_core.providers.heavy import HeavyProvider
from rich.console import Console

console = Console()


async def test_heavy_cycle():
    console.print("[bold cyan]INITIALIZING MAGI-HEAVY TEST...[/bold cyan]")

    # Using a fast local model for testing
    model = "lfm2.5-thinking:latest"
    base_provider = OllamaProvider(model=model)

    # In HeavyProvider, we can use the same provider for all roles,
    # or mix and match. For this test, we use the same one.
    heavy = HeavyProvider(
        advisor_providers=[base_provider, base_provider, base_provider],
        judge_provider=base_provider,
    )

    prompt = "Is it ethical to use AI to automate job interviews?"

    console.print(f"\n[bold yellow]TARGET PROMPT:[/bold yellow] {prompt}")
    console.print(
        "[italic]Commencing 3-phase debate cycle (Divergence -> Critique -> Convergence)...[/italic]\n"
    )

    try:
        response = await heavy.generate(prompt)

        console.print("[bold green]--- FINAL MAGI RULING ---[/bold green]")
        console.print(response.content)

        console.print("\n[bold blue]--- THINKING PROCESS (LOG) ---[/bold blue]")
        console.print(response.thinking_process)

    except Exception as e:
        console.print(f"[bold red]TEST FAILED:[/bold red] {str(e)}")


if __name__ == "__main__":
    asyncio.run(test_heavy_cycle())
