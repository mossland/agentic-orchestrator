"""
CLI entry point for the Agentic Orchestrator.

Provides commands for both legacy pipeline and new backlog-based workflow.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from . import __version__
from .utils.logging import setup_logging
from .orchestrator import Orchestrator
from .backlog import BacklogOrchestrator
from .utils.config import (
    get_env_bool,
    get_env_int,
    validate_backlog_environment,
    EnvironmentValidationError,
)

console = Console()


def validate_backlog_env_or_exit() -> None:
    """Validate backlog environment and exit with helpful message if invalid."""
    try:
        validate_backlog_environment()
    except EnvironmentValidationError as e:
        console.print(Panel(
            f"[bold red]Environment Configuration Error[/bold red]\n\n"
            f"{e.message}\n\n"
            f"[dim]Tip: Copy .env.example to .env and configure your API keys.[/dim]",
            title="Configuration Required",
            border_style="red",
        ))
        sys.exit(1)


def create_orchestrator(dry_run: bool = False) -> Orchestrator:
    """Create an orchestrator instance."""
    return Orchestrator(
        base_path=Path.cwd(),
        dry_run=dry_run or get_env_bool("DRY_RUN"),
    )


@click.group()
@click.version_option(version=__version__, prog_name="Agentic Orchestrator")
def main():
    """
    Mossland Agentic Orchestrator

    An autonomous system for discovering, planning, implementing,
    and validating micro Web3 services for the Mossland ecosystem.
    """
    pass


@main.command()
@click.option("--project-id", "-p", help="Custom project ID")
@click.option("--dry-run", is_flag=True, help="Run without making changes")
def init(project_id: Optional[str], dry_run: bool):
    """Initialize a new project."""
    console.print("[bold blue]Initializing new project...[/bold blue]")

    orchestrator = create_orchestrator(dry_run)

    try:
        pid = orchestrator.init_project(project_id)
        console.print(f"[bold green]Project initialized: {pid}[/bold green]")
        console.print(f"\nNext step: Run [bold]ao step[/bold] to start ideation")
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        sys.exit(1)


@main.command()
@click.option("--dry-run", is_flag=True, help="Run without making changes")
def step(dry_run: bool):
    """Execute a single pipeline step."""
    orchestrator = create_orchestrator(dry_run)

    # Check if we have a project
    if not orchestrator.state.project_id:
        console.print("[yellow]No active project. Initializing new project...[/yellow]")
        pid = orchestrator.init_project()
        console.print(f"[green]Created project: {pid}[/green]\n")

    current_stage = orchestrator.state.stage.value
    console.print(f"[blue]Current stage: {current_stage}[/blue]")

    if dry_run:
        console.print("[yellow](Dry run mode - no actual changes)[/yellow]")

    try:
        with console.status(f"[bold green]Executing {current_stage}...[/bold green]"):
            result = orchestrator.step()

        if result.success:
            console.print(f"[bold green]Stage completed successfully[/bold green]")
            console.print(f"  Message: {result.message}")

            if result.next_stage:
                console.print(f"  Next stage: {result.next_stage.value}")

            if result.artifacts:
                console.print(f"  Artifacts created: {len(result.artifacts)}")
                for artifact in result.artifacts[:5]:  # Show first 5
                    console.print(f"    - {artifact}")
        else:
            console.print(f"[bold red]Stage failed[/bold red]")
            console.print(f"  Error: {result.error}")
            console.print(f"  Message: {result.message}")
            sys.exit(1)

    except Exception as e:
        console.print(f"[bold red]Unexpected error: {e}[/bold red]")
        sys.exit(1)


@main.command()
@click.option("--max-steps", "-m", type=int, help="Maximum steps to execute")
@click.option("--delay", "-d", type=int, help="Delay between steps (seconds)")
@click.option("--dry-run", is_flag=True, help="Run without making changes")
def loop(max_steps: Optional[int], delay: Optional[int], dry_run: bool):
    """Run in continuous loop mode."""
    orchestrator = create_orchestrator(dry_run)

    # Check if we have a project
    if not orchestrator.state.project_id:
        console.print("[yellow]No active project. Initializing...[/yellow]")
        pid = orchestrator.init_project()
        console.print(f"[green]Created project: {pid}[/green]\n")

    console.print("[bold blue]Starting loop mode[/bold blue]")
    console.print(f"  Max steps: {max_steps or orchestrator.config.loop_max_steps}")
    console.print(f"  Delay: {delay or orchestrator.config.loop_delay}s")

    if dry_run:
        console.print("[yellow](Dry run mode)[/yellow]")

    console.print()

    try:
        results = orchestrator.loop(max_steps=max_steps, delay_seconds=delay)

        # Summary
        console.print("\n[bold blue]Loop Summary[/bold blue]")
        console.print(f"  Total steps: {len(results)}")
        console.print(f"  Successful: {sum(1 for r in results if r.success)}")
        console.print(f"  Failed: {sum(1 for r in results if not r.success)}")
        console.print(f"  Final stage: {orchestrator.state.stage.value}")

        if orchestrator.state.is_complete():
            console.print("\n[bold green]Project completed successfully![/bold green]")
        elif orchestrator.state.is_paused():
            console.print(f"\n[bold yellow]Paused: {orchestrator.state.errors.paused_reason}[/bold yellow]")

    except KeyboardInterrupt:
        console.print("\n[yellow]Loop interrupted by user[/yellow]")
        orchestrator.save_state()
    except Exception as e:
        console.print(f"[bold red]Loop error: {e}[/bold red]")
        sys.exit(1)


@main.command()
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def status(as_json: bool):
    """Show current orchestrator status."""
    orchestrator = create_orchestrator()
    status_data = orchestrator.status()

    if as_json:
        import json
        click.echo(json.dumps(status_data, indent=2, default=str))
        return

    # Rich output
    console.print()

    # Header
    project_id = status_data["project_id"] or "(none)"
    stage = status_data["stage"]

    console.print(Panel(
        f"[bold]Project:[/bold] {project_id}\n"
        f"[bold]Stage:[/bold] {stage}",
        title="Orchestrator Status",
        border_style="blue",
    ))

    # Flags
    flags = status_data["flags"]
    flag_str = []
    if flags["is_complete"]:
        flag_str.append("[green]COMPLETE[/green]")
    if flags["is_paused"]:
        flag_str.append("[yellow]PAUSED[/yellow]")
    if flags["can_continue"]:
        flag_str.append("[blue]READY[/blue]")

    if flag_str:
        console.print(f"Status: {' | '.join(flag_str)}")

    # Iterations
    table = Table(title="Iterations")
    table.add_column("Type", style="cyan")
    table.add_column("Current", style="magenta")
    table.add_column("Max", style="green")

    iter_data = status_data["iteration"]
    limits = status_data["limits"]

    table.add_row("Planning", str(iter_data["planning"]), str(limits["planning_max"]))
    table.add_row("Development", str(iter_data["dev"]), str(limits["dev_max"]))

    console.print(table)

    # Quality
    quality = status_data["quality"]
    if quality["review_score"] is not None or quality["tests_passed"] is not None:
        console.print("\n[bold]Quality Metrics:[/bold]")
        if quality["review_score"] is not None:
            score_color = "green" if quality["review_score"] >= quality["required_score"] else "yellow"
            console.print(f"  Review Score: [{score_color}]{quality['review_score']}/{quality['required_score']}[/{score_color}]")
        if quality["tests_passed"] is not None:
            test_color = "green" if quality["tests_passed"] else "red"
            test_str = "PASSED" if quality["tests_passed"] else "FAILED"
            console.print(f"  Tests: [{test_color}]{test_str}[/{test_color}]")

    # Errors
    errors = status_data["errors"]
    if errors["last_error"] or errors["paused_reason"]:
        console.print("\n[bold red]Errors:[/bold red]")
        if errors["paused_reason"]:
            console.print(f"  Paused: {errors['paused_reason']}")
        if errors["last_error"]:
            console.print(f"  Last Error: {errors['last_error']}")
        console.print(f"  Error Count: {errors['error_count']}")

    # Timestamps
    ts = status_data["timestamps"]
    if ts["created"]:
        console.print(f"\n[dim]Created: {ts['created']}[/dim]")
    if ts["last_updated"]:
        console.print(f"[dim]Updated: {ts['last_updated']}[/dim]")

    # Next step hint
    console.print()
    if flags["is_complete"]:
        console.print("[dim]Run 'ao init' to start a new project[/dim]")
    elif flags["is_paused"]:
        console.print("[dim]Resolve the issue and run 'ao resume' to continue[/dim]")
    elif flags["can_continue"]:
        console.print("[dim]Run 'ao step' to continue[/dim]")


@main.command()
@click.option("--dry-run", is_flag=True, help="Run without making changes")
def resume(dry_run: bool):
    """Resume from a paused state."""
    orchestrator = create_orchestrator(dry_run)

    if not orchestrator.state.is_paused():
        console.print("[yellow]Orchestrator is not paused. Use 'ao step' to continue.[/yellow]")
        return

    console.print(f"[blue]Resuming from: {orchestrator.state.errors.paused_reason}[/blue]")

    try:
        result = orchestrator.resume()

        if result.success:
            console.print("[green]Resumed successfully[/green]")
            console.print(f"  Message: {result.message}")
        else:
            console.print(f"[red]Resume failed: {result.error}[/red]")
            sys.exit(1)

    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        sys.exit(1)


@main.command()
@click.option("--keep-project", is_flag=True, help="Keep current project ID")
@click.confirmation_option(prompt="Are you sure you want to reset?")
def reset(keep_project: bool):
    """Reset the orchestrator state."""
    orchestrator = create_orchestrator()

    try:
        orchestrator.reset(keep_project=keep_project)
        console.print("[green]State reset successfully[/green]")
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        sys.exit(1)


@main.command()
@click.option("--dry-run", is_flag=True, help="Show what would be pushed")
def push(dry_run: bool):
    """Push all committed changes to remote."""
    orchestrator = create_orchestrator(dry_run)

    try:
        if dry_run:
            console.print("[yellow]Dry run - would push to remote[/yellow]")
            return

        success = orchestrator.push_changes()
        if success:
            console.print("[green]Changes pushed successfully[/green]")
        else:
            console.print("[red]Push failed[/red]")
            sys.exit(1)

    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        sys.exit(1)


# =============================================================================
# Backlog-based workflow commands
# =============================================================================

@main.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose/debug logging")
@click.pass_context
def backlog(ctx, verbose: bool):
    """
    Backlog-based workflow commands.

    This is the recommended workflow where:
    - Ideas are generated and stored as GitHub Issues
    - Humans promote ideas to plans via labels
    - Humans promote plans to development via labels
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    if verbose:
        setup_logging(level=logging.DEBUG)
        console.print("[dim]Verbose logging enabled[/dim]")


