"""Command-line interface for interview prep coach."""

import sys
import json
import click
from pathlib import Path

# Check version requirements before any other imports
from ._version_check import check_versions
check_versions()

from .config.installer import ClaudeCodeInstaller
from .config.paths import get_data_dir, get_database_file
from .core import DatabaseManager, ProgressTracker, MaterialEditor


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
        # Initialize database and import bundled material
        try:
            db = DatabaseManager()
            db.initialize_schema()

            if db.count_records("materials") == 0:
                click.echo("  ✓ Initializing database...")
                from .plugins.bundled import JavaSpringPlugin

                # Fresh install - import bundled material
                plugin = JavaSpringPlugin()
                db.execute(
                    """INSERT INTO materials (id, name, description, version, source_type, is_active)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (plugin.plugin_id, plugin.name, plugin.description, plugin.version, 'bundled', True)
                )
                if plugin.import_material(db, plugin.plugin_id):
                    click.echo("  ✓ Imported bundled material")
        except Exception as e:
            click.secho(f"  ⚠ Database initialization warning: {e}", fg='yellow')

        click.echo()
        click.echo("✅ Installation successful!")
        click.echo()
        click.echo("Components installed:")
        click.echo(f"  ✓ Skill: /prep")
        click.echo(f"  ✓ MCP Server: interview-prep-coach")
        click.echo(f"  ✓ Database: {get_database_file()}")
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
        click.echo("Manage materials: interview-prep-coach materials --help")
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
@click.option('--remove-data', is_flag=True, help='Also remove database (all progress and materials)')
@click.confirmation_option(prompt='Are you sure you want to uninstall?')
def uninstall(remove_data):
    """Uninstall interview prep coach from Claude Code."""
    click.echo("🗑️  Uninstalling Interview Prep Coach...")
    click.echo()

    if remove_data:
        click.secho("⚠️  This will delete your database with all progress and materials!", fg='yellow', bold=True)
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
            click.echo(f"  {'✓' if results['steps'].get('data_removed') else '✗'} Database")
        else:
            click.echo(f"  ℹ Database preserved at: {get_database_file()}")
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
    click.echo(f"  - Database: {'✓' if get_database_file().exists() else '✗'}")

    click.echo()
    click.echo("Locations:")
    click.echo(f"  - Data directory: {status_info['data_directory']}")
    click.echo(f"  - Database: {get_database_file()}")
    click.echo(f"  - Skill location: {status_info['skill_location']}")
    click.echo(f"  - Settings: {status_info['settings_location']}")

    # Database statistics if it exists
    if get_database_file().exists():
        try:
            db = DatabaseManager()

            # Active material info
            active_material = db.fetchone("SELECT * FROM materials WHERE is_active = TRUE")
            if active_material:
                click.echo()
                click.echo("Active Material:")
                click.echo(f"  - Name: {active_material['name']}")
                click.echo(f"  - ID: {active_material['id']}")
                click.echo(f"  - Source: {active_material['source_type']}")

                # Question count
                question_count = db.count_records("questions", "material_id = ?", (active_material['id'],))
                click.echo(f"  - Questions: {question_count}")

            # Total materials
            material_count = db.count_records("materials")
            click.echo()
            click.echo(f"Total Materials: {material_count}")

            # Progress statistics
            if active_material:
                tracker = ProgressTracker(db)
                stats = tracker.get_statistics(active_material['id'])

                click.echo()
                click.echo("Progress Statistics:")
                click.echo(f"  - Questions answered: {stats['overallProgress']['totalQuestionsAsked']}")
                click.echo(f"  - Correct answers: {stats['overallProgress']['totalQuestionsCorrect']}")
                click.echo(f"  - Accuracy: {stats['overallProgress']['accuracy'] * 100:.1f}%")
                click.echo(f"  - Weak areas: {stats['totalWeakAreas']}")
                click.echo(f"  - Strong areas: {stats['totalStrongAreas']}")

        except Exception as e:
            click.echo()
            click.echo(f"Could not load database statistics: {e}")

    click.echo()


@cli.command()
@click.option('--material-id', help='Material ID to reset (default: active material)')
@click.confirmation_option(prompt='This will delete all progress for this material. Are you sure?')
def reset(material_id):
    """Reset progress data for a material."""
    click.echo("🔄 Resetting progress...")

    try:
        db = DatabaseManager()

        # Get material ID
        if not material_id:
            active = db.fetchone("SELECT id FROM materials WHERE is_active = TRUE")
            if not active:
                click.secho("❌ No active material found", fg='red')
                sys.exit(1)
            material_id = active['id']

        # Verify material exists
        material = db.fetchone("SELECT name FROM materials WHERE id = ?", (material_id,))
        if not material:
            click.secho(f"❌ Material not found: {material_id}", fg='red')
            sys.exit(1)

        tracker = ProgressTracker(db)
        tracker.reset_progress(material_id)

        click.echo(f"✅ Progress reset successfully for: {material['name']}")
    except Exception as e:
        click.secho(f"❌ Failed to reset progress: {e}", fg='red', bold=True)
        sys.exit(1)


@cli.group()
def materials():
    """Manage interview material sources."""
    pass


@materials.command('list')
@click.option('--all', 'show_all', is_flag=True, help='Show all materials including inactive')
def list_materials(show_all):
    """List all material sources."""
    try:
        db = DatabaseManager()

        query = "SELECT * FROM materials"
        if not show_all:
            query += " WHERE is_active = TRUE"
        query += " ORDER BY name"

        materials_list = db.fetchall(query)

        if not materials_list:
            click.echo("No materials found.")
            return

        click.echo("📚 Interview Materials")
        click.echo("=" * 70)
        click.echo()

        for mat in materials_list:
            # Get question count
            question_count = db.count_records("questions", "material_id = ?", (mat['id'],))

            status = "●" if mat['is_active'] else "○"
            click.echo(f"{status} {mat['name']}")
            click.echo(f"  ID: {mat['id']}")
            click.echo(f"  Source: {mat['source_type']}")
            click.echo(f"  Questions: {question_count}")
            click.echo(f"  Version: {mat['version']}")
            if mat['description']:
                click.echo(f"  Description: {mat['description']}")
            click.echo()

    except Exception as e:
        click.secho(f"❌ Error: {e}", fg='red')
        sys.exit(1)


@materials.command('info')
@click.argument('material_id')
def material_info(material_id):
    """Show detailed information about a material."""
    try:
        db = DatabaseManager()
        editor = MaterialEditor(db)

        info = editor.get_material_info(material_id)

        if 'error' in info:
            click.secho(f"❌ {info['error']}", fg='red')
            sys.exit(1)

        click.echo(f"📄 Material: {info['name']}")
        click.echo("=" * 50)
        click.echo()
        click.echo(f"ID: {info['id']}")
        click.echo(f"Description: {info['description']}")
        click.echo(f"Version: {info['version']}")
        click.echo(f"Source Type: {info['source_type']}")
        click.echo(f"Status: {'Active' if info['is_active'] else 'Inactive'}")
        click.echo()
        click.echo(f"Questions: {info['question_count']}")
        click.echo(f"Sections: {info['section_count']}")
        click.echo()
        click.echo(f"Created: {info['created_at']}")
        click.echo(f"Updated: {info['updated_at']}")

    except Exception as e:
        click.secho(f"❌ Error: {e}", fg='red')
        sys.exit(1)


@materials.command('activate')
@click.argument('material_id')
def activate_material(material_id):
    """Activate a material source."""
    try:
        db = DatabaseManager()

        # Check material exists
        material = db.fetchone("SELECT name FROM materials WHERE id = ?", (material_id,))
        if not material:
            click.secho(f"❌ Material not found: {material_id}", fg='red')
            sys.exit(1)

        # Deactivate all, activate specified
        db.execute("UPDATE materials SET is_active = FALSE")
        db.execute("UPDATE materials SET is_active = TRUE WHERE id = ?", (material_id,))

        click.echo(f"✅ Activated material: {material['name']}")

    except Exception as e:
        click.secho(f"❌ Error: {e}", fg='red')
        sys.exit(1)


@materials.command('import')
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--id', 'material_id', required=True, help='Unique material ID')
@click.option('--name', required=True, help='Display name for material')
@click.option('--format', type=click.Choice(['markdown', 'json']), default='markdown', help='File format')
def import_material(file_path, material_id, name, format):
    """Import questions from a file."""
    try:
        from .plugins.importers import MarkdownImporter, JSONImporter

        db = DatabaseManager()
        file_path = Path(file_path)

        # Check if material ID already exists
        existing = db.fetchone("SELECT id FROM materials WHERE id = ?", (material_id,))
        if existing:
            click.secho(f"❌ Material ID already exists: {material_id}", fg='red')
            sys.exit(1)

        click.echo(f"📥 Importing from {file_path.name}...")

        # Register material
        db.execute(
            """INSERT INTO materials (id, name, description, version, source_type, is_active)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (material_id, name, f"Imported from {file_path.name}", "1.0.0", "user", False)
        )

        # Import questions
        if format == 'markdown':
            importer = MarkdownImporter()
            count = importer.import_to_db(db, material_id, file_path)
        else:
            importer = JSONImporter()
            count = importer.import_to_db(db, material_id, file_path)

        click.echo(f"✅ Imported {count} questions as material: {material_id}")
        click.echo()
        click.echo(f"To activate: interview-prep-coach materials activate {material_id}")

    except Exception as e:
        click.secho(f"❌ Error: {e}", fg='red')
        sys.exit(1)


