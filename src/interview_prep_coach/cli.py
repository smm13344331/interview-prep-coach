"""Command-line interface for interview prep coach."""

import sys
import click
from pathlib import Path

from .config.installer import ClaudeCodeInstaller
from .config.paths import get_data_dir, get_progress_file, get_improvement_file
from .core import ProgressTracker


@click.group()
@click.version_option(version="1.0.0", prog_name="interview-prep-coach")
def cli():
    """Interview Preparation Coach - AI-powered interview prep for senior engineers."""
    pass


@cli.command()
@click.option('--force', is_flag=True, help='Force reinstall even if already installed')
def install(force):
    """Install interview prep coach to Claude Code."""
    click.echo("🚀 Installing Interview Prep Coach...")
    click.echo()

    installer = ClaudeCodeInstaller()

    # Check if already installed
    if not force:
        is_installed, details = installer.is_installed()
        if is_installed:
            click.echo("✓ Interview Prep Coach is already installed!")
            click.echo()
            click.echo("Components:")
            click.echo(f"  - Skill (/prep): {'✓' if details['skill'] else '✗'}")
            click.echo(f"  - MCP Server: {'✓' if details['mcp_server'] else '✗'}")
            click.echo()
            click.echo("Use --force to reinstall.")
            return

    # Perform installation
    results = installer.install(force=force)

    if results['success']:
        click.echo("✅ Installation successful!")
        click.echo()
        click.echo("Components installed:")
        click.echo(f"  ✓ Skill: /prep")
        click.echo(f"  ✓ MCP Server: interview-prep-coach")
        click.echo(f"  ✓ Data directory: {get_data_dir()}")
        click.echo()
        click.secho("⚠️  IMPORTANT: Restart Claude Code for changes to take effect", fg='yellow', bold=True)
        click.echo()
        click.echo("Usage:")
        click.echo("  1. Start Claude Code")
        click.echo("  2. Type: /prep")
        click.echo("  3. Choose mode:")
        click.echo("     - /prep             → Continue last session")
        click.echo("     - /prep weak        → Practice weak areas")
        click.echo("     - /prep mock        → Mock interview mode")
        click.echo("     - /prep section Java → Practice specific section")
        click.echo()
        click.echo("For more info: interview-prep-coach status")
    else:
        click.secho("❌ Installation failed!", fg='red', bold=True)
        click.echo()
        if results['errors']:
            click.echo("Errors:")
            for error in results['errors']:
                click.echo(f"  - {error}")
        click.echo()
        click.echo("Steps completed:")
        for step, status in results['steps'].items():
            status_icon = '✓' if status else '✗'
            click.echo(f"  {status_icon} {step}")
        sys.exit(1)


@cli.command()
@click.option('--remove-data', is_flag=True, help='Also remove user data (progress, improvements)')
@click.confirmation_option(prompt='Are you sure you want to uninstall?')
def uninstall(remove_data):
    """Uninstall interview prep coach from Claude Code."""
    click.echo("🗑️  Uninstalling Interview Prep Coach...")
    click.echo()

    if remove_data:
        click.secho("⚠️  This will also delete your progress and improvement data!", fg='yellow', bold=True)
        if not click.confirm('Are you absolutely sure?'):
            click.echo("Uninstall cancelled.")
            return

    installer = ClaudeCodeInstaller()
    results = installer.uninstall(remove_data=remove_data)

    if results['success']:
        click.echo("✅ Uninstallation successful!")
        click.echo()
        click.echo("Components removed:")
        click.echo(f"  {'✓' if results['steps'].get('skill_removed') else '✗'} Skill (/prep)")
        click.echo(f"  {'✓' if results['steps'].get('mcp_server_removed') else '✗'} MCP Server")
        if remove_data:
            click.echo(f"  {'✓' if results['steps'].get('data_removed') else '✗'} User data")
        else:
            click.echo(f"  ℹ User data preserved at: {get_data_dir()}")
        click.echo()
        click.echo("Restart Claude Code for changes to take effect.")
    else:
        click.secho("❌ Uninstallation failed!", fg='red', bold=True)
        click.echo()
        if results['errors']:
            click.echo("Errors:")
            for error in results['errors']:
                click.echo(f"  - {error}")