@backlog.command("run")
@click.option("--ideas", "-i", type=int, default=1, help="Number of traditional ideas to generate")
@click.option("--trend-ideas", "-t", type=int, default=0, help="Number of trend-based ideas to generate")
@click.option("--analyze-trends", is_flag=True, help="Run trend analysis from RSS feeds")
@click.option("--no-ideas", is_flag=True, help="Skip idea generation")
@click.option("--max-promotions", "-m", type=int, default=5, help="Max promotions to process")
@click.option("--dry-run", is_flag=True, help="Run without making changes")
def backlog_run(
    ideas: int,
    trend_ideas: int,
    analyze_trends: bool,
    no_ideas: bool,
    max_promotions: int,
    dry_run: bool,
):
    """
    Run one orchestration cycle.

    Generates ideas (traditional and/or trend-based), processes promotions,
    and starts development for promoted items.

    Examples:
        ao backlog run                          # 1 traditional idea
        ao backlog run -i 2 -t 2 --analyze-trends  # 2 traditional + 2 trend-based
        ao backlog run -t 3                     # 3 trend-based ideas only
    """
    # Validate environment before proceeding
    validate_backlog_env_or_exit()

    console.print("[bold blue]Running backlog orchestration cycle[/bold blue]")

    if dry_run:
        console.print("[yellow](Dry run mode)[/yellow]")

    if analyze_trends or trend_ideas > 0:
        console.print(f"[cyan]Trend analysis: enabled[/cyan]")
        if trend_ideas > 0:
            console.print(f"[cyan]Trend-based ideas: {trend_ideas}[/cyan]")

    orchestrator = BacklogOrchestrator(dry_run=dry_run)

    try:
        with console.status("[bold green]Processing...[/bold green]"):
            results = orchestrator.run_cycle(
                generate_ideas=not no_ideas,
                idea_count=ideas,
                trend_idea_count=trend_ideas,
                run_trend_analysis=analyze_trends,
                max_promotions=max_promotions,
            )

        if "error" in results:
            console.print(f"[bold red]Error: {results['error']}[/bold red]")
            sys.exit(1)

        # Show results
        console.print("\n[bold]Cycle Results:[/bold]")
        console.print(f"  Traditional ideas: {results['ideas_generated']}")
        console.print(f"  Trend-based ideas: {results['trend_ideas_generated']}")
        if results.get('trends_analyzed'):
            console.print(f"  Trend analysis: [green]completed[/green]")
        if results.get('plans_rejected', 0) > 0:
            console.print(f"  Plans rejected: {results['plans_rejected']}")
        console.print(f"  Plans generated: {results['plans_generated']}")
        console.print(f"  Dev projects started: {results['devs_started']}")

        if results.get("errors"):
            console.print("\n[yellow]Warnings:[/yellow]")
            for error in results["errors"]:
                console.print(f"  - {error}")

    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        sys.exit(1)