@materials.command('clone')
@click.argument('source_id')
@click.argument('new_id')
@click.option('--name', required=True, help='Name for cloned material')
def clone_material(source_id, new_id, name):
    """Clone an existing material for customization."""
    try:
        db = DatabaseManager()
        editor = MaterialEditor(db)

        click.echo(f"📋 Cloning {source_id} to {new_id}...")

        success = editor.clone_material(source_id, new_id, name)

        if success:
            click.echo(f"✅ Material cloned successfully")
            click.echo()
            click.echo(f"To activate: interview-prep-coach materials activate {new_id}")
        else:
            click.secho("❌ Failed to clone material", fg='red')
            sys.exit(1)

    except Exception as e:
        click.secho(f"❌ Error: {e}", fg='red')
        sys.exit(1)


@materials.command('delete')
@click.argument('material_id')
@click.confirmation_option(prompt='This will delete the material and all associated data. Are you sure?')
def delete_material(material_id):
    """Delete a material source."""
    try:
        db = DatabaseManager()

        # Check if active
        active = db.fetchone("SELECT id FROM materials WHERE is_active = TRUE AND id = ?", (material_id,))
        if active:
            click.secho("❌ Cannot delete active material. Activate another material first.", fg='red')
            sys.exit(1)

        # Get material name for confirmation
        material = db.fetchone("SELECT name FROM materials WHERE id = ?", (material_id,))
        if not material:
            click.secho(f"❌ Material not found: {material_id}", fg='red')
            sys.exit(1)

        # Delete (CASCADE will remove questions, progress, etc.)
        db.execute("DELETE FROM materials WHERE id = ?", (material_id,))

        click.echo(f"✅ Deleted material: {material['name']}")

    except Exception as e:
        click.secho(f"❌ Error: {e}", fg='red')
        sys.exit(1)


