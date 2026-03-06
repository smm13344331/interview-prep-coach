"""MCP server for interview prep coach."""

import json
import logging
from typing import Any, Sequence
from pathlib import Path

# Check version requirements before any other imports
from ._version_check import check_versions
check_versions()

from mcp.server import Server
from mcp.types import Tool, TextContent

from .core import (
    DatabaseManager,
    ProgressTracker,
    ImprovementLogger,
    QuestionParser,
    MaterialEditor,
    PluginManager
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize server
server = Server("interview-prep-coach")

# Initialize database
db_manager = DatabaseManager()
db_manager.initialize_schema()

# Check if database is empty and needs initial material
if db_manager.count_records("materials") == 0:
    logger.info("Empty database detected, importing bundled material")
    from .plugins.bundled import JavaSpringPlugin

    plugin = JavaSpringPlugin()

    # Register material
    db_manager.execute(
        """INSERT INTO materials (id, name, description, version, source_type, is_active)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            plugin.plugin_id,
            plugin.name,
            plugin.description,
            plugin.version,
            'bundled',
            True
        )
    )

    # Import questions
    if plugin.import_material(db_manager, plugin.plugin_id):
        logger.info(f"Successfully imported bundled material: {plugin.name}")
    else:
        logger.error("Failed to import bundled material")

# Initialize components with database
progress_tracker = ProgressTracker(db_manager)
improvement_logger = ImprovementLogger(db_manager)
question_parser = QuestionParser(db_manager)
material_editor = MaterialEditor(db_manager)
plugin_manager = PluginManager(db_manager)


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        # Progress tracking tools
        Tool(
            name="get-statistics",
            description="Get overall progress statistics and learning metrics for the active interview preparation material. Shows total questions answered, accuracy percentage, weak areas count, and strong areas. Use when starting a session or reviewing overall performance.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="update-progress",
            description="Record and track progress after a user answers an interview question. Saves the response (correct, incorrect, partial, or skipped) and optional notes about their understanding. Use after every question to maintain accurate learning statistics and identify weak areas. Essential for progress tracking.",
            inputSchema={
                "type": "object",
                "properties": {
                    "questionId": {
                        "type": "integer",
                        "description": "Question ID from database"
                    },
                    "response": {
                        "type": "string",
                        "description": "Response type: correct, incorrect, partial, skipped",
                        "enum": ["correct", "incorrect", "partial", "skipped"]
                    },
                    "notes": {
                        "type": "string",
                        "description": "Optional notes about the answer"
                    }
                },
                "required": ["questionId", "response"]
            }
        ),
        Tool(
            name="get-weak-areas",
            description="Identify weak areas and topics where the user is struggling based on performance below 60% accuracy. Returns sections and subsections that need more practice. Use when user wants to focus on improving specific topics or during targeted practice sessions.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="start-session",
            description="Begin a new interview practice session for tracking learning activity. Creates a session record with timestamp and returns a session ID. Use at the start of every practice session to enable session analytics, duration tracking, and question count per session.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="end-session",
            description="Complete and finalize the current interview practice session. Records session duration and question count. Use when user finishes practicing or wants to end their study session. Requires the session ID from start-session.",
            inputSchema={
                "type": "object",
                "properties": {
                    "sessionId": {
                        "type": "integer",
                        "description": "Session ID to end"
                    }
                },
                "required": ["sessionId"]
            }
        ),

        # Question retrieval tools
        Tool(
            name="get-sections",
            description="List all available topic sections in the active interview preparation material (e.g., 'Java Core Concepts', 'Spring Framework', 'System Design'). Use when user wants to browse available topics, choose what to practice, or see material structure. Returns section names only.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get-subsections",
            description="List all subtopics within a specific section of interview material (e.g., within 'Java Core Concepts' get 'Memory Management', 'Concurrency', 'Collections'). Use when user wants to see detailed topics within a section or choose a specific area to practice.",
            inputSchema={
                "type": "object",
                "properties": {
                    "section": {
                        "type": "string",
                        "description": "Section name"
                    }
                },
                "required": ["section"]
            }
        ),
        Tool(
            name="get-question",
            description="Get a specific question by section, subsection, and number",
            inputSchema={
                "type": "object",
                "properties": {
                    "section": {
                        "type": "string",
                        "description": "Section name"
                    },
                    "subsection": {
                        "type": "string",
                        "description": "Subsection name"
                    },
                    "questionNumber": {
                        "type": "integer",
                        "description": "Question number (1-indexed)"
                    }
                },
                "required": ["section", "subsection", "questionNumber"]
            }
        ),
        Tool(
            name="get-next-question",
            description="Retrieve the next sequential interview question in a subsection to continue practicing. Use when user says 'continue', 'next', 'keep going', or wants to resume from where they left off. Returns question text, answer, question ID, and metadata. Provide lastQuestionNumber (0 for first question) to get the subsequent question.",
            inputSchema={
                "type": "object",
                "properties": {
                    "section": {
                        "type": "string",
                        "description": "Section name"
                    },
                    "subsection": {
                        "type": "string",
                        "description": "Subsection name"
                    },
                    "lastQuestionNumber": {
                        "type": "integer",
                        "description": "Last question number answered (0 for first question)",
                        "default": 0
                    }
                },
                "required": ["section", "subsection"]
            }
        ),
        Tool(
            name="get-all-questions",
            description="Retrieve all interview questions within a specific subsection at once. Useful for random selection in mock interview mode, practicing weak areas, or getting a complete question pool. Returns array of all questions with IDs, text, and answers.",
            inputSchema={
                "type": "object",
                "properties": {
                    "section": {
                        "type": "string",
                        "description": "Section name"
                    },
                    "subsection": {
                        "type": "string",
                        "description": "Subsection name"
                    }
                },
                "required": ["section", "subsection"]
            }
        ),
        Tool(
            name="search-questions",
            description="Search for interview questions by keyword or topic using full-text search across all questions and answers. Use when user wants to find questions about specific concepts (e.g., 'dependency injection', 'REST API', 'garbage collection') or practice a particular technology.",
            inputSchema={
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "Keyword to search for"
                    }
                },
                "required": ["keyword"]
            }
        ),
        Tool(
            name="get-question-count",
            description="Get count of questions in section or subsection",
            inputSchema={
                "type": "object",
                "properties": {
                    "section": {
                        "type": "string",
                        "description": "Section name (optional)"
                    },
                    "subsection": {
                        "type": "string",
                        "description": "Subsection name (optional, requires section)"
                    }
                },
                "required": []
            }
        ),

        # Material editing tools
        Tool(
            name="edit-question",
            description="Edit a specific question's text or answer",
            inputSchema={
                "type": "object",
                "properties": {
                    "questionId": {
                        "type": "integer",
                        "description": "Question ID from database"
                    },
                    "newQuestion": {
                        "type": "string",
                        "description": "New question text (optional)"
                    },
                    "newAnswer": {
                        "type": "string",
                        "description": "New answer text (optional)"
                    }
                },
                "required": ["questionId"]
            }
        ),
        Tool(
            name="add-question",
            description="Add a new question to a section/subsection",
            inputSchema={
                "type": "object",
                "properties": {
                    "section": {
                        "type": "string",
                        "description": "Section name"
                    },
                    "subsection": {
                        "type": "string",
                        "description": "Subsection name"
                    },
                    "question": {
                        "type": "string",
                        "description": "Question text"
                    },
                    "answer": {
                        "type": "string",
                        "description": "Answer text"
                    },
                    "position": {
                        "type": "integer",
                        "description": "Position to insert (optional, null to append)"
                    }
                },
                "required": ["section", "subsection", "question", "answer"]
            }
        ),
        Tool(
            name="delete-question",
            description="Delete a question from the material",
            inputSchema={
                "type": "object",
                "properties": {
                    "questionId": {
                        "type": "integer",
                        "description": "Question ID to delete"
                    }
                },
                "required": ["questionId"]
            }
        ),

        # Improvement tracking tools
        Tool(
            name="log-improvement",
            description="Record quality issues or improvement suggestions for interview questions and materials. Use when noticing unclear questions, outdated information, missing topics, incorrect answers, or coverage gaps. Tracks improvement type, priority, and description for later review and implementation.",
            inputSchema={
                "type": "object",
                "properties": {
                    "improvementType": {
                        "type": "string",
                        "description": "Type of improvement",
                        "enum": [
                            "unclear_question",
                            "missing_topic",
                            "outdated_info",
                            "insufficient_coverage",
                            "answer_issue",
                            "difficulty_mismatch",
                            "missing_followup"
                        ]
                    },
                    "section": {
                        "type": "string",
                        "description": "Section name"
                    },
                    "subsection": {
                        "type": "string",
                        "description": "Subsection name"
                    },
                    "description": {
                        "type": "string",
                        "description": "Detailed description of the improvement"
                    },
                    "questionId": {
                        "type": "integer",
                        "description": "Question ID if applicable"
                    },
                    "priority": {
                        "type": "string",
                        "description": "Priority level",
                        "enum": ["low", "medium", "high", "critical"],
                        "default": "medium"
                    }
                },
                "required": ["improvementType", "section", "subsection", "description"]
            }
        ),
        Tool(
            name="get-improvements",
            description="Get improvements by status",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "Filter by status",
                        "enum": ["pending", "implemented"]
                    },
                    "section": {
                        "type": "string",
                        "description": "Filter by section"
                    },
                    "priority": {
                        "type": "string",
                        "description": "Filter by priority"
                    }
                },
                "required": ["status"]
            }
        ),
        Tool(
            name="mark-improvement-implemented",
            description="Mark an improvement as implemented",
            inputSchema={
                "type": "object",
                "properties": {
                    "improvementId": {
                        "type": "integer",
                        "description": "Improvement ID"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Implementation notes"
                    }
                },
                "required": ["improvementId"]
            }
        ),
        Tool(
            name="get-improvement-metrics",
            description="Get improvement tracking metrics",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),

        # Plugin/Material management tools
        Tool(
            name="list-materials",
            description="List all available interview preparation material sources and question banks (bundled, imported, or custom). Shows material names, IDs, source types, active status, and question counts. Use when user wants to see what materials are available or switch between different question sets.",
            inputSchema={
                "type": "object",
                "properties": {
                    "includeInactive": {
                        "type": "boolean",
                        "description": "Include inactive materials",
                        "default": False
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get-material-info",
            description="Get detailed information about an interview material source including name, description, version, question count, section count, source type, and timestamps. Use to check which material is currently active or inspect a specific material's details.",
            inputSchema={
                "type": "object",
                "properties": {
                    "materialId": {
                        "type": "string",
                        "description": "Material ID (optional, uses active if not specified)"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="activate-material",
            description="Switch to a different interview preparation material source or question bank. Makes the specified material active for practice sessions. Use when user wants to practice different topics (e.g., switch from Java to Python questions, or from general to company-specific interview prep).",
            inputSchema={
                "type": "object",
                "properties": {
                    "materialId": {
                        "type": "string",
                        "description": "Material ID to activate"
                    }
                },
                "required": ["materialId"]
            }
        ),
        Tool(
            name="import-material",
            description="Import questions from a file (markdown or JSON)",
            inputSchema={
                "type": "object",
                "properties": {
                    "filePath": {
                        "type": "string",
                        "description": "Path to file to import"
                    },
                    "materialId": {
                        "type": "string",
                        "description": "Unique material ID"
                    },
                    "materialName": {
                        "type": "string",
                        "description": "Display name for material"
                    },
                    "format": {
                        "type": "string",
                        "description": "File format",
                        "enum": ["markdown", "json"],
                        "default": "markdown"
                    }
                },
                "required": ["filePath", "materialId", "materialName"]
            }
        ),
        Tool(
            name="clone-material",
            description="Clone an existing material for customization",
            inputSchema={
                "type": "object",
                "properties": {
                    "sourceMaterialId": {
                        "type": "string",
                        "description": "Source material ID to clone"
                    },
                    "newMaterialId": {
                        "type": "string",
                        "description": "New material ID"
                    },
                    "newMaterialName": {
                        "type": "string",
                        "description": "Name for new material"
                    }
                },
                "required": ["sourceMaterialId", "newMaterialId", "newMaterialName"]
            }
        ),
        Tool(
            name="delete-material",
            description="Delete a material source and all associated data",
            inputSchema={
                "type": "object",
                "properties": {
                    "materialId": {
                        "type": "string",
                        "description": "Material ID to delete"
                    },
                    "confirm": {
                        "type": "boolean",
                        "description": "Confirmation flag (must be true)"
                    }
                },
                "required": ["materialId", "confirm"]
            }
        ),
        Tool(
            name="export-material",
            description="Export material to markdown file",
            inputSchema={
                "type": "object",
                "properties": {
                    "materialId": {
                        "type": "string",
                        "description": "Material ID (optional, uses active if not specified)"
                    },
                    "outputPath": {
                        "type": "string",
                        "description": "Path to save exported file"
                    }
                },
                "required": ["outputPath"]
            }
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Any) -> Sequence[TextContent]:
    """Handle tool calls."""
    try:
        # Get active material ID once
        active_material = db_manager.fetchone("SELECT id FROM materials WHERE is_active = TRUE LIMIT 1")
        active_material_id = active_material['id'] if active_material else None

        # Progress tracking tools
        if name == "get-statistics":
            if not active_material_id:
                return [TextContent(type="text", text="Error: No active material")]
            stats = progress_tracker.get_statistics(active_material_id)
            return [TextContent(type="text", text=json.dumps(stats, indent=2))]

        elif name == "update-progress":
            if not active_material_id:
                return [TextContent(type="text", text="Error: No active material")]
            question_id = arguments["questionId"]
            response = arguments["response"]
            notes = arguments.get("notes")

            success = progress_tracker.update_progress(
                active_material_id, question_id, response, None, notes
            )

            if success:
                return [TextContent(type="text", text=f"✓ Progress updated: {response}")]
            else:
                return [TextContent(type="text", text="✗ Failed to update progress")]

        elif name == "get-weak-areas":
            if not active_material_id:
                return [TextContent(type="text", text="Error: No active material")]
            weak_areas = progress_tracker.get_weak_areas(active_material_id)
            return [TextContent(type="text", text=json.dumps(weak_areas, indent=2))]

        elif name == "start-session":
            if not active_material_id:
                return [TextContent(type="text", text="Error: No active material")]
            session_id = progress_tracker.start_session(active_material_id)
            return [TextContent(type="text", text=f"✓ Session started: #{session_id}")]

        elif name == "end-session":
            session_id = arguments["sessionId"]
            success = progress_tracker.end_session(session_id)
            if success:
                return [TextContent(type="text", text=f"✓ Session #{session_id} ended")]
            else:
                return [TextContent(type="text", text="✗ Failed to end session")]

        # Question retrieval tools
        elif name == "get-sections":
            if not active_material_id:
                return [TextContent(type="text", text="Error: No active material")]
            sections = question_parser.get_sections(active_material_id)
            return [TextContent(type="text", text=json.dumps(sections, indent=2))]

        elif name == "get-subsections":
            if not active_material_id:
                return [TextContent(type="text", text="Error: No active material")]
            section = arguments["section"]
            subsections = question_parser.get_subsections(section, active_material_id)
            return [TextContent(type="text", text=json.dumps(subsections, indent=2))]

        elif name == "get-question":
            if not active_material_id:
                return [TextContent(type="text", text="Error: No active material")]
            section = arguments["section"]
            subsection = arguments["subsection"]
            question_number = arguments["questionNumber"]

            question = question_parser.get_question(
                section, subsection, question_number, active_material_id
            )

            if question:
                return [TextContent(type="text", text=json.dumps(question, indent=2))]
            else:
                return [TextContent(type="text", text=f"Question not found: {section}/{subsection} #{question_number}")]

        elif name == "get-next-question":
            if not active_material_id:
                return [TextContent(type="text", text="Error: No active material")]
            section = arguments["section"]
            subsection = arguments["subsection"]
            last_question = arguments.get("lastQuestionNumber", 0)

            question = question_parser.get_next_question(
                section, subsection, last_question, active_material_id
            )

            if question:
                return [TextContent(type="text", text=json.dumps(question, indent=2))]
            else:
                return [TextContent(type="text", text=f"No more questions in {section}/{subsection}")]

        elif name == "get-all-questions":
            if not active_material_id:
                return [TextContent(type="text", text="Error: No active material")]
            section = arguments["section"]
            subsection = arguments["subsection"]

            questions = question_parser.get_all_questions_in_subsection(
                section, subsection, active_material_id
            )
            return [TextContent(type="text", text=json.dumps(questions, indent=2))]

        elif name == "search-questions":
            if not active_material_id:
                return [TextContent(type="text", text="Error: No active material")]
            keyword = arguments["keyword"]
            results = question_parser.search_questions(keyword, active_material_id)

            if results:
                return [TextContent(type="text", text=json.dumps(results, indent=2))]
            else:
                return [TextContent(type="text", text=f"No questions found matching '{keyword}'")]

        elif name == "get-question-count":
            if not active_material_id:
                return [TextContent(type="text", text="Error: No active material")]
            section = arguments.get("section")
            subsection = arguments.get("subsection")

            count = question_parser.get_question_count(section, subsection, active_material_id)
            return [TextContent(type="text", text=f"{count} questions")]

        # Material editing tools
        elif name == "edit-question":
            if not active_material_id:
                return [TextContent(type="text", text="Error: No active material")]
            question_id = arguments["questionId"]
            new_question = arguments.get("newQuestion")
            new_answer = arguments.get("newAnswer")

            success = material_editor.edit_question(
                active_material_id, question_id, new_question, new_answer
            )

            if success:
                return [TextContent(type="text", text=f"✓ Question #{question_id} updated")]
            else:
                return [TextContent(type="text", text="✗ Failed to edit question")]

        elif name == "add-question":
            if not active_material_id:
                return [TextContent(type="text", text="Error: No active material")]
            section = arguments["section"]
            subsection = arguments["subsection"]
            question = arguments["question"]
            answer = arguments["answer"]
            position = arguments.get("position")

            question_id = material_editor.add_question(
                active_material_id, section, subsection, question, answer, position
            )

            if question_id:
                return [TextContent(type="text", text=f"✓ Question added: #{question_id} in {section}/{subsection}")]
            else:
                return [TextContent(type="text", text="✗ Failed to add question")]

        elif name == "delete-question":
            question_id = arguments["questionId"]
            success = material_editor.delete_question(question_id)

            if success:
                return [TextContent(type="text", text=f"✓ Question #{question_id} deleted")]
            else:
                return [TextContent(type="text", text="✗ Failed to delete question")]

        # Improvement tracking tools
        elif name == "log-improvement":
            if not active_material_id:
                return [TextContent(type="text", text="Error: No active material")]
            improvement_type = arguments["improvementType"]
            section = arguments["section"]
            subsection = arguments["subsection"]
            description = arguments["description"]
            question_id = arguments.get("questionId")
            priority = arguments.get("priority", "medium")

            imp_id = improvement_logger.log_improvement(
                active_material_id, improvement_type, section, subsection,
                description, question_id, priority, "user"
            )

            if imp_id:
                return [TextContent(type="text", text=f"✓ Improvement logged: #{imp_id}")]
            else:
                return [TextContent(type="text", text="✗ Failed to log improvement")]

        elif name == "get-improvements":
            material_id = active_material_id if active_material_id else None
            status = arguments["status"]
            section = arguments.get("section")
            priority = arguments.get("priority")

            if status == "pending":
                improvements = improvement_logger.get_pending_improvements(
                    material_id, section, priority
                )
            else:
                improvements = improvement_logger.get_implemented_improvements(
                    material_id, section
                )

            return [TextContent(type="text", text=json.dumps(improvements, indent=2))]

        elif name == "mark-improvement-implemented":
            improvement_id = arguments["improvementId"]
            notes = arguments.get("notes")

            success = improvement_logger.mark_implemented(improvement_id, notes)

            if success:
                return [TextContent(type="text", text=f"✓ Improvement #{improvement_id} marked as implemented")]
            else:
                return [TextContent(type="text", text="✗ Failed to mark improvement")]

        elif name == "get-improvement-metrics":
            material_id = active_material_id if active_material_id else None
            metrics = improvement_logger.get_metrics(material_id)
            return [TextContent(type="text", text=json.dumps(metrics, indent=2))]

        # Plugin/Material management tools
        elif name == "list-materials":
            include_inactive = arguments.get("includeInactive", False)

            query = "SELECT * FROM materials"
            if not include_inactive:
                query += " WHERE is_active = TRUE"
            query += " ORDER BY name"

            materials = db_manager.fetchall(query)

            # Add question counts
            for mat in materials:
                mat['question_count'] = db_manager.count_records(
                    "questions", "material_id = ?", (mat['id'],)
                )

            return [TextContent(type="text", text=json.dumps(materials, indent=2))]

        elif name == "get-material-info":
            material_id = arguments.get("materialId", active_material_id)
            if not material_id:
                return [TextContent(type="text", text="Error: No material specified or active")]

            info = material_editor.get_material_info(material_id)
            return [TextContent(type="text", text=json.dumps(info, indent=2))]

        elif name == "activate-material":
            material_id = arguments["materialId"]

            # Deactivate all
            db_manager.execute("UPDATE materials SET is_active = FALSE")

            # Activate specified
            result = db_manager.execute(
                "UPDATE materials SET is_active = TRUE WHERE id = ?",
                (material_id,)
            )

            if result.rowcount > 0:
                return [TextContent(type="text", text=f"✓ Activated material: {material_id}")]
            else:
                return [TextContent(type="text", text=f"✗ Material not found: {material_id}")]

        elif name == "import-material":
            from .plugins.importers import MarkdownImporter, JSONImporter

            file_path = Path(arguments["filePath"])
            material_id = arguments["materialId"]
            material_name = arguments["materialName"]
            format_type = arguments.get("format", "markdown")

            if not file_path.exists():
                return [TextContent(type="text", text=f"✗ File not found: {file_path}")]

            # Register material
            db_manager.execute(
                """INSERT INTO materials (id, name, description, version, source_type, is_active)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (material_id, material_name, f"Imported from {file_path.name}", "1.0.0", "user", False)
            )

            # Import questions
            if format_type == "markdown":
                importer = MarkdownImporter()
                count = importer.import_to_db(db_manager, material_id, file_path)
            else:
                importer = JSONImporter()
                count = importer.import_to_db(db_manager, material_id, file_path)

            return [TextContent(type="text", text=f"✓ Imported {count} questions as material: {material_id}")]

        elif name == "clone-material":
            source_id = arguments["sourceMaterialId"]
            new_id = arguments["newMaterialId"]
            new_name = arguments["newMaterialName"]

            success = material_editor.clone_material(source_id, new_id, new_name)

            if success:
                return [TextContent(type="text", text=f"✓ Cloned {source_id} to {new_id}")]
            else:
                return [TextContent(type="text", text="✗ Failed to clone material")]

        elif name == "delete-material":
            material_id = arguments["materialId"]
            confirm = arguments["confirm"]

            if not confirm:
                return [TextContent(type="text", text="✗ Deletion not confirmed (confirm must be true)")]

            # Check if it's the active material
            if material_id == active_material_id:
                return [TextContent(type="text", text="✗ Cannot delete active material. Activate another material first.")]

            # Delete (CASCADE will remove questions, progress, etc.)
            result = db_manager.execute("DELETE FROM materials WHERE id = ?", (material_id,))

            if result.rowcount > 0:
                return [TextContent(type="text", text=f"✓ Deleted material: {material_id}")]
            else:
                return [TextContent(type="text", text=f"✗ Material not found: {material_id}")]

        elif name == "export-material":
            material_id = arguments.get("materialId", active_material_id)
            output_path = Path(arguments["outputPath"])

            if not material_id:
                return [TextContent(type="text", text="Error: No material specified or active")]

            success = material_editor.export_material_to_markdown(material_id, output_path)

            if success:
                return [TextContent(type="text", text=f"✓ Exported to {output_path}")]
            else:
                return [TextContent(type="text", text="✗ Failed to export material")]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        logger.error(f"Error in tool {name}: {e}", exc_info=True)
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def async_main():
    """Run the MCP server (async)."""
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


def main():
    """Entry point for the MCP server (sync wrapper)."""
    import asyncio
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
