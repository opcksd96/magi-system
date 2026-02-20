import typer
import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.layout import Layout


from magi_core.providers.openai import OpenAIProvider
from magi_core.providers.ollama_provider import OllamaProvider
from magi_core.logic.casper import CasperEngine
from magi_core.prompts import MAGI_SYSTEM_PROMPTS

app = typer.Typer()
console = Console()


async def run_magi(prompt: str, model: str, local: bool):
    """
    Async function to run the MAGI cycle.
    """
    # 1. Initialize Providers
    # For now, we use the same model for all 3 Magi for the API version,
    # or different local models if specified.
    # In a full deployment, we'd mix and match (e.g. GPT-4o for Casper, Claude for Melchior).

    if local:
        if model == "gpt-4o":
            model = "lfm2.5-thinking:latest"  # Default to user's available model
        provider = OllamaProvider(model=model)
        judge = OllamaProvider(model=model)  # Local Judge
    else:
        provider = OpenAIProvider(model=model)
        judge = OpenAIProvider(model=model)

    engine = CasperEngine(judge_provider=judge)

    # 1.5 Health Check
    with console.status(
        "[bold orange1]PERFORMING HEALTH CHECK...[/bold orange1]", spinner="dots"
    ):
        if not await provider.health_check():
            console.print(
                f"[bold red]SYSTEM ERROR:[/bold red] Could not connect to provider for model {model}."
            )
            if local:
                console.print("Please ensure Ollama is running (try `ollama serve`).")
            else:
                console.print("Please ensure your API key is set correctly.")
            return

    console.print(f"[bold green]MAGI SYSTEM ACTIVATED[/bold green] (Model: {model})")
    console.print(f"Target: [bold cyan]{prompt}[/bold cyan]\n")

    # 2. Parallel Execution (The Debate)
    with console.status(
        "[bold orange1]PROCESSING...[/bold orange1]", spinner="aesthetic"
    ):
        try:
            # We run 3 requests in parallel
            tasks = [
                provider.generate(prompt, MAGI_SYSTEM_PROMPTS["MELCHIOR"]),
                provider.generate(prompt, MAGI_SYSTEM_PROMPTS["BALTHASAR"]),
                provider.generate(prompt, MAGI_SYSTEM_PROMPTS["CASPER"]),
            ]

            melchior, balthasar, casper = await asyncio.gather(*tasks)

        except Exception as e:  # noqa: BLE001 # pylint: disable=broad-exception-caught
            console.print(f"[bold red]SYSTEM ERROR:[/bold red] {e}")
            return

    # 3. Display Individual Thoughts
    layout = Layout()
    layout.split_row(
        Layout(Panel(melchior.content, title="MELCHIOR-1", border_style="cyan")),
        Layout(Panel(balthasar.content, title="BALTHASAR-2", border_style="magenta")),
        Layout(Panel(casper.content, title="CASPER-3", border_style="yellow")),
    )
    console.print(layout)
    console.print("\n")

    # 4. The Judgment (Casper Logic)
    with console.status("[bold red]JUDGING...[/bold red]", spinner="aesthetic"):
        decision = await engine.deliberate(melchior, balthasar, casper)

    # 5. Final Display
    color = "green" if decision.decision == "APPROVE" else "red"
    if decision.decision == "CONDITIONAL":
        color = "yellow"

    final_panel = Panel(
        f"""
[bold size=20]{decision.decision}[/bold size]
Confidence: {decision.confidence_score}%

[bold]RULING:[/bold] {decision.main_ruling}

[bold]REASONING:[/bold]
{decision.reasoning}

[bold]APPENDICES:[/bold]
"""
        + "\n".join([f"- {a}" for a in decision.appendices]),
        title="MAGI SYSTEM DECISION",
        border_style=color,
        subtitle="CASPER CONSENSUS AGENT",
    )
    console.print(final_panel)


@app.command()
def ask(
    prompt: str,
    model: str = typer.Option("gpt-4o", help="Model to use (e.g. gpt-4o, llama3)"),
    local: bool = typer.Option(
        False, "--local", help="Use local Ollama instead of OpenAI"
    ),
):
    """
    Ask the MAGI System a question.
    """
    asyncio.run(run_magi(prompt, model, local))


if __name__ == "__main__":
    app()
