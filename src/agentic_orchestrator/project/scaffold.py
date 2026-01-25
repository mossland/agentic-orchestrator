"""
Project scaffold orchestrator.

Orchestrates the complete project generation pipeline:
1. Load Plan from database
2. Parse Plan content
3. Detect tech stack
4. Generate template files
5. Generate LLM-enhanced code
6. Create project directory structure
7. Update project status in database
8. Auto-commit and push to GitHub
"""

import json
import logging
import asyncio
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

from .parser import PlanParser, ParsedPlan
from .templates import TemplateManager, TemplateFile
from .generator import ProjectCodeGenerator, GeneratedFile

logger = logging.getLogger(__name__)


@dataclass
class ProjectGenerationResult:
    """Result of project generation."""
    success: bool
    project_id: Optional[str] = None
    project_path: Optional[str] = None
    plan_id: str = ""
    tech_stack: Dict[str, Any] = field(default_factory=dict)
    files_generated: int = 0
    error: Optional[str] = None
    duration_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "project_id": self.project_id,
            "project_path": self.project_path,
            "plan_id": self.plan_id,
            "tech_stack": self.tech_stack,
            "files_generated": self.files_generated,
            "error": self.error,
            "duration_seconds": self.duration_seconds,
        }


class ProjectScaffold:
    """
    Orchestrates project generation from Plans.

    Usage:
        scaffold = ProjectScaffold(router=llm_router)
        result = await scaffold.generate_project(plan_id="abc123")

        if result.success:
            print(f"Project created at: {result.project_path}")
    """

    def __init__(
        self,
        router=None,
        projects_dir: str = "projects",
        db_session=None,
    ):
        """
        Initialize the scaffold.

        Args:
            router: HybridLLMRouter for LLM-based generation
            projects_dir: Base directory for generated projects
            db_session: SQLAlchemy session (optional)
        """
        self.router = router
        self.projects_dir = Path(projects_dir)
        self.db_session = db_session

        self.parser = PlanParser(router=router)
        self.templates = TemplateManager(projects_dir=projects_dir)
        self.generator = ProjectCodeGenerator(router=router)

        # Ensure projects directory exists
        self.projects_dir.mkdir(parents=True, exist_ok=True)

    async def generate_project(
        self,
        plan_id: str,
        force_regenerate: bool = False,
    ) -> ProjectGenerationResult:
        """
        Generate a project from a Plan.

        Args:
            plan_id: ID of the Plan to generate from
            force_regenerate: If True, regenerate even if project exists

        Returns:
            ProjectGenerationResult with status and details
        """
        start_time = datetime.utcnow()

        try:
            # Load plan from database
            plan = await self._load_plan(plan_id)
            if not plan:
                return ProjectGenerationResult(
                    success=False,
                    plan_id=plan_id,
                    error=f"Plan not found: {plan_id}",
                )

            # Check if project already exists
            existing_project = await self._get_existing_project(plan_id)
            if existing_project and not force_regenerate:
                return ProjectGenerationResult(
                    success=True,
                    project_id=existing_project.get("id"),
                    project_path=existing_project.get("directory_path"),
                    plan_id=plan_id,
                    tech_stack=existing_project.get("tech_stack", {}),
                    error="Project already exists. Use force_regenerate=True to regenerate.",
                )

            # Parse plan content with deep extraction
            logger.info(f"Parsing plan: {plan_id}")
            plan_content = plan.get("final_plan") or plan.get("prd_content") or ""
            plan_title = plan.get("title") or "Untitled Project"

            if self.router:
                # Use deep parsing for comprehensive extraction
                logger.info("Using deep LLM parsing for high-quality code generation")
                parsed_plan = await self.parser.parse_deep_with_llm(plan_content, plan_title)
            else:
                parsed_plan = self.parser.parse(plan_content, plan_title)

            logger.info(f"Parsed: {len(parsed_plan.entities)} entities, "
                       f"{len(parsed_plan.api_endpoints)} endpoints, "
                       f"{len(parsed_plan.ui_components)} UI components")

            # Generate project name
            project_name = self._generate_project_name(parsed_plan.title)
            logger.info(f"Generating project: {project_name}")

            # Create project in database (status: generating)
            project_id = await self._create_project_record(
                plan_id=plan_id,
                name=project_name,
                tech_stack=parsed_plan.tech_stack.to_dict(),
                status="generating",
            )

            # Generate full production-quality project code
            logger.info("Generating production-quality project code...")
            logger.info(f"Tech stack: {parsed_plan.tech_stack.to_dict()}")

            if self.router:
                # Use full project generation for high-quality code
                generated_files = await self.generator.generate_full_project(
                    parsed_plan, project_name
                )
                all_files = [
                    TemplateFile(path=f.path, content=f.content)
                    for f in generated_files
                ]
                logger.info(f"Generated {len(all_files)} production-quality files")
            else:
                # Fallback: Use template files + basic LLM generation
                template_files = self.templates.get_template_files(
                    frontend=parsed_plan.tech_stack.frontend,
                    backend=parsed_plan.tech_stack.backend,
                    database=parsed_plan.tech_stack.database,
                    blockchain=parsed_plan.tech_stack.blockchain,
                )
                llm_files = await self._generate_llm_files(parsed_plan, project_name)
                all_files = template_files + [
                    TemplateFile(path=f.path, content=f.content)
                    for f in llm_files
                ]
                logger.info(f"Generated {len(all_files)} files (fallback mode)")

            # Add PLAN.md (copy of original plan)
            all_files.append(TemplateFile(
                path="PLAN.md",
                content=plan_content or "# Plan\n\nOriginal plan content not available.",
            ))

            # Add .moss-project.json with metadata
            all_files.append(TemplateFile(
                path=".moss-project.json",
                content=json.dumps({
                    "version": "1.0.0",
                    "generator": "moss-ao",
                    "createdAt": datetime.utcnow().isoformat(),
                    "planId": plan_id,
                    "projectId": project_id,
                    "techStack": parsed_plan.tech_stack.to_dict(),
                    "features": parsed_plan.features[:10],
                }, indent=2),
            ))

            # Create project directory and files
            project_path = self.templates.create_project_structure(
                project_name=project_name,
                files=all_files,
            )

            logger.info(f"Project created at: {project_path}")

            # Update project status in database
            await self._update_project_status(
                project_id=project_id,
                status="ready",
                directory_path=str(project_path),
            )

            # Auto-commit and push to GitHub
            git_success = await self._git_commit_and_push(str(project_path), project_name)
            if git_success:
                logger.info(f"Project auto-pushed to GitHub: {project_name}")
            else:
                logger.warning(f"Git push failed for project: {project_name} (project still created locally)")

            duration = (datetime.utcnow() - start_time).total_seconds()

            return ProjectGenerationResult(
                success=True,
                project_id=project_id,
                project_path=str(project_path),
                plan_id=plan_id,
                tech_stack=parsed_plan.tech_stack.to_dict(),
                files_generated=len(all_files),
                duration_seconds=duration,
            )

        except Exception as e:
            logger.error(f"Project generation failed: {e}", exc_info=True)
            duration = (datetime.utcnow() - start_time).total_seconds()

            # Update project status to error if we created a record
            if 'project_id' in locals():
                await self._update_project_status(
                    project_id=project_id,
                    status="error",
                )

            return ProjectGenerationResult(
                success=False,
                plan_id=plan_id,
                error=str(e),
                duration_seconds=duration,
            )

    async def _load_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Load plan from database."""
        if not self.db_session:
            logger.warning("No database session, cannot load plan")
            return None

        try:
            from ..db.models import Plan
            plan = self.db_session.query(Plan).filter(Plan.id == plan_id).first()
            if plan:
                return {
                    "id": plan.id,
                    "title": plan.title,
                    "final_plan": plan.final_plan,
                    "prd_content": plan.prd_content,
                    "architecture_content": plan.architecture_content,
                    "status": plan.status,
                }
            return None
        except Exception as e:
            logger.error(f"Failed to load plan: {e}")
            return None

    async def _get_existing_project(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Check if a project already exists for this plan."""
        if not self.db_session:
            return None

        try:
            from ..db.models import Project
            project = self.db_session.query(Project).filter(
                Project.plan_id == plan_id
            ).first()
            if project:
                return {
                    "id": project.id,
                    "directory_path": project.directory_path,
                    "tech_stack": project.tech_stack,
                    "status": project.status,
                }
            return None
        except Exception as e:
            logger.debug(f"No existing project found: {e}")
            return None

    async def _create_project_record(
        self,
        plan_id: str,
        name: str,
        tech_stack: Dict[str, Any],
        status: str = "generating",
    ) -> str:
        """Create project record in database."""
        import uuid
        project_id = str(uuid.uuid4())[:8]

        if not self.db_session:
            return project_id

        try:
            from ..db.models import Project
            project = Project(
                id=project_id,
                plan_id=plan_id,
                name=name,
                tech_stack=tech_stack,
                status=status,
            )
            self.db_session.add(project)
            self.db_session.flush()
            return project_id
        except Exception as e:
            logger.error(f"Failed to create project record: {e}")
            return project_id

    async def _update_project_status(
        self,
        project_id: str,
        status: str,
        directory_path: Optional[str] = None,
    ):
        """Update project status in database."""
        if not self.db_session:
            return

        try:
            from ..db.models import Project
            project = self.db_session.query(Project).filter(
                Project.id == project_id
            ).first()
            if project:
                project.status = status
                if directory_path:
                    project.directory_path = directory_path
                if status == "ready":
                    project.completed_at = datetime.utcnow()
                self.db_session.flush()
        except Exception as e:
            logger.error(f"Failed to update project status: {e}")

    async def _generate_llm_files(
        self,
        parsed_plan: ParsedPlan,
        project_name: str,
    ) -> List[GeneratedFile]:
        """Generate LLM-enhanced files."""
        files = []

        # Generate README.md
        logger.info("Generating README.md...")
        readme = await self.generator.generate_readme(parsed_plan, project_name)
        files.append(GeneratedFile(
            path="README.md",
            content=readme,
            description="Project README",
        ))

        # Generate architecture documentation
        logger.info("Generating architecture documentation...")
        architecture = await self.generator.generate_architecture_doc(
            parsed_plan, project_name
        )
        files.append(GeneratedFile(
            path="docs/ARCHITECTURE.md",
            content=architecture,
            description="Architecture documentation",
        ))

        # Generate API routes if endpoints are defined
        if parsed_plan.api_endpoints:
            logger.info("Generating API routes...")
            route_files = await self.generator.generate_api_routes(parsed_plan)
            files.extend(route_files)

        # Generate data models if backend is defined
        if parsed_plan.tech_stack.backend:
            logger.info("Generating data models...")
            model_files = await self.generator.generate_data_models(parsed_plan)
            files.extend(model_files)

        return files

    def _generate_project_name(self, title: str) -> str:
        """Generate a safe project directory name from title."""
        # Remove special characters and convert to lowercase
        safe_name = "".join(
            c if c.isalnum() or c in "-_ " else ""
            for c in title
        ).strip()

        # Replace spaces with hyphens
        safe_name = "-".join(safe_name.split())

        # Ensure it's not too long
        if len(safe_name) > 50:
            safe_name = safe_name[:50].rsplit("-", 1)[0]

        return safe_name.lower() or "project"

    async def _git_commit_and_push(self, project_path: str, project_name: str) -> bool:
        """
        Commit and push the generated project to GitHub.

        Args:
            project_path: Full path to the project directory
            project_name: Name of the project

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get the repository root (parent of projects/ directory)
            repo_root = Path(project_path).parent.parent

            # Stage the project directory
            add_result = subprocess.run(
                ["git", "add", f"projects/{project_name}/"],
                cwd=repo_root,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if add_result.returncode != 0:
                logger.error(f"Git add failed: {add_result.stderr}")
                return False

            # Create commit message
            commit_message = f"feat: generate production-quality code for {project_name}"

            # Commit the changes
            commit_result = subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=repo_root,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if commit_result.returncode != 0:
                # Check if there's nothing to commit
                if "nothing to commit" in commit_result.stdout.lower():
                    logger.info("No changes to commit (project already committed)")
                    return True
                logger.error(f"Git commit failed: {commit_result.stderr}")
                return False

            logger.info(f"Committed project: {project_name}")

            # Push to remote
            push_result = subprocess.run(
                ["git", "push", "origin", "main"],
                cwd=repo_root,
                capture_output=True,
                text=True,
                timeout=60,
            )
            if push_result.returncode != 0:
                logger.error(f"Git push failed: {push_result.stderr}")
                return False

            logger.info(f"Pushed project to GitHub: {project_name}")
            return True

        except subprocess.TimeoutExpired:
            logger.error("Git operation timed out")
            return False
        except Exception as e:
            logger.error(f"Git commit/push failed: {e}")
            return False


async def generate_project_from_plan(
    plan_id: str,
    router=None,
    db_session=None,
    force_regenerate: bool = False,
) -> ProjectGenerationResult:
    """
    Convenience function to generate a project from a plan.

    Args:
        plan_id: ID of the Plan
        router: HybridLLMRouter (optional)
        db_session: SQLAlchemy session (optional)
        force_regenerate: Force regeneration if project exists

    Returns:
        ProjectGenerationResult
    """
    scaffold = ProjectScaffold(
        router=router,
        db_session=db_session,
    )
    return await scaffold.generate_project(
        plan_id=plan_id,
        force_regenerate=force_regenerate,
    )