@backlog.command("generate")
@click.option("--count", "-c", type=int, default=1, help="Number of ideas to generate")
@click.option("--dry-run", is_flag=True, help="Run without making changes")
def backlog_generate(count: int, dry_run: bool):
    """Generate new idea issues."""
    # Validate environment before proceeding
    validate_backlog_env_or_exit()

    console.print(f"[bold blue]Generating {count} idea(s)...[/bold blue]")

    if dry_run:
        console.print("[yellow](Dry run mode)[/yellow]")

    orchestrator = BacklogOrchestrator(dry_run=dry_run)

    try:
        with console.status("[bold green]Generating ideas...[/bold green]"):
            ideas = orchestrator.idea_generator.generate_ideas(count=count)

        console.print(f"\n[green]Created {len(ideas)} idea issue(s)[/green]")
        for idea in ideas:
            console.print(f"  #{idea.number}: {idea.title}")
            console.print(f"    {idea.html_url}")

    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        sys.exit(1)


@backlog.command("process")
@click.option("--max", "-m", type=int, default=5, help="Max items to process")
@click.option("--dry-run", is_flag=True, help="Run without making changes")
def backlog_process(max: int, dry_run: bool):
    """Process pending promotions only (no idea generation)."""
    # Validate environment before proceeding
    validate_backlog_env_or_exit()

    console.print("[bold blue]Processing pending promotions...[/bold blue]")

    if dry_run:
        console.print("[yellow](Dry run mode)[/yellow]")

    orchestrator = BacklogOrchestrator(dry_run=dry_run)

    try:
        with console.status("[bold green]Processing...[/bold green]"):
            results = orchestrator.run_cycle(
                generate_ideas=False,
                max_promotions=max,
            )

        if "error" in results:
            console.print(f"[bold red]Error: {results['error']}[/bold red]")
            sys.exit(1)

        console.print("\n[bold]Results:[/bold]")
        if results.get('plans_rejected', 0) > 0:
            console.print(f"  Plans rejected: {results['plans_rejected']}")
        console.print(f"  Plans generated: {results['plans_generated']}")
        console.print(f"  Dev projects started: {results['devs_started']}")

    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        sys.exit(1)