@cli.command()
def status():
    """Show installation status and statistics."""
    installer = ClaudeCodeInstaller()
    status_info = installer.get_status()

    click.echo("📊 Interview Prep Coach Status")
    click.echo("=" * 50)
    click.echo()

    # Installation status
    if status_info['installed']:
        click.secho("✅ Status: INSTALLED", fg='green', bold=True)
    else:
        click.secho("⚠️  Status: NOT FULLY INSTALLED", fg='yellow', bold=True)

    click.echo()
    click.echo("Components:")
    click.echo(f"  - Skill (/prep): {'✓' if status_info['components']['skill'] else '✗'}")
    click.echo(f"  - MCP Server: {'✓' if status_info['components']['mcp_server'] else '✗'}")
    click.echo(f"  - Data files: {'✓' if status_info['data_initialized'] else '✗'}")

    click.echo()
    click.echo("Locations:")
    click.echo(f"  - Data directory: {status_info['data_directory']}")
    click.echo(f"  - Skill location: {status_info['skill_location']}")
    click.echo(f"  - Settings: {status_info['settings_location']}")

    # Progress statistics if installed
    if status_info['data_initialized']:
        try:
            tracker = ProgressTracker()
            stats = tracker.get_statistics()

            click.echo()
            click.echo("Progress Statistics:")
            click.echo(f"  - Questions answered: {stats['overallProgress']['totalQuestionsAsked']}")
            click.echo(f"  - Correct answers: {stats['overallProgress']['totalQuestionsCorrect']}")
            click.echo(f"  - Accuracy: {stats['overallProgress']['accuracy'] * 100:.1f}%")
            click.echo(f"  - Current section: {stats['currentSection']}")
            click.echo(f"  - Weak areas: {stats['totalWeakAreas']}")
            click.echo(f"  - Strong areas: {stats['totalStrongAreas']}")
        except Exception as e:
            click.echo()
            click.echo(f"Could not load progress: {e}")

    click.echo()


@cli.command()
@click.confirmation_option(prompt='This will delete all your progress. Are you sure?')
def reset():
    """Reset all progress data."""
    click.echo("🔄 Resetting progress...")

    try:
        tracker = ProgressTracker()
        tracker.reset_progress()

        # Also reset improvement log
        from .core import ImprovementLogger
        logger = ImprovementLogger()
        improvement_file = get_improvement_file()
        if improvement_file.exists():
            improvement_file.unlink()

        from .config.paths import ensure_data_files_exist
        ensure_data_files_exist()

        click.echo("✅ Progress reset successfully!")
        click.echo()
        click.echo("All data has been reset to initial state.")
    except Exception as e:
        click.secho(f"❌ Failed to reset progress: {e}", fg='red', bold=True)
        sys.exit(1)


@cli.command()
def info():
    """Show information about the interview prep system."""
    click.echo("📚 Interview Prep Coach")
    click.echo("=" * 50)
    click.echo()
    click.echo("A comprehensive interview preparation system for senior software engineers.")
    click.echo()
    click.echo("Coverage:")
    click.echo("  • Java Core Concepts (Memory, Concurrency, Collections, Modern Features)")
    click.echo("  • Spring Framework (Boot, Data JPA, MVC, Security, Reactive)")
    click.echo("  • Databases (SQL, MongoDB, Redis)")
    click.echo("  • Docker (Containerization, Best Practices)")
    click.echo("  • Kubernetes (Core & Advanced Concepts)")
    click.echo("  • System Design (Patterns & Architecture)")
    click.echo()
    click.echo("Features:")
    click.echo("  ✓ 150+ curated questions and answers")
    click.echo("  ✓ Interactive AI coach with progress tracking")
    click.echo("  ✓ Adaptive difficulty based on performance")
    click.echo("  ✓ Weak area identification and practice")
    click.echo("  ✓ Mock interview mode")
    click.echo("  ✓ Continuous improvement system")
    click.echo()
    click.echo("Commands:")
    click.echo("  install    - Install to Claude Code")
    click.echo("  uninstall  - Remove from Claude Code")
    click.echo("  status     - Show installation and progress")
    click.echo("  reset      - Reset all progress")
    click.echo("  info       - Show this information")
    click.echo()
    click.echo("After installation, use /prep in Claude Code to start practicing!")


if __name__ == '__main__':
    cli()
