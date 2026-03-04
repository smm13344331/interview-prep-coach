"""MCP server for interview prep coach."""

import json
import logging
from typing import Any, Sequence

from mcp.server import Server
from mcp.types import Tool, TextContent

from .core import ProgressTracker, ImprovementLogger, QuestionParser, MaterialEditor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize server
server = Server("interview-prep-coach")

# Initialize components
progress_tracker = ProgressTracker()
improvement_logger = ImprovementLogger()
question_parser = QuestionParser()
material_editor = MaterialEditor()


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="get-progress",
            description="Load and return current learning progress",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="update-progress",
            description="Update progress after answering a question",
            inputSchema={
                "type": "object",
                "properties": {
                    "section": {
                        "type": "string",
                        "description": "Section name (e.g., 'Java Core Concepts')"
                    },
                    "subsection": {
                        "type": "string",
                        "description": "Subsection name"
                    },
                    "questionNumber": {
                        "type": "integer",
                        "description": "Question number answered"
                    },
                    "correct": {
                        "type": "boolean",
                        "description": "Whether the answer was correct"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Optional notes about the answer"
                    }
                },
                "required": ["section", "subsection", "questionNumber", "correct"]
            }
        ),
        Tool(
            name="get-next-question",
            description="Get the next question from interview material",
            inputSchema={
                "type": "object",
                "properties": {
                    "section": {
                        "type": "string",
                        "description": "Section name (optional, uses current if not specified)"
                    },
                    "subsection": {
                        "type": "string",
                        "description": "Subsection name (optional, uses current if not specified)"
                    },
                    "lastQuestionNumber": {
                        "type": "integer",
                        "description": "Last question number answered (0 for first question)",
                        "default": 0
                    }
                },
                "required": []
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
            name="log-improvement",
            description="Log an improvement to the interview material",
            inputSchema={
                "type": "object",
                "properties": {
                    "section": {
                        "type": "string",
                        "description": "Section name"
                    },
                    "subsection": {
                        "type": "string",
                        "description": "Subsection name (null for section-level)"
                    },
                    "improvementType": {
                        "type": "string",
                        "description": "Type: unclear_question, missing_topic, outdated_info, insufficient_coverage, answer_issue, difficulty_mismatch, missing_followup",
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
                    "description": {
                        "type": "string",
                        "description": "Detailed description of the improvement"
                    },
                    "questionNumber": {
                        "type": "integer",
                        "description": "Specific question number if applicable"
                    },
                    "priority": {
                        "type": "string",
                        "description": "Priority level",
                        "enum": ["low", "medium", "high", "critical"],
                        "default": "medium"
                    },
                    "suggestedBy": {
                        "type": "string",
                        "description": "Who suggested: user, system, coach",
                        "default": "user"
                    }
                },
                "required": ["section", "improvementType", "description"]
            }
        ),
        Tool(
            name="get-weak-areas",
            description="Get list of weak areas based on performance",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get-improvements",
            description="Get pending or implemented improvements",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "Filter by status: pending or implemented",
                        "enum": ["pending", "implemented"]
                    },
                    "section": {
                        "type": "string",
                        "description": "Filter by section name"
                    },
                    "priority": {
                        "type": "string",
                        "description": "Filter by priority for pending improvements"
                    }
                },
                "required": ["status"]
            }
        ),
        Tool(
            name="parse-questions",
            description="Parse and return all questions for a section or subsection",
            inputSchema={
                "type": "object",
                "properties": {
                    "section": {
                        "type": "string",
                        "description": "Section name"
                    },
                    "subsection": {
                        "type": "string",
                        "description": "Subsection name (optional)"
                    }
                },
                "required": ["section"]
            }
        ),
        Tool(
            name="get-statistics",
            description="Get overall progress statistics",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="search-questions",
            description="Search for questions containing a keyword",
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
            name="get-sections",
            description="Get list of all available sections",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get-subsections",
            description="Get list of subsections for a section",
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
            name="apply-improvement",
            description="Apply a logged improvement to the source material. This actually modifies the questions file based on the improvement description.",
            inputSchema={
                "type": "object",
                "properties": {
                    "improvementId": {
                        "type": "integer",
                        "description": "ID of the improvement to apply"
                    }
                },
                "required": ["improvementId"]
            }
        ),
        Tool(
            name="edit-question",
            description="Edit a specific question's text or answer directly",
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
                        "description": "Question number to edit (1-indexed)"
                    },
                    "newQuestion": {
                        "type": "string",
                        "description": "New question text (optional, null to keep existing)"
                    },
                    "newAnswer": {
                        "type": "string",
                        "description": "New answer text (optional, null to keep existing)"
                    }
                },
                "required": ["section", "subsection", "questionNumber"]
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
                        "description": "Position to insert (optional, null to append to end)"
                    }
                },
                "required": ["section", "subsection", "question", "answer"]
            }
        ),
        Tool(
            name="refresh-material",
            description="Refresh the questions parser after material edits. Call this after making changes.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get-material-info",
            description="Get information about the current material (source, size, last modified)",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="reset-material",
            description="Reset material to bundled version, discarding all user edits",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="export-material",
            description="Export current material to a file",
            inputSchema={
                "type": "object",
                "properties": {
                    "exportPath": {
                        "type": "string",
                        "description": "Path to export material to"
                    }
                },
                "required": ["exportPath"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Any) -> Sequence[TextContent]:
    """Handle tool calls."""
    try:
        if name == "get-progress":
            progress = progress_tracker.load_progress()
            return [TextContent(type="text", text=json.dumps(progress, indent=2))]

        elif name == "update-progress":
            section = arguments["section"]
            subsection = arguments["subsection"]
            question_number = arguments["questionNumber"]
            correct = arguments["correct"]
            notes = arguments.get("notes")

            progress = progress_tracker.update_progress(
                section, subsection, question_number, correct, notes
            )
            return [TextContent(
                type="text",
                text=f"Progress updated. Questions asked: {progress['overallProgress']['totalQuestionsAsked']}, "
                     f"Correct: {progress['overallProgress']['totalQuestionsCorrect']}, "
                     f"Accuracy: {progress['overallProgress']['accuracy']}"
            )]

        elif name == "get-next-question":
            # Get current position from progress if not specified
            if "section" in arguments and "subsection" in arguments:
                section = arguments["section"]
                subsection = arguments["subsection"]
                last_q = arguments.get("lastQuestionNumber", 0)
            else:
                section, subsection, next_q = progress_tracker.get_next_question_location()
                last_q = next_q - 1

            question = question_parser.get_next_question(section, subsection, last_q)

            if question:
                return [TextContent(type="text", text=json.dumps(question, indent=2))]
            else:
                return [TextContent(
                    type="text",
                    text=f"No more questions in {section} - {subsection}"
                )]

        elif name == "get-question":
            section = arguments["section"]
            subsection = arguments["subsection"]
            question_number = arguments["questionNumber"]

            question = question_parser.get_question(section, subsection, question_number)

            if question:
                return [TextContent(type="text", text=json.dumps(question, indent=2))]
            else:
                return [TextContent(
                    type="text",
                    text=f"Question not found: {section} - {subsection} #{question_number}"
                )]

        elif name == "log-improvement":
            section = arguments["section"]
            subsection = arguments.get("subsection")
            improvement_type = arguments["improvementType"]
            description = arguments["description"]
            question_number = arguments.get("questionNumber")
            priority = arguments.get("priority", "medium")
            suggested_by = arguments.get("suggestedBy", "user")

            improvement = improvement_logger.log_improvement(
                section, subsection, improvement_type, description,
                question_number, priority, suggested_by
            )

            return [TextContent(
                type="text",
                text=f"Improvement #{improvement['id']} logged: {improvement_type} - {description[:100]}"
            )]

        elif name == "get-weak-areas":
            weak_areas = progress_tracker.get_weak_areas()
            return [TextContent(type="text", text=json.dumps(weak_areas, indent=2))]

        elif name == "get-improvements":
            status = arguments["status"]
            section = arguments.get("section")
            priority = arguments.get("priority")

            if status == "pending":
                improvements = improvement_logger.get_pending_improvements(section, priority)
            else:
                improvements = improvement_logger.get_implemented_improvements(section)

            return [TextContent(type="text", text=json.dumps(improvements, indent=2))]

        elif name == "parse-questions":
            section = arguments["section"]
            subsection = arguments.get("subsection")

            if subsection:
                questions = question_parser.get_all_questions_in_subsection(section, subsection)
            else:
                # Get all questions in section across all subsections
                subsections = question_parser.get_subsections(section)
                questions = []
                for sub in subsections:
                    questions.extend(
                        question_parser.get_all_questions_in_subsection(section, sub)
                    )

            return [TextContent(type="text", text=json.dumps(questions, indent=2))]

        elif name == "get-statistics":
            stats = progress_tracker.get_statistics()
            return [TextContent(type="text", text=json.dumps(stats, indent=2))]

        elif name == "search-questions":
            keyword = arguments["keyword"]
            results = question_parser.search_questions(keyword)
            return [TextContent(
                type="text",
                text=json.dumps(results, indent=2) if results else f"No questions found matching '{keyword}'"
            )]

        elif name == "get-sections":
            sections = question_parser.get_sections()
            return [TextContent(type="text", text=json.dumps(sections, indent=2))]

        elif name == "get-subsections":
            section = arguments["section"]
            subsections = question_parser.get_subsections(section)
            return [TextContent(type="text", text=json.dumps(subsections, indent=2))]

        elif name == "apply-improvement":
            improvement_id = arguments["improvementId"]

            # Get the improvement
            improvements = improvement_logger.load_improvements()
            improvement = None
            for imp in improvements['pendingImprovements']:
                if imp['id'] == improvement_id:
                    improvement = imp
                    break

            if not improvement:
                return [TextContent(type="text", text=f"Improvement #{improvement_id} not found in pending list")]

            # Apply the improvement
            success, message = material_editor.apply_improvement(improvement)

            if success:
                # Mark as implemented
                improvement_logger.mark_implemented(improvement_id, message)
                # Refresh parser
                global question_parser
                question_parser = QuestionParser()
                return [TextContent(type="text", text=f"✓ Applied improvement #{improvement_id}: {message}")]
            else:
                return [TextContent(type="text", text=f"✗ Failed to apply improvement #{improvement_id}: {message}")]

        elif name == "edit-question":
            section = arguments["section"]
            subsection = arguments["subsection"]
            question_number = arguments["questionNumber"]
            new_question = arguments.get("newQuestion")
            new_answer = arguments.get("newAnswer")

            success = material_editor.edit_question(
                section, subsection, question_number,
                new_question, new_answer
            )

            if success:
                # Refresh parser
                global question_parser
                question_parser = QuestionParser()
                return [TextContent(
                    type="text",
                    text=f"✓ Edited question #{question_number} in {section} - {subsection}"
                )]
            else:
                return [TextContent(type="text", text=f"✗ Question not found")]

        elif name == "add-question":
            section = arguments["section"]
            subsection = arguments["subsection"]
            question = arguments["question"]
            answer = arguments["answer"]
            position = arguments.get("position")

            success = material_editor.add_question(
                section, subsection, question, answer, position
            )

            if success:
                # Refresh parser
                global question_parser
                question_parser = QuestionParser()
                return [TextContent(
                    type="text",
                    text=f"✓ Added new question to {section} - {subsection}"
                )]
            else:
                return [TextContent(type="text", text=f"✗ Section/subsection not found")]

        elif name == "refresh-material":
            # Force reload of questions
            global question_parser
            question_parser = QuestionParser()
            return [TextContent(type="text", text="✓ Material refreshed")]

        elif name == "get-material-info":
            info = material_editor.get_material_info()
            return [TextContent(type="text", text=json.dumps(info, indent=2))]

        elif name == "reset-material":
            success = material_editor.reset_to_bundled()
            if success:
                # Refresh parser
                global question_parser
                question_parser = QuestionParser()
                return [TextContent(type="text", text="✓ Material reset to bundled version")]
            else:
                return [TextContent(type="text", text="✗ Failed to reset material")]

        elif name == "export-material":
            export_path = arguments["exportPath"]
            from pathlib import Path
            success = material_editor.export_material(Path(export_path))
            if success:
                return [TextContent(type="text", text=f"✓ Material exported to {export_path}")]
            else:
                return [TextContent(type="text", text=f"✗ Failed to export material")]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        logger.error(f"Error in tool {name}: {e}", exc_info=True)
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Run the MCP server."""
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