@backlog.command("status")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def backlog_status(as_json: bool):
    """Show backlog status."""
    orchestrator = BacklogOrchestrator()

    try:
        status_data = orchestrator.get_status()

        if as_json:
            import json
            click.echo(json.dumps(status_data, indent=2))
            return

        if "error" in status_data:
            console.print(f"[bold red]Error: {status_data['error']}[/bold red]")
            sys.exit(1)

        # Backlog summary
        backlog = status_data["backlog"]
        pending = status_data["pending_promotion"]

        console.print(Panel(
            f"[bold]Backlog Ideas:[/bold] {backlog['ideas']} "
            f"([cyan]{backlog.get('trend_ideas', 0)} from trends[/cyan])\n"
            f"[bold]Backlog Plans:[/bold] {backlog['plans']}\n\n"
            f"[bold]Pending Promotions:[/bold]\n"
            f"  Ideas → Plan: {pending['ideas_to_plan']}\n"
            f"  Plans → Dev: {pending['plans_to_dev']}",
            title="Backlog Status",
            border_style="blue",
        ))

        # Recent ideas
        if status_data.get("issues", {}).get("ideas"):
            console.print("\n[bold]Recent Ideas:[/bold]")
            for idea in status_data["issues"]["ideas"][:5]:
                console.print(f"  #{idea['number']}: {idea['title']}")

        # Recent plans
        if status_data.get("issues", {}).get("plans"):
            console.print("\n[bold]Recent Plans:[/bold]")
            for plan in status_data["issues"]["plans"][:5]:
                console.print(f"  #{plan['number']}: {plan['title']}")

        console.print("\n[dim]To promote an idea: Add 'promote:to-plan' label[/dim]")
        console.print("[dim]To start development: Add 'promote:to-dev' label[/dim]")
        console.print("[dim]To reject a plan: Add 'reject:plan' label or use 'ao backlog reject'[/dim]")
        console.print("[dim]To see trend analysis: Run 'ao backlog trends-status'[/dim]")

    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        sys.exit(1)


