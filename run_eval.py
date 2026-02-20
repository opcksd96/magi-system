import asyncio
from magi_core.eval.benchmarker import MardukBenchmarker
from magi_core.providers.ollama_provider import OllamaProvider
from rich.console import Console
from rich.table import Table

console = Console()


async def run_marduk_report():
    console.print("[bold red]INITIATING MARDUK REPORT GENERATION...[/bold red]")

    # Setup
    model = "lfm2.5-thinking:latest"
    provider = OllamaProvider(model=model)
    bench = MardukBenchmarker(
        dataset_path="data/golden_dataset.json", provider=provider
    )

    # Run
    metrics = await bench.run_benchmark()

    # Display Summary
    console.print("\n[bold green]--- MARDUK REPORT SUMMARY ---[/bold green]")
    console.print(f"Total Cases: {metrics['total_cases']}")
    console.print(f"Baseline Accuracy: {metrics['baseline_accuracy']}%")
    console.print(f"MAGI Accuracy: {metrics['magi_accuracy']}%")
    console.print(f"Average Consensus Confidence: {metrics['avg_confidence']}%")
    console.print(f"Final MAGI Score: [bold cyan]{metrics['magi_score']}[/bold cyan]")

    # Display Table
    table = Table(title="Detailed Results")
    table.add_column("ID", style="dim")
    table.add_column("Category")
    table.add_column("Baseline")
    table.add_column("MAGI")
    table.add_column("Expected", style="bold green")
    table.add_column("Confidence")

    for res in metrics["raw_results"]:
        table.add_row(
            res["id"],
            res["category"],
            res["baseline"],
            res["magi"],
            res["expected"],
            f"{res['magi_confidence']}%",
        )

    console.print(table)


if __name__ == "__main__":
    asyncio.run(run_marduk_report())