@materials.command('export')
@click.argument('material_id', required=False)
@click.option('--output', '-o', required=True, type=click.Path(), help='Output file path')
def export_material(material_id, output):
    """Export material to markdown file."""
    try:
        db = DatabaseManager()
        editor = MaterialEditor(db)

        # Get material ID
        if not material_id:
            active = db.fetchone("SELECT id, name FROM materials WHERE is_active = TRUE")
            if not active:
                click.secho("❌ No active material found", fg='red')
                sys.exit(1)
            material_id = active['id']
            material_name = active['name']
        else:
            material = db.fetchone("SELECT name FROM materials WHERE id = ?", (material_id,))
            if not material:
                click.secho(f"❌ Material not found: {material_id}", fg='red')
                sys.exit(1)
            material_name = material['name']

        click.echo(f"📤 Exporting {material_name}...")

        success = editor.export_material_to_markdown(material_id, Path(output))

        if success:
            click.echo(f"✅ Exported to {output}")
        else:
            click.secho("❌ Export failed", fg='red')
            sys.exit(1)

    except Exception as e:
        click.secho(f"❌ Error: {e}", fg='red')
        sys.exit(1)


@cli.command()
def info():
    """Show information about the interview prep system."""
    click.echo("📚 Interview Prep Coach")
    click.echo("=" * 50)
    click.echo()
    click.echo("A comprehensive interview preparation system for senior software engineers.")
    click.echo()
    click.echo("Default Coverage:")
    click.echo("  • Java Core Concepts (Memory, Concurrency, Collections, Modern Features)")
    click.echo("  • Spring Framework (Boot, Data JPA, MVC, Security, Reactive)")
    click.echo("  • Databases (SQL, MongoDB, Redis)")
    click.echo("  • Docker (Containerization, Best Practices)")
    click.echo("  • Kubernetes (Core & Advanced Concepts)")
    click.echo("  • System Design (Patterns & Architecture)")
    click.echo()
    click.echo("Features:")
    click.echo("  ✓ Plugin-based material system (easily add custom topics)")
    click.echo("  ✓ Interactive AI coach with progress tracking")
    click.echo("  ✓ Adaptive difficulty based on performance")
    click.echo("  ✓ Weak area identification and practice")
    click.echo("  ✓ Mock interview mode")
    click.echo("  ✓ Continuous improvement system")
    click.echo()
    click.echo("Commands:")
    click.echo("  install      - Install to Claude Code")
    click.echo("  uninstall    - Remove from Claude Code")
    click.echo("  status       - Show installation and progress")
    click.echo("  reset        - Reset progress data")
    click.echo("  materials    - Manage material sources")
    click.echo("  info         - Show this information")
    click.echo()
    click.echo("Material Management:")
    click.echo("  materials list          - List all materials")
    click.echo("  materials info <id>     - Show material details")
    click.echo("  materials activate <id> - Switch active material")
    click.echo("  materials import <file> - Import from file")
    click.echo("  materials clone         - Clone for customization")
    click.echo("  materials export        - Export to markdown")
    click.echo("  materials delete <id>   - Delete material")
    click.echo()
    click.echo("After installation, use /prep in Claude Code to start practicing!")


if __name__ == '__main__':
    cli()