@backlog.command("reject")
@click.argument("plan_number", type=int)
@click.option("--force", "-f", is_flag=True, help="Skip confirmation")
def backlog_reject(plan_number: int, force: bool):
    """
    Reject a PLAN and reset its idea for re-planning.

    This will:
    1. Close the specified PLAN issue
    2. Reset the original IDEA to backlog with promote:to-plan label
    3. A new plan will be generated in the next orchestrator cycle

    Example:
        ao backlog reject 42
    """
    # Validate environment
    validate_backlog_env_or_exit()

    orchestrator = BacklogOrchestrator()

    try:
        # Get plan info first
        from .github_client import Labels

        plan_issue = orchestrator.github.get_issue(plan_number)

        if not plan_issue.has_label(Labels.TYPE_PLAN):
            console.print(f"[bold red]Error: Issue #{plan_number} is not a PLAN issue[/bold red]")
            sys.exit(1)

        if plan_issue.state == "closed":
            console.print(f"[bold red]Error: Plan #{plan_number} is already closed[/bold red]")
            sys.exit(1)

        # Show plan info
        console.print(Panel(
            f"[bold]#{plan_number}:[/bold] {plan_issue.title}\n"
            f"[dim]State: {plan_issue.state}[/dim]",
            title="Plan to Reject",
            border_style="yellow",
        ))

        # Confirm
        if not force:
            if not click.confirm("Are you sure you want to reject this plan?"):
                console.print("[yellow]Cancelled[/yellow]")
                return

        # Reject the plan
        with console.status("[bold green]Rejecting plan...[/bold green]"):
            result = orchestrator.reject_plan_manually(plan_number)

        if "error" in result:
            console.print(f"[bold red]Error: {result['error']}[/bold red]")
            sys.exit(1)

        console.print(f"[bold green]Success![/bold green] {result['message']}")
        console.print("\n[dim]The idea has been reset and will be re-planned in the next cycle.[/dim]")
        console.print("[dim]Run 'ao backlog process' to generate a new plan immediately.[/dim]")

    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        sys.exit(1)


@backlog.command("analyze-trends")
@click.option("--dry-run", is_flag=True, help="Run without making changes")
def backlog_analyze_trends(dry_run: bool):
    """
    Fetch RSS feeds and analyze current trends.

    Fetches articles from configured RSS feeds and uses Claude to identify
    trending topics. Results are stored in data/trends/ directory.
    """
    console.print("[bold blue]Analyzing trends from RSS feeds...[/bold blue]")

    if dry_run:
        console.print("[yellow](Dry run mode)[/yellow]")

    orchestrator = BacklogOrchestrator(dry_run=dry_run)

    try:
        with console.status("[bold green]Fetching feeds and analyzing...[/bold green]"):
            analyses = orchestrator.trend_generator.run_daily_analysis()

        if not analyses:
            console.print("[yellow]No trends analyzed (no feed items available)[/yellow]")
            return

        console.print("\n[bold]Trend Analysis Results:[/bold]")

        for period, analysis in analyses.items():
            period_label = {"24h": "24 Hours", "1w": "1 Week", "1m": "1 Month"}.get(period, period)
            console.print(f"\n[cyan]{period_label}:[/cyan]")
            console.print(f"  Articles analyzed: {analysis.raw_article_count}")
            console.print(f"  Trends identified: {len(analysis.trends)}")

            if analysis.trends:
                console.print("  Top trends:")
                for i, trend in enumerate(analysis.trends[:5], 1):
                    console.print(f"    {i}. {trend.topic} (score: {trend.score:.1f})")

        console.print("\n[green]Trend analysis saved to data/trends/[/green]")

    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        sys.exit(1)


