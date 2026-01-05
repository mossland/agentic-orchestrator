"""
Trend analysis storage.

Stores trend analysis results as Markdown files with YAML frontmatter.
Maintains trend history and tracks idea-trend relationships.
"""

import json
import re
import shutil
from datetime import datetime, timedelta
from pathlib import Path

import yaml

from ..utils.config import Config, load_config
from ..utils.files import ensure_dir
from ..utils.logging import get_logger
from .models import Trend, TrendAnalysis, TrendIdeaLink

logger = get_logger(__name__)


class TrendStorage:
    """
    Stores and retrieves trend analysis data.

    Uses Markdown files with YAML frontmatter for human-readable storage.
    Directory structure: data/trends/YYYY/MM/YYYY-MM-DD.md
    """

    # Index file for tracking idea-trend links
    INDEX_FILE = "idea_links.json"

    def __init__(
        self,
        base_path: Path | None = None,
        config: Config | None = None,
    ):
        """
        Initialize trend storage.

        Args:
            base_path: Base path for the project. Uses cwd if not provided.
            config: Configuration object.
        """
        self.config = config or load_config()
        storage_dir = self.config.get("trends", "storage", "directory", default="data/trends")
        self.base_path = (base_path or Path.cwd()) / storage_dir
        ensure_dir(self.base_path)

    def _get_file_path(self, date: datetime) -> Path:
        """
        Get the file path for a given date.

        Args:
            date: Date for the analysis.

        Returns:
            Path to the Markdown file.
        """
        year = str(date.year)
        month = f"{date.month:02d}"
        filename = f"{date.strftime('%Y-%m-%d')}.md"
        return self.base_path / year / month / filename

    def save_analysis(
        self,
        analyses: dict[str, TrendAnalysis],
        date: datetime | None = None,
    ) -> Path | None:
        """
        Save trend analysis to Markdown file.

        Skips saving if analysis is empty or existing file has more trends.

        Args:
            analyses: Dictionary mapping period to TrendAnalysis.
            date: Date for the file. Uses current date if not provided.

        Returns:
            Path to the saved file, or None if save was skipped.
        """
        date = date or datetime.utcnow()
        file_path = self._get_file_path(date)
        ensure_dir(file_path.parent)

        total_trends = sum(len(a.trends) for a in analyses.values())
        if total_trends == 0:
            logger.warning(f"Skipping save: no trends in analysis for {date.strftime('%Y-%m-%d')}")
            return None

        if file_path.exists():
            existing = self.load_analysis(date)
            if existing:
                existing_trends = sum(len(a.trends) for a in existing.values())
                if existing_trends > total_trends:
                    logger.warning(
                        f"Skipping save: existing file has {existing_trends} trends, "
                        f"new analysis has only {total_trends}"
                    )
                    return file_path

        # Collect metadata from all analyses
        all_sources = set()
        all_categories = set()
        total_articles = 0
        periods_analyzed = []

        for period, analysis in analyses.items():
            all_sources.update(analysis.sources_analyzed)
            all_categories.update(analysis.categories_analyzed)
            total_articles += analysis.raw_article_count
            periods_analyzed.append(period)

        # Build frontmatter
        frontmatter = {
            "date": date.strftime("%Y-%m-%d"),
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "periods": periods_analyzed,
            "total_articles": total_articles,
            "sources": sorted(all_sources),
            "categories": sorted(all_categories),
        }

        # Build content
        content_parts = [
            "---",
            yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True).strip(),
            "---",
            "",
            f"# Trend Analysis - {date.strftime('%Y-%m-%d')}",
            "",
        ]

        # Add each period's trends
        period_labels = {
            "24h": "24-Hour Trends",
            "1w": "Weekly Trends",
            "1m": "Monthly Trends",
        }

        for period in ["24h", "1w", "1m"]:
            if period not in analyses:
                continue

            analysis = analyses[period]
            label = period_labels.get(period, period)

            content_parts.append(f"## {label}")
            content_parts.append("")

            if not analysis.trends:
                content_parts.append("*No significant trends identified.*")
                content_parts.append("")
                continue

            for i, trend in enumerate(analysis.trends[:10], 1):
                content_parts.append(f"### {i}. {trend.topic} (Score: {trend.score:.1f})")
                content_parts.append("")
                content_parts.append(f"- **Category:** {trend.category}")
                content_parts.append(f"- **Articles:** {trend.article_count}")
                content_parts.append(f"- **Keywords:** {', '.join(trend.keywords[:5])}")
                content_parts.append(f"- **Sources:** {', '.join(trend.sources[:5])}")
                content_parts.append("")
                content_parts.append(f"**Summary:** {trend.summary}")
                content_parts.append("")

                if trend.web3_relevance:
                    content_parts.append(f"**Web3 Relevance:** {trend.web3_relevance}")
                    content_parts.append("")

                if trend.sample_headlines:
                    content_parts.append("**Sample Headlines:**")
                    for headline in trend.sample_headlines[:3]:
                        content_parts.append(f"- {headline}")
                    content_parts.append("")

                if trend.idea_seeds:
                    content_parts.append("**Idea Seeds:**")
                    for idea in trend.idea_seeds[:3]:
                        content_parts.append(f"- {idea}")
                    content_parts.append("")

        # Add footer
        content_parts.append("---")
        content_parts.append("")
        content_parts.append(
            f"*Generated by Agentic Orchestrator at "
            f"{datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC*"
        )

        # Write file
        content = "\n".join(content_parts)
        file_path.write_text(content, encoding="utf-8")

        logger.info(f"Saved trend analysis to {file_path}")
        return file_path

    def load_analysis(
        self,
        date: datetime,
    ) -> dict[str, TrendAnalysis] | None:
        """
        Load trend analysis for a specific date.

        Args:
            date: Date of the analysis.

        Returns:
            Dictionary mapping period to TrendAnalysis, or None if not found.
        """
        file_path = self._get_file_path(date)

        if not file_path.exists():
            logger.debug(f"No analysis found for {date.strftime('%Y-%m-%d')}")
            return None

        try:
            content = file_path.read_text(encoding="utf-8")
            return self._parse_analysis_file(content, date)
        except Exception as e:
            logger.error(f"Failed to load analysis from {file_path}: {e}")
            return None

    def _parse_analysis_file(
        self,
        content: str,
        date: datetime,
    ) -> dict[str, TrendAnalysis]:
        """
        Parse a trend analysis Markdown file.

        Args:
            content: File content.
            date: Date of the analysis.

        Returns:
            Dictionary mapping period to TrendAnalysis.
        """
        analyses: dict[str, TrendAnalysis] = {}

        # Parse frontmatter
        frontmatter_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        if not frontmatter_match:
            return analyses

        try:
            frontmatter = yaml.safe_load(frontmatter_match.group(1))
        except yaml.YAMLError:
            frontmatter = {}

        sources = frontmatter.get("sources", [])
        categories = frontmatter.get("categories", [])
        total_articles = frontmatter.get("total_articles", 0)

        # Parse each period section
        period_patterns = {
            "24h": r"## 24-Hour Trends\n(.*?)(?=## |$)",
            "1w": r"## Weekly Trends\n(.*?)(?=## |$)",
            "1m": r"## Monthly Trends\n(.*?)(?=## |$)",
        }

        for period, pattern in period_patterns.items():
            match = re.search(pattern, content, re.DOTALL)
            if not match:
                continue

            section = match.group(1)
            trends = self._parse_trends_section(section, period)

            analyses[period] = TrendAnalysis(
                date=date,
                period=period,
                trends=trends,
                raw_article_count=total_articles // len(period_patterns),
                sources_analyzed=sources,
                categories_analyzed=categories,
            )

        return analyses

    def _parse_trends_section(
        self,
        section: str,
        period: str,
    ) -> list[Trend]:
        """
        Parse trends from a period section.

        Args:
            section: Markdown content for one period.
            period: Time period.

        Returns:
            List of Trend objects.
        """
        trends = []

        # Find trend blocks
        trend_pattern = r"### \d+\. (.*?) \(Score: ([\d.]+)\)\n(.*?)(?=### \d+\. |$)"
        matches = re.findall(trend_pattern, section, re.DOTALL)

        for topic, score, details in matches:
            trend = Trend(
                topic=topic.strip(),
                keywords=self._extract_field(details, "Keywords"),
                score=float(score),
                time_period=period,
                sources=self._extract_field(details, "Sources"),
                article_count=self._extract_int(details, "Articles"),
                sample_headlines=[],
                category=self._extract_single(details, "Category") or "general",
                summary=self._extract_single(details, "Summary") or "",
            )
            trends.append(trend)

        return trends

    def _extract_field(self, text: str, field: str) -> list[str]:
        """Extract a comma-separated field value."""
        match = re.search(rf"\*\*{field}:\*\* (.*?)(?:\n|$)", text)
        if match:
            return [x.strip() for x in match.group(1).split(",")]
        return []

    def _extract_single(self, text: str, field: str) -> str | None:
        """Extract a single field value."""
        match = re.search(rf"\*\*{field}:\*\* (.*?)(?:\n|$)", text)
        return match.group(1).strip() if match else None

    def _extract_int(self, text: str, field: str) -> int:
        """Extract an integer field value."""
        match = re.search(rf"\*\*{field}:\*\* (\d+)", text)
        return int(match.group(1)) if match else 0

    def get_recent_analyses(
        self,
        days: int = 7,
    ) -> list[dict[str, TrendAnalysis]]:
        """
        Get trend analyses from recent days.

        Args:
            days: Number of days to look back.

        Returns:
            List of analysis dictionaries, newest first.
        """
        analyses = []
        today = datetime.utcnow()

        for i in range(days):
            date = today - timedelta(days=i)
            analysis = self.load_analysis(date)
            if analysis:
                analyses.append(analysis)

        return analyses

    def link_idea_to_trend(
        self,
        link: TrendIdeaLink,
    ) -> None:
        """
        Record which trend led to which idea.

        Args:
            link: TrendIdeaLink object to save.
        """
        index_path = self.base_path / self.INDEX_FILE

        # Load existing links
        links = []
        if index_path.exists():
            try:
                links = json.loads(index_path.read_text())
            except (OSError, json.JSONDecodeError):
                links = []

        # Add new link
        links.append(link.to_dict())

        # Save
        index_path.write_text(json.dumps(links, indent=2))
        logger.debug(f"Linked idea #{link.idea_issue_number} to trend '{link.trend_topic}'")

    def get_ideas_for_trend(
        self,
        topic: str,
    ) -> list[int]:
        """
        Get idea issue numbers generated from a specific trend.

        Args:
            topic: Trend topic to search for.

        Returns:
            List of GitHub issue numbers.
        """
        index_path = self.base_path / self.INDEX_FILE

        if not index_path.exists():
            return []

        try:
            links = json.loads(index_path.read_text())
            return [link["idea_issue_number"] for link in links if link.get("trend_topic") == topic]
        except (OSError, json.JSONDecodeError):
            return []

    def get_all_idea_links(self) -> list[TrendIdeaLink]:
        """
        Get all idea-trend links.

        Returns:
            List of TrendIdeaLink objects.
        """
        index_path = self.base_path / self.INDEX_FILE

        if not index_path.exists():
            return []

        try:
            links_data = json.loads(index_path.read_text())
            return [TrendIdeaLink.from_dict(data) for data in links_data]
        except (OSError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load idea links: {e}")
            return []

    def cleanup_old_data(
        self,
        retention_days: int | None = None,
    ) -> int:
        """
        Remove trend data older than retention period.

        Args:
            retention_days: Days to retain. Uses config if not provided.

        Returns:
            Number of files deleted.
        """
        days_to_retain: int = (
            retention_days
            if retention_days is not None
            else (self.config.get("trends", "storage", "retention_days", default=90) or 90)
        )
        cutoff = datetime.utcnow() - timedelta(days=days_to_retain)
        deleted = 0

        # Iterate through year directories
        for year_dir in self.base_path.iterdir():
            if not year_dir.is_dir() or not year_dir.name.isdigit():
                continue

            year = int(year_dir.name)
            if year < cutoff.year - 1:  # Keep at least current and previous year
                shutil.rmtree(year_dir)
                logger.info(f"Deleted old trend data directory: {year_dir}")
                continue

            # Check month directories
            for month_dir in year_dir.iterdir():
                if not month_dir.is_dir():
                    continue

                for file_path in month_dir.glob("*.md"):
                    try:
                        # Parse date from filename
                        date_str = file_path.stem  # YYYY-MM-DD
                        file_date = datetime.strptime(date_str, "%Y-%m-%d")

                        if file_date < cutoff:
                            file_path.unlink()
                            deleted += 1
                            logger.debug(f"Deleted old trend file: {file_path}")
                    except ValueError:
                        continue

        if deleted > 0:
            logger.info(f"Cleaned up {deleted} old trend files")

        return deleted