@backlog.command("generate-trends")
@click.option("--count", "-c", type=int, default=2, help="Number of trend-based ideas to generate")
@click.option("--dry-run", is_flag=True, help="Run without making changes")
def backlog_generate_trends(count: int, dry_run: bool):
    """
    Generate ideas based on current trends.

    Analyzes RSS feeds to identify trends, then generates Web3 micro-service
    ideas based on the top trending topics.
    """
    # Validate environment before proceeding
    validate_backlog_env_or_exit()

    console.print(f"[bold blue]Generating {count} trend-based idea(s)...[/bold blue]")

    if dry_run:
        console.print("[yellow](Dry run mode)[/yellow]")

    orchestrator = BacklogOrchestrator(dry_run=dry_run)

    try:
        with console.status("[bold green]Analyzing trends and generating ideas...[/bold green]"):
            ideas = orchestrator.trend_generator.generate_trend_based_ideas(count=count)

        if not ideas:
            console.print("[yellow]No ideas generated (no significant trends found)[/yellow]")
            return

        console.print(f"\n[green]Created {len(ideas)} trend-based idea(s)[/green]")
        for idea in ideas:
            console.print(f"  #{idea.number}: {idea.title}")
            console.print(f"    {idea.html_url}")

    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        sys.exit(1)


@backlog.command("trends-status")
@click.option("--days", "-d", type=int, default=7, help="Days of history to show")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def backlog_trends_status(days: int, as_json: bool):
    """
    Show trend analysis history and idea links.

    Displays recent trend analyses and which ideas were generated
    from which trends.
    """
    orchestrator = BacklogOrchestrator()

    try:
        status_data = orchestrator.get_trend_status(days=days)

        if as_json:
            import json
            click.echo(json.dumps(status_data, indent=2, default=str))
            return

        console.print(Panel(
            f"[bold]Analyses Available:[/bold] {status_data['analyses_available']} (last {days} days)\n"
            f"[bold]Ideas from Trends:[/bold] {status_data['total_ideas_from_trends']}",
            title="Trend Analysis Status",
            border_style="cyan",
        ))

        # Recent analyses
        if status_data.get("recent_trends"):
            console.print("\n[bold]Recent Analyses:[/bold]")
            for analysis in status_data["recent_trends"]:
                if analysis.get("date"):
                    console.print(
                        f"  {analysis['date']}: {analysis['total_trends']} trends "
                        f"({', '.join(analysis['periods'])})"
                    )

        # Idea links
        if status_data.get("idea_links"):
            console.print("\n[bold]Recent Trend-Based Ideas:[/bold]")
            for link in status_data["idea_links"]:
                console.print(
                    f"  #{link['issue']}: {link['trend']} [{link['category']}]"
                )

        console.print("\n[dim]Run 'ao backlog analyze-trends' to run new analysis[/dim]")
        console.print("[dim]Run 'ao backlog generate-trends' to generate trend ideas[/dim]")

    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        sys.exit(1)


@backlog.command("setup")
def backlog_setup():
    """Set up required labels in the repository."""
    console.print("[bold blue]Setting up labels...[/bold blue]")

    orchestrator = BacklogOrchestrator()

    try:
        orchestrator.setup_labels()
        console.print("[green]Labels created successfully![/green]")
        console.print("\nCreated labels:")
        from .github_client import Labels
        for label in Labels.ALL_LABELS.keys():
            console.print(f"  - {label}")

    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
