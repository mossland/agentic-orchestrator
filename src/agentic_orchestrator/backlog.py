"""
Backlog-based workflow handlers.

Implements the new workflow where:
- Ideas are generated and stored as GitHub Issues
- Humans promote ideas to plans via labels
- Humans promote plans to development via labels
- Orchestrator polls for promotions and processes them
"""

import re
from datetime import datetime
from pathlib import Path

from .debate import DebateResult, create_debate_session
from .github_client import GitHubClient, GitHubIssue, GitHubRateLimitError, Labels
from .providers.base import BaseProvider, QuotaExhaustedError
from .providers.claude import ClaudeProvider, create_claude_provider
from .providers.gemini import GeminiProvider, create_gemini_provider
from .providers.openai import OpenAIProvider, create_openai_provider
from .trends import FeedFetcher, Trend, TrendAnalysis, TrendAnalyzer, TrendIdeaLink, TrendStorage
from .utils.config import get_env_bool, load_config
from .utils.files import (
    create_alert_file,
    ensure_dir,
    generate_project_id,
    get_project_dir,
    write_markdown,
)
from .utils.git import GitHelper
from .utils.logging import get_logger

logger = get_logger(__name__)


class IdeaGenerator:
    """
    Generates new idea issues for the backlog.

    Creates GitHub Issues with structured idea content
    following Mossland ecosystem focus.
    """

    def __init__(
        self,
        github: GitHubClient,
        claude: ClaudeProvider | None = None,
        dry_run: bool = False,
    ):
        self.github = github
        self._claude = claude
        self.dry_run = dry_run

    @property
    def claude(self) -> ClaudeProvider:
        if self._claude is None:
            self._claude = create_claude_provider(dry_run=self.dry_run)
        return self._claude

    def generate_ideas(self, count: int = 1) -> list[GitHubIssue]:
        """
        Generate new idea issues.

        Args:
            count: Number of ideas to generate.

        Returns:
            List of created GitHubIssue objects.
        """
        created = []

        for i in range(count):
            try:
                logger.info(f"Generating idea {i + 1}/{count}")

                # Generate idea content
                idea = self._generate_idea_content()

                if self.dry_run:
                    logger.info(f"[DRY RUN] Would create idea: {idea['title']}")
                    continue

                # Create GitHub Issue
                issue = self.github.create_issue(
                    title=f"[IDEA] {idea['title']}",
                    body=idea["body"],
                    labels=[
                        Labels.TYPE_IDEA,
                        Labels.STATUS_BACKLOG,
                        Labels.GENERATED_BY_ORCHESTRATOR,
                    ],
                )

                created.append(issue)
                logger.info(f"Created idea issue #{issue.number}: {idea['title']}")

            except Exception as e:
                logger.error(f"Failed to generate idea {i + 1}: {e}")
                continue

        return created

    def _generate_idea_content(self) -> dict:
        """Generate structured idea content using Claude."""
        prompt = self._get_idea_prompt()

        response = self.claude.chat(
            user_message=prompt,
            system_message=self._get_system_message(),
        )

        # Parse response
        return self._parse_idea_response(response)

    def _get_system_message(self) -> str:
        return """You are a creative Web3 product strategist for the Mossland ecosystem.

Mossland is a blockchain-based metaverse project with:
- MOC Token (Mossland Coin) - the native cryptocurrency
- Real-world location integration with virtual spaces
- NFT-based digital assets
- AR/VR experiences

Generate SMALL, FOCUSED micro-service ideas that:
1. Can be built as an MVP in 1-2 weeks
2. Provide clear value to MOC holders or the ecosystem
3. Are technically feasible with Web3 technologies
4. Have measurable success criteria

Avoid:
- Large platform/mainnet development
- Overly complex infrastructure
- Ideas requiring massive user adoption to work

Good examples:
- Token utility tools
- Community engagement helpers
- Governance participation tools
- Content verification systems
- Badge/achievement systems
- Simple bridges or integrations
- Analytics dashboards
- Reward distribution tools"""

    def _get_idea_prompt(self) -> str:
        return """Generate ONE innovative micro Web3 service idea for the Mossland ecosystem.

Provide a structured response with these exact sections (in ENGLISH first, then KOREAN translation):

## Title
A short, descriptive name (3-6 words)

## Problem
What specific problem does this solve? (2-3 sentences)

## Target User
Who will use this? What's their main need? (2-3 sentences)

## Why Mossland
How does this benefit the Mossland ecosystem and MOC token? (2-3 sentences)

## MVP Scope
What's the minimum viable product? List 3-5 core features:
- Feature 1
- Feature 2
- Feature 3

## Technical Approach
Brief technical overview (2-3 sentences mentioning key technologies)

## Risks
Top 2-3 risks and challenges:
- Risk 1
- Risk 2

## Success Metrics
How do we measure success? List 2-3 metrics:
- Metric 1
- Metric 2

---

## 한국어 번역 (Korean Translation)

Now provide the KOREAN translation of ALL sections above:

## 제목
(Title in Korean)

## 문제
(Problem in Korean)

## 대상 사용자
(Target User in Korean)

## 왜 모스랜드인가
(Why Mossland in Korean)

## MVP 범위
(MVP Scope in Korean)

## 기술적 접근
(Technical Approach in Korean)

## 위험 요소
(Risks in Korean)

## 성공 지표
(Success Metrics in Korean)

Be specific and practical. Focus on something that can actually be built quickly."""

    def _parse_idea_response(self, response: str) -> dict:
        """Parse Claude's response into structured idea."""
        # Extract title
        title_match = re.search(r"##\s*Title\s*\n+(.+?)(?=\n\n|\n##)", response, re.DOTALL)
        title = title_match.group(1).strip() if title_match else "Untitled Idea"

        # Clean title
        title = title.replace("#", "").strip()
        if len(title) > 80:
            title = title[:77] + "..."

        # Extract Korean title
        korean_title = self._extract_section(response, "제목", "문제")
        if korean_title == "(Not provided)":
            korean_title = ""
        else:
            korean_title = korean_title.replace("#", "").strip()

        # Build body with all sections (English + Korean)
        body = f"""## Overview

{self._extract_section(response, "Problem", "Target User")}

## Target User

{self._extract_section(response, "Target User", "Why Mossland")}

## Why Mossland

{self._extract_section(response, "Why Mossland", "MVP Scope")}

## MVP Scope

{self._extract_section(response, "MVP Scope", "Technical Approach")}

## Technical Approach

{self._extract_section(response, "Technical Approach", "Risks")}

## Risks

{self._extract_section(response, "Risks", "Success Metrics")}

## Success Metrics

{self._extract_section(response, "Success Metrics", "한국어 번역")}

---

# 🇰🇷 한국어 (Korean)

## 개요

{self._extract_section(response, "문제", "대상 사용자")}

## 대상 사용자

{self._extract_section(response, "대상 사용자", "왜 모스랜드인가")}

## 왜 모스랜드인가

{self._extract_section(response, "왜 모스랜드인가", "MVP 범위")}

## MVP 범위

{self._extract_section(response, "MVP 범위", "기술적 접근")}

## 기술적 접근

{self._extract_section(response, "기술적 접근", "위험 요소")}

## 위험 요소

{self._extract_section(response, "위험 요소", "성공 지표")}

## 성공 지표

{self._extract_section(response, "성공 지표", None)}

---

*Generated by Agentic Orchestrator on {datetime.now().strftime("%Y-%m-%d %H:%M")} UTC*

**To promote this idea to planning:** Add the `promote:to-plan` label.
"""

        return {"title": title, "body": body}

    def _extract_section(
        self,
        text: str,
        section: str,
        next_section: str | None,
    ) -> str:
        """Extract content between two section headers."""
        if next_section:
            pattern = rf"##\s*{section}\s*\n+(.*?)(?=##\s*{next_section})"
        else:
            pattern = rf"##\s*{section}\s*\n+(.*?)$"

        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return "(Not provided)"


class TrendBasedIdeaGenerator:
    """
    Generates ideas based on current trends from RSS feeds.

    Fetches feeds, analyzes trends, and creates GitHub Issues
    with trend-based idea content.
    """

    def __init__(
        self,
        github: GitHubClient,
        claude: ClaudeProvider | None = None,
        config: dict | None = None,
        dry_run: bool = False,
    ):
        self.github = github
        self._claude = claude
        self.config = config or load_config()
        self.dry_run = dry_run

        self._fetcher: FeedFetcher | None = None
        self._analyzer: TrendAnalyzer | None = None
        self._storage: TrendStorage | None = None

    @property
    def claude(self) -> ClaudeProvider:
        if self._claude is None:
            self._claude = create_claude_provider(dry_run=self.dry_run)
        return self._claude

    @property
    def fetcher(self) -> FeedFetcher:
        if self._fetcher is None:
            self._fetcher = FeedFetcher(self.config)
        return self._fetcher

    @property
    def analyzer(self) -> TrendAnalyzer:
        if self._analyzer is None:
            self._analyzer = TrendAnalyzer(
                claude=self.claude,
                config=self.config,
                dry_run=self.dry_run,
            )
        return self._analyzer

    @property
    def storage(self) -> TrendStorage:
        if self._storage is None:
            self._storage = TrendStorage(config=self.config)
        return self._storage

    def run_daily_analysis(self) -> dict[str, TrendAnalysis]:
        """
        Fetch feeds and analyze trends for all periods.

        Returns:
            Dictionary mapping period to TrendAnalysis.
        """
        logger.info("=" * 60)
        logger.info("TREND ANALYSIS START")
        logger.info("=" * 60)

        logger.info("[Step 1/3] Fetching RSS feeds...")
        items = self.fetcher.fetch_all_feeds()
        logger.info(f"[Step 1/3] Result: {len(items)} total items fetched")

        if not items:
            logger.error("[Step 1/3] FAILED: No feed items fetched!")
            logger.info("=" * 60)
            return {}

        logger.info("[Step 2/3] Analyzing trends with Claude...")
        analyses = self.analyzer.analyze_all_periods(items)

        total_trends = sum(len(a.trends) for a in analyses.values())
        logger.info(f"[Step 2/3] Result: {total_trends} trends across {len(analyses)} periods")

        for period, analysis in analyses.items():
            logger.info(
                f"  - {period}: {len(analysis.trends)} trends, "
                f"{analysis.raw_article_count} articles"
            )

        logger.info("[Step 3/3] Saving analysis...")
        if not self.dry_run and analyses:
            file_path = self.storage.save_analysis(analyses)
            if file_path:
                logger.info(f"[Step 3/3] Saved to {file_path}")
            else:
                logger.warning("[Step 3/3] Save skipped (empty or existing file has more)")
        else:
            logger.info("[Step 3/3] Skipped (dry run or no analyses)")

        logger.info("=" * 60)
        logger.info(f"TREND ANALYSIS COMPLETE: {total_trends} trends found")
        logger.info("=" * 60)

        return analyses

    def generate_trend_based_ideas(
        self,
        count: int = 2,
        analyses: dict[str, TrendAnalysis] | None = None,
    ) -> list[GitHubIssue]:
        """
        Generate ideas based on top trends.

        Args:
            count: Number of trend-based ideas to generate.
            analyses: Optional pre-computed trend analyses.

        Returns:
            List of created GitHubIssue objects.
        """
        created = []

        # Get or run analysis
        if analyses is None:
            analyses = self.run_daily_analysis()

        if not analyses:
            logger.warning("No trend analyses available")
            return created

        # Get top trends across all periods (prefer 24h trends)
        top_trends = self._get_top_trends(analyses, count)

        if not top_trends:
            logger.warning("No significant trends found")
            return created

        for i, trend in enumerate(top_trends):
            try:
                logger.info(f"Generating trend-based idea {i + 1}/{count} for: {trend.topic}")

                # Generate idea content
                idea = self._generate_idea_from_trend(trend)

                if self.dry_run:
                    logger.info(f"[DRY RUN] Would create trend-based idea: {idea['title']}")
                    continue

                # Create GitHub Issue with trend label
                issue = self.github.create_issue(
                    title=f"[IDEA] {idea['title']}",
                    body=idea["body"],
                    labels=[
                        Labels.TYPE_IDEA,
                        Labels.STATUS_BACKLOG,
                        Labels.GENERATED_BY_ORCHESTRATOR,
                        Labels.SOURCE_TREND,
                    ],
                )

                created.append(issue)
                logger.info(f"Created trend-based idea #{issue.number}: {idea['title']}")

                # Link idea to trend
                link = TrendIdeaLink(
                    idea_issue_number=issue.number,
                    trend_topic=trend.topic,
                    trend_category=trend.category,
                    analysis_date=datetime.utcnow(),
                )
                self.storage.link_idea_to_trend(link)

            except Exception as e:
                logger.error(f"Failed to generate trend-based idea {i + 1}: {e}")
                continue

        return created

    def _get_top_trends(
        self,
        analyses: dict[str, TrendAnalysis],
        count: int,
    ) -> list[Trend]:
        """
        Get top trends from analyses.

        Prioritizes 24h trends, then supplements with weekly/monthly.
        """
        all_trends = []

        # Priority order: 24h > 1w > 1m
        for period in ["24h", "1w", "1m"]:
            if period in analyses:
                all_trends.extend(analyses[period].trends)

        # Sort by score and deduplicate by topic
        seen_topics = set()
        unique_trends = []
        for trend in sorted(all_trends, key=lambda t: t.score, reverse=True):
            topic_lower = trend.topic.lower()
            if topic_lower not in seen_topics:
                seen_topics.add(topic_lower)
                unique_trends.append(trend)
                if len(unique_trends) >= count:
                    break

        return unique_trends

    def _generate_idea_from_trend(self, trend: Trend) -> dict:
        """Generate idea content based on a trend."""
        prompt = self._get_trend_idea_prompt(trend)

        response = self.claude.chat(
            user_message=prompt,
            system_message=self._get_trend_system_message(),
        )

        return self._parse_trend_idea_response(response, trend)

    def _get_trend_system_message(self) -> str:
        return """You are a creative Web3 product strategist who capitalizes on current trends.

You generate SMALL, FOCUSED micro-service ideas that:
1. Directly leverage or relate to trending topics
2. Can be built as an MVP in 1-2 weeks
3. Have clear value proposition tied to the trend
4. Are technically feasible with Web3 technologies
5. Could optionally integrate with Mossland ecosystem (MOC token) but not required

Focus on:
- Timely opportunities from the trend
- Clear user needs emerging from the trend
- Practical Web3 implementations
- Quick time-to-market for trend relevance"""

    def _get_trend_idea_prompt(self, trend: Trend) -> str:
        headlines = "\n".join(f"- {h}" for h in trend.sample_headlines[:5])
        keywords = ", ".join(trend.keywords[:8])
        idea_seeds = (
            "\n".join(f"- {s}" for s in trend.idea_seeds[:3])
            if trend.idea_seeds
            else "None provided"
        )

        return f"""Based on this trending topic, generate ONE innovative micro Web3 service idea.

## Trend: {trend.topic}
**Category:** {trend.category}
**Score:** {trend.score}/10
**Why trending:** {trend.summary}
**Keywords:** {keywords}

**Sample Headlines:**
{headlines}

**Web3 Relevance:** {trend.web3_relevance or "To be explored"}

**Potential Ideas (for inspiration):**
{idea_seeds}

---

Provide a structured response with these exact sections (in ENGLISH first, then KOREAN translation):

## Title
A short, descriptive name (3-6 words) that reflects the trend

## Trend Connection
How does this idea capitalize on the current trend? (2-3 sentences)

## Problem
What specific problem does this solve? (2-3 sentences)

## Target User
Who will use this? What's their main need? (2-3 sentences)

## MVP Scope
What's the minimum viable product? List 3-5 core features:
- Feature 1
- Feature 2
- Feature 3

## Technical Approach
Brief technical overview (2-3 sentences mentioning key Web3 technologies)

## Risks
Top 2-3 risks and challenges:
- Risk 1
- Risk 2

## Success Metrics
How do we measure success? List 2-3 metrics:
- Metric 1
- Metric 2

---

## 한국어 번역 (Korean Translation)

Now provide the KOREAN translation of ALL sections above:

## 제목
(Title in Korean)

## 트렌드 연결
(Trend Connection in Korean)

## 문제
(Problem in Korean)

## 대상 사용자
(Target User in Korean)

## MVP 범위
(MVP Scope in Korean)

## 기술적 접근
(Technical Approach in Korean)

## 위험 요소
(Risks in Korean)

## 성공 지표
(Success Metrics in Korean)

Be specific, practical, and timely. Focus on something that can be built quickly while the trend is hot."""

    def _parse_trend_idea_response(self, response: str, trend: Trend) -> dict:
        """Parse Claude's response into structured idea."""
        # Extract title
        title_match = re.search(r"##\s*Title\s*\n+(.+?)(?=\n\n|\n##)", response, re.DOTALL)
        title = title_match.group(1).strip() if title_match else f"Trend-Based: {trend.topic[:50]}"

        # Clean title
        title = title.replace("#", "").strip()
        if len(title) > 80:
            title = title[:77] + "..."

        # Build body with trend context (English + Korean)
        body = f"""## Trend Source

**Topic:** {trend.topic}
**Category:** {trend.category}
**Score:** {trend.score}/10
**Keywords:** {", ".join(trend.keywords[:5])}

---

## Trend Connection

{self._extract_section(response, "Trend Connection", "Problem")}

## Problem

{self._extract_section(response, "Problem", "Target User")}

## Target User

{self._extract_section(response, "Target User", "MVP Scope")}

## MVP Scope

{self._extract_section(response, "MVP Scope", "Technical Approach")}

## Technical Approach

{self._extract_section(response, "Technical Approach", "Risks")}

## Risks

{self._extract_section(response, "Risks", "Success Metrics")}

## Success Metrics

{self._extract_section(response, "Success Metrics", "한국어 번역")}

---

# 🇰🇷 한국어 (Korean)

## 트렌드 연결

{self._extract_section(response, "트렌드 연결", "문제")}

## 문제

{self._extract_section(response, "문제", "대상 사용자")}

## 대상 사용자

{self._extract_section(response, "대상 사용자", "MVP 범위")}

## MVP 범위

{self._extract_section(response, "MVP 범위", "기술적 접근")}

## 기술적 접근

{self._extract_section(response, "기술적 접근", "위험 요소")}

## 위험 요소

{self._extract_section(response, "위험 요소", "성공 지표")}

## 성공 지표

{self._extract_section(response, "성공 지표", None)}

---

*Generated by Agentic Orchestrator (Trend-Based) on {datetime.now().strftime("%Y-%m-%d %H:%M")} UTC*

**Source Trend:** {trend.topic} ({trend.time_period})

**To promote this idea to planning:** Add the `promote:to-plan` label.
"""

        return {"title": title, "body": body}

    def _extract_section(
        self,
        text: str,
        section: str,
        next_section: str | None,
    ) -> str:
        """Extract content between two section headers."""
        if next_section:
            pattern = rf"##\s*{section}\s*\n+(.*?)(?=##\s*{next_section})"
        else:
            pattern = rf"##\s*{section}\s*\n+(.*?)$"

        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return "(Not provided)"

    def get_trend_status(self, days: int = 7) -> dict:
        """
        Get trend analysis status for recent days.

        Args:
            days: Number of days to look back.

        Returns:
            Dictionary with trend status information.
        """
        recent = self.storage.get_recent_analyses(days=days)
        links = self.storage.get_all_idea_links()

        return {
            "analyses_available": len(recent),
            "total_ideas_from_trends": len(links),
            "recent_trends": [
                {
                    "date": (
                        list(analysis.values())[0].date.strftime("%Y-%m-%d") if analysis else None
                    ),
                    "periods": list(analysis.keys()),
                    "total_trends": sum(len(a.trends) for a in analysis.values()),
                }
                for analysis in recent[:5]
            ],
            "idea_links": [
                {
                    "issue": link.idea_issue_number,
                    "trend": link.trend_topic,
                    "category": link.trend_category,
                }
                for link in links[-10:]  # Last 10 links
            ],
        }


class PlanGenerator:
    """
    Generates planning documents from promoted ideas.

    Creates detailed PRD, Architecture, Tasks, and Acceptance Criteria
    and stores them in a new GitHub Issue.

    Supports two modes:
    1. Simple mode: Single AI generates the plan (default fallback)
    2. Debate mode: Multi-agent debate with Founder, VC, Accelerator, Founder Friend
    """

    def __init__(
        self,
        github: GitHubClient,
        claude: ClaudeProvider | None = None,
        openai: OpenAIProvider | None = None,
        gemini: GeminiProvider | None = None,
        dry_run: bool = False,
        enable_debate: bool = True,
        debate_max_rounds: int = 5,
    ):
        self.github = github
        self._claude = claude
        self._openai = openai
        self._gemini = gemini
        self.dry_run = dry_run
        self.enable_debate = enable_debate
        self.debate_max_rounds = debate_max_rounds

    @property
    def claude(self) -> ClaudeProvider:
        if self._claude is None:
            self._claude = create_claude_provider(dry_run=self.dry_run)
        return self._claude

    @property
    def openai(self) -> OpenAIProvider | None:
        if self._openai is None:
            try:
                self._openai = create_openai_provider(dry_run=self.dry_run)
            except Exception as e:
                logger.warning(f"Failed to create OpenAI provider: {e}")
                return None
        return self._openai

    @property
    def gemini(self) -> GeminiProvider | None:
        if self._gemini is None:
            try:
                self._gemini = create_gemini_provider(dry_run=self.dry_run)
            except Exception as e:
                logger.warning(f"Failed to create Gemini provider: {e}")
                return None
        return self._gemini

    def _all_providers_available(self) -> bool:
        """Check if all providers are available for debate mode."""
        try:
            claude_ok = self.claude is not None and self.claude.is_available()
            openai_ok = self.openai is not None and self.openai.is_available()
            gemini_ok = self.gemini is not None and self.gemini.is_available()
            return claude_ok and openai_ok and gemini_ok
        except Exception:
            return False

    def _get_providers_dict(self) -> dict[str, BaseProvider]:
        """Get providers as a dictionary for debate session."""
        providers = {}
        if self.claude:
            providers["claude"] = self.claude
        if self.openai:
            providers["openai"] = self.openai
        if self.gemini:
            providers["gemini"] = self.gemini
        return providers

    def generate_plan_from_idea(self, idea_issue: GitHubIssue) -> GitHubIssue | None:
        """
        Generate a plan issue from an idea issue.

        Args:
            idea_issue: The idea issue to plan.

        Returns:
            Created plan issue, or None if failed/skipped.
        """
        logger.info(f"Generating plan for idea #{idea_issue.number}: {idea_issue.title}")

        # Idempotency check: skip if already processed
        if idea_issue.has_label(Labels.PROCESSED_TO_PLAN):
            logger.info(f"Idea #{idea_issue.number} already has processed label, skipping")
            return None

        if idea_issue.has_label(Labels.STATUS_PLANNED):
            logger.info(f"Idea #{idea_issue.number} already planned, skipping")
            return None

        # Check for existing plan that references this idea
        existing_plans = self._find_existing_plan_for_idea(idea_issue.number)
        if existing_plans:
            logger.info(
                f"Plan already exists for idea #{idea_issue.number}: "
                f"#{existing_plans[0].number}, skipping"
            )
            return None

        # Choose generation mode: debate or simple
        if self.enable_debate and self._all_providers_available():
            logger.info("Using multi-agent debate mode for plan generation")
            return self._generate_plan_with_debate(idea_issue)
        else:
            if self.enable_debate:
                logger.warning(
                    "Debate mode enabled but not all providers available, "
                    "falling back to simple mode"
                )
            return self._generate_plan_simple(idea_issue)

    def _generate_plan_simple(self, idea_issue: GitHubIssue) -> GitHubIssue | None:
        """
        Generate plan using single AI (simple mode).

        This is the fallback mode when debate mode is disabled or
        not all providers are available.
        """
        # Track created artifacts for rollback
        created_plan: GitHubIssue | None = None

        try:
            # Generate plan content
            plan_content = self._generate_plan_content(idea_issue)

            if self.dry_run:
                logger.info(f"[DRY RUN] Would create plan for idea #{idea_issue.number}")
                return None

            # Step 1: Create plan issue
            plan_title = idea_issue.title.replace("[IDEA]", "[PLAN]")
            created_plan = self.github.create_issue(
                title=plan_title,
                body=plan_content,
                labels=[
                    Labels.TYPE_PLAN,
                    Labels.STATUS_BACKLOG,
                    Labels.GENERATED_BY_ORCHESTRATOR,
                ],
            )
            logger.debug(f"Created plan issue #{created_plan.number}")

            # Step 2: Update idea issue status
            self.github.mark_idea_as_planned(idea_issue.number)
            logger.debug(f"Marked idea #{idea_issue.number} as planned")

            # Step 3: Add cross-reference comments (non-critical, don't rollback for these)
            try:
                self.github.add_comment(
                    idea_issue.number,
                    f"Planning document created: #{created_plan.number}\n\n"
                    f"This idea has been promoted to the planning phase.",
                )

                self.github.add_comment(
                    created_plan.number,
                    f"This plan was generated from idea #{idea_issue.number}.\n\n"
                    f"**To promote this plan to development:** Add the `promote:to-dev` label.",
                )
            except Exception as comment_err:
                # Comments are non-critical, just log warning
                logger.warning(f"Failed to add cross-reference comments: {comment_err}")

            logger.info(f"Created plan issue #{created_plan.number}")
            return created_plan

        except Exception as e:
            logger.error(f"Failed to generate plan for #{idea_issue.number}: {e}")

            # Rollback: Close the created plan issue if it exists
            if created_plan is not None:
                try:
                    logger.warning(
                        f"Rolling back: closing plan issue #{created_plan.number} "
                        f"due to error: {e}"
                    )
                    self.github.update_issue(
                        created_plan.number,
                        state="closed",
                        labels=[Labels.TYPE_PLAN, "rollback:failed"],
                    )
                    self.github.add_comment(
                        created_plan.number,
                        f"This plan was automatically closed due to an error during creation.\n\n"
                        f"Error: {e}\n\n"
                        f"The original idea #{idea_issue.number} may need to be re-promoted.",
                    )
                except Exception as rollback_err:
                    logger.error(f"Failed to rollback plan issue: {rollback_err}")

            # Add error comment to idea (only if plan wasn't created or rollback succeeded)
            if not self.dry_run:
                try:
                    self.github.add_comment(
                        idea_issue.number,
                        f"Failed to generate plan: {e}\n\n"
                        f"Please try again or create plan manually.",
                    )
                except Exception:
                    pass  # Best effort

            raise

    def _generate_plan_content(self, idea_issue: GitHubIssue) -> str:
        """Generate detailed planning content."""
        prompt = f"""Based on the following idea, create a detailed planning document.

# Idea: {idea_issue.title}

{idea_issue.body}

---

Create a comprehensive planning document with these sections:

## 1. Product Requirements Document (PRD)

### 1.1 Executive Summary
Brief overview (2-3 sentences)

### 1.2 Problem Statement
Detailed problem description

### 1.3 Goals and Success Metrics
- Primary goal
- Key metrics

### 1.4 User Stories
Write 3-5 user stories in format: "As a [user], I want [action] so that [benefit]"

### 1.5 Functional Requirements
List core features with priorities (Must Have / Should Have / Nice to Have)

### 1.6 Non-Functional Requirements
Performance, security, scalability considerations

## 2. Architecture

### 2.1 System Overview
High-level architecture description

### 2.2 Technology Stack
| Layer | Technology | Justification |
|-------|------------|---------------|

### 2.3 Component Design
Key components and their responsibilities

### 2.4 Data Model
Core entities and relationships

### 2.5 API Design
Key endpoints (if applicable)

## 3. Task Breakdown

### Phase 1: Setup
- [ ] Task 1 (Effort: S/M/L)
- [ ] Task 2

### Phase 2: Core Development
- [ ] Task 3
- [ ] Task 4

### Phase 3: Integration & Testing
- [ ] Task 5
- [ ] Task 6

## 4. Acceptance Criteria

### Feature 1
- [ ] Criterion 1
- [ ] Criterion 2

### Feature 2
- [ ] Criterion 1

## 5. Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|

## 6. Timeline Estimate

- Phase 1: X days
- Phase 2: X days
- Phase 3: X days
- **Total: X days**

Be specific and practical. Focus on MVP scope that can be built in 1-2 weeks."""

        response = self.claude.chat(
            user_message=prompt,
            system_message="You are an expert product manager and software architect. Create detailed, actionable planning documents.",
        )

        # Add metadata
        body = f"""# Planning Document

**Source Idea:** #{idea_issue.number}
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M")} UTC

---

{response}

---

**To promote this plan to development:** Add the `promote:to-dev` label.
"""

        return body

    def _generate_plan_with_debate(self, idea_issue: GitHubIssue) -> GitHubIssue | None:
        """
        Generate plan using multi-agent debate mode.

        This mode uses Claude, ChatGPT, and Gemini to play different roles
        (Founder, VC, Accelerator, Founder Friend) and debate the plan
        through multiple rounds.
        """
        created_plan: GitHubIssue | None = None

        try:
            # Create debate session
            session = create_debate_session(
                idea_title=idea_issue.title,
                idea_content=idea_issue.body,
                idea_issue_number=idea_issue.number,
                providers=self._get_providers_dict(),
                max_rounds=self.debate_max_rounds,
                dry_run=self.dry_run,
            )

            # Run the debate
            logger.info(f"Starting debate for idea #{idea_issue.number}")
            debate_result = session.run_debate()
            logger.info(
                f"Debate completed: {debate_result.total_rounds} rounds, "
                f"reason: {debate_result.termination_reason}"
            )

            if self.dry_run:
                logger.info(
                    f"[DRY RUN] Would create plan from debate for idea #{idea_issue.number}"
                )
                return None

            # Build plan content with debate result
            plan_content = self._format_debate_plan(idea_issue, debate_result)

            # Create plan issue
            plan_title = idea_issue.title.replace("[IDEA]", "[PLAN]")
            created_plan = self.github.create_issue(
                title=plan_title,
                body=plan_content,
                labels=[
                    Labels.TYPE_PLAN,
                    Labels.STATUS_BACKLOG,
                    Labels.GENERATED_BY_ORCHESTRATOR,
                ],
            )
            logger.debug(f"Created plan issue #{created_plan.number}")

            # Update debate record with plan issue number
            debate_result.record.plan_issue_number = created_plan.number

            # Add discussion record as comment
            discussion_comment = debate_result.format_discussion_record()
            self.github.add_comment(created_plan.number, discussion_comment)
            logger.debug(f"Added discussion record to plan #{created_plan.number}")

            # Update idea issue status
            self.github.mark_idea_as_planned(idea_issue.number)
            logger.debug(f"Marked idea #{idea_issue.number} as planned")

            # Add cross-reference comments
            try:
                self.github.add_comment(
                    idea_issue.number,
                    f"Planning document created: #{created_plan.number}\n\n"
                    f"This idea has been promoted to the planning phase through "
                    f"a {debate_result.total_rounds}-round multi-agent debate.",
                )

                self.github.add_comment(
                    created_plan.number,
                    f"This plan was generated from idea #{idea_issue.number}.\n\n"
                    f"**Generation method:** Multi-agent debate ({debate_result.total_rounds} rounds)\n"
                    f"**Termination reason:** {debate_result.termination_reason}\n\n"
                    f"**To promote this plan to development:** Add the `promote:to-dev` label.",
                )
            except Exception as comment_err:
                logger.warning(f"Failed to add cross-reference comments: {comment_err}")

            logger.info(f"Created plan issue #{created_plan.number} via debate")
            return created_plan

        except Exception as e:
            logger.error(f"Failed to generate plan via debate for #{idea_issue.number}: {e}")

            # Rollback if plan was created
            if created_plan is not None:
                try:
                    logger.warning(f"Rolling back: closing plan issue #{created_plan.number}")
                    self.github.update_issue(
                        created_plan.number,
                        state="closed",
                        labels=[Labels.TYPE_PLAN, "rollback:failed"],
                    )
                    self.github.add_comment(
                        created_plan.number,
                        f"This plan was automatically closed due to an error during debate.\n\n"
                        f"Error: {e}\n\n"
                        f"The original idea #{idea_issue.number} may need to be re-promoted.",
                    )
                except Exception as rollback_err:
                    logger.error(f"Failed to rollback plan issue: {rollback_err}")

            # Add error comment to idea
            if not self.dry_run:
                try:
                    self.github.add_comment(
                        idea_issue.number,
                        f"Failed to generate plan via debate: {e}\n\n"
                        f"Please try again or create plan manually.",
                    )
                except Exception:
                    pass

            raise

    def _format_debate_plan(self, idea_issue: GitHubIssue, debate_result: DebateResult) -> str:
        """Format the final plan from debate result."""
        body = f"""# Planning Document

**Source Idea:** #{idea_issue.number}
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M")} UTC
**Generation Method:** Multi-Agent Debate ({debate_result.total_rounds} rounds)

---

{debate_result.final_plan}

---

**To promote this plan to development:** Add the `promote:to-dev` label.
"""
        return body

    def _find_existing_plan_for_idea(self, idea_number: int) -> list[GitHubIssue]:
        """
        Find existing OPEN plan issues that reference a specific idea.

        Only returns open plans - closed/rejected plans are ignored,
        allowing new plans to be generated for the same idea.

        Args:
            idea_number: The idea issue number to search for.

        Returns:
            List of open plan issues that reference this idea.
        """
        try:
            # Search for OPEN plan issues only (closed/rejected plans are ignored)
            plans = self.github.search_issues(
                labels=[Labels.TYPE_PLAN],
                state="open",  # Only open plans - rejected plans are closed
            )

            # Filter plans that reference this idea in their body
            matching_plans = []
            source_patterns = [
                f"Source Idea: #{idea_number}",
                f"Source Idea:** #{idea_number}",
                f"idea #{idea_number}",
            ]
            for plan in plans:
                if any(pattern in plan.body for pattern in source_patterns):
                    matching_plans.append(plan)

            return matching_plans
        except Exception as e:
            logger.warning(f"Failed to search for existing plans: {e}")
            return []


class DevScaffolder:
    """
    Sets up development environment from promoted plans.

    Creates project structure, initial files, and prepares
    for development work.
    """

    def __init__(
        self,
        github: GitHubClient,
        base_path: Path | None = None,
        dry_run: bool = False,
    ):
        self.github = github
        self.base_path = base_path or Path.cwd()
        self.dry_run = dry_run
        self._git: GitHelper | None = None

    @property
    def git(self) -> GitHelper:
        if self._git is None:
            self._git = GitHelper(self.base_path)
        return self._git

    def scaffold_from_plan(self, plan_issue: GitHubIssue) -> str | None:
        """
        Create development scaffold from a plan issue.

        Args:
            plan_issue: The plan issue to scaffold.

        Returns:
            Project ID if successful, None if failed/skipped.
        """
        logger.info(f"Scaffolding development for plan #{plan_issue.number}")

        # Idempotency check: skip if already processed
        if plan_issue.has_label(Labels.PROCESSED_TO_DEV):
            logger.info(f"Plan #{plan_issue.number} already has processed label, skipping")
            return None

        if plan_issue.has_label(Labels.STATUS_IN_DEV):
            logger.info(f"Plan #{plan_issue.number} already in development, skipping")
            return None

        # Check for existing project directory for this plan
        existing_project = self._find_existing_project_for_plan(plan_issue.number)
        if existing_project:
            logger.info(
                f"Project already exists for plan #{plan_issue.number}: "
                f"{existing_project}, skipping"
            )
            return None

        try:
            # Generate project ID
            project_id = generate_project_id()

            if self.dry_run:
                logger.info(f"[DRY RUN] Would scaffold project {project_id}")
                return project_id

            # Create project structure
            project_dir = get_project_dir(project_id, self.base_path)
            self._create_project_structure(project_dir, plan_issue, project_id)

            # Commit changes
            self.git.add(all=True)
            self.git.commit(
                f"[dev] Scaffold project {project_id} from plan #{plan_issue.number}",
                stage="DEV",
                project_id=project_id,
            )

            # Update plan issue
            self.github.mark_plan_as_in_dev(plan_issue.number)

            # Add comment with project info
            self.github.add_comment(
                plan_issue.number,
                f"Development started!\n\n"
                f"- **Project ID:** `{project_id}`\n"
                f"- **Directory:** `projects/{project_id}/`\n\n"
                f"Initial scaffold has been committed to the repository.",
            )

            logger.info(f"Created project scaffold: {project_id}")
            return project_id

        except Exception as e:
            logger.error(f"Failed to scaffold from plan #{plan_issue.number}: {e}")
            if not self.dry_run:
                self.github.add_comment(
                    plan_issue.number,
                    f"Failed to start development: {e}\n\nPlease check the logs and try again.",
                )
            raise

    def _create_project_structure(
        self,
        project_dir: Path,
        plan_issue: GitHubIssue,
        project_id: str,
    ) -> None:
        """Create the project directory structure."""
        # Create directories
        dirs = [
            project_dir / "01_ideation",
            project_dir / "02_planning",
            project_dir / "03_implementation" / "src",
            project_dir / "03_implementation" / "tests",
            project_dir / "04_quality",
        ]
        for d in dirs:
            ensure_dir(d)

        # Extract idea number from plan body
        idea_ref = re.search(r"Source Idea.*?#(\d+)", plan_issue.body)
        idea_number = idea_ref.group(1) if idea_ref else "unknown"

        # Save plan document
        write_markdown(
            project_dir / "02_planning" / "PLAN.md",
            plan_issue.body,
            title=plan_issue.title,
            metadata={
                "source_issue": plan_issue.number,
                "source_idea": idea_number,
                "project_id": project_id,
                "created_at": datetime.now().isoformat(),
            },
        )

        # Create project README
        readme_content = f"""# Project: {project_id}

## Source

- **Plan Issue:** [#{plan_issue.number}]({plan_issue.html_url})
- **Idea Issue:** #{idea_number}

## Status

- [x] Idea generated
- [x] Planning complete
- [ ] Development in progress
- [ ] Quality assurance
- [ ] Complete

## Structure

```
{project_id}/
├── 01_ideation/       # Original idea documents
├── 02_planning/       # PRD, Architecture, Tasks
├── 03_implementation/ # Source code
│   ├── src/
│   └── tests/
└── 04_quality/        # QA reports, reviews
```

## Development

Development was initiated on {datetime.now().strftime("%Y-%m-%d")}.

See `02_planning/PLAN.md` for detailed requirements and tasks.
"""

        write_markdown(
            project_dir / "README.md",
            readme_content,
            title=f"Project {project_id}",
        )

        # Create implementation placeholder
        write_markdown(
            project_dir / "03_implementation" / "README.md",
            "# Implementation\n\nSource code will be added here during development.",
        )

    def _find_existing_project_for_plan(self, plan_number: int) -> str | None:
        """
        Find existing project directory that references a specific plan.

        Args:
            plan_number: The plan issue number to search for.

        Returns:
            Project ID if found, None otherwise.
        """
        try:
            projects_dir = self.base_path / "projects"
            if not projects_dir.exists():
                return None

            # Search through project directories
            for project_path in projects_dir.iterdir():
                if not project_path.is_dir():
                    continue

                # Check PLAN.md or README.md for plan reference
                plan_md = project_path / "02_planning" / "PLAN.md"
                readme_md = project_path / "README.md"

                for check_file in [plan_md, readme_md]:
                    if check_file.exists():
                        content = check_file.read_text()
                        if (
                            f"#{plan_number}" in content
                            or f"source_issue: {plan_number}" in content
                        ):
                            return project_path.name

            return None
        except Exception as e:
            logger.warning(f"Failed to search for existing projects: {e}")
            return None


class BacklogOrchestrator:
    """
    Main orchestrator for the backlog-based workflow.

    Handles:
    - Periodic idea generation
    - Polling for promotion labels
    - Processing promoted items
    - Concurrency control
    """

    def __init__(
        self,
        base_path: Path | None = None,
        dry_run: bool = False,
    ):
        self.base_path = base_path or Path.cwd()
        self.dry_run = dry_run or get_env_bool("DRY_RUN")
        self.config = load_config()

        self._github: GitHubClient | None = None
        self._idea_generator: IdeaGenerator | None = None
        self._trend_generator: TrendBasedIdeaGenerator | None = None
        self._plan_generator: PlanGenerator | None = None
        self._dev_scaffolder: DevScaffolder | None = None

        # Concurrency control
        self._lock_file = self.base_path / ".agent" / "orchestrator.lock"

    @property
    def github(self) -> GitHubClient:
        if self._github is None:
            self._github = GitHubClient()
        return self._github

    @property
    def idea_generator(self) -> IdeaGenerator:
        if self._idea_generator is None:
            self._idea_generator = IdeaGenerator(
                github=self.github,
                dry_run=self.dry_run,
            )
        return self._idea_generator

    @property
    def trend_generator(self) -> TrendBasedIdeaGenerator:
        if self._trend_generator is None:
            self._trend_generator = TrendBasedIdeaGenerator(
                github=self.github,
                config=self.config,
                dry_run=self.dry_run,
            )
        return self._trend_generator

    @property
    def plan_generator(self) -> PlanGenerator:
        if self._plan_generator is None:
            self._plan_generator = PlanGenerator(
                github=self.github,
                dry_run=self.dry_run,
            )
        return self._plan_generator

    @property
    def dev_scaffolder(self) -> DevScaffolder:
        if self._dev_scaffolder is None:
            self._dev_scaffolder = DevScaffolder(
                github=self.github,
                base_path=self.base_path,
                dry_run=self.dry_run,
            )
        return self._dev_scaffolder

    def acquire_lock(self) -> bool:
        """
        Acquire execution lock to prevent concurrent runs.

        Includes stale lock detection:
        - Checks if lock holder process is still alive
        - Checks if lock has exceeded timeout
        """
        import fcntl
        import os

        ensure_dir(self._lock_file.parent)

        # Check for stale lock before attempting to acquire
        self._cleanup_stale_lock()

        try:
            self._lock_fd = open(self._lock_file, "w")
            fcntl.flock(self._lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            self._lock_fd.write(f"{os.getpid()}\n{datetime.now().isoformat()}")
            self._lock_fd.flush()
            return True
        except OSError:
            logger.warning("Another orchestrator instance is running")
            return False

    def _cleanup_stale_lock(self) -> None:
        """Remove stale lock if process is dead or timeout exceeded."""

        if not self._lock_file.exists():
            return

        try:
            content = self._lock_file.read_text().strip()
            lines = content.split("\n")
            if len(lines) < 2:
                # Malformed lock file, remove it
                logger.warning("Malformed lock file detected, removing")
                self._lock_file.unlink()
                return

            pid_str, timestamp_str = lines[0], lines[1]
            pid = int(pid_str)
            lock_time = datetime.fromisoformat(timestamp_str)

            # Get lock timeout from config (default 300 seconds)
            lock_timeout = self.config.get("orchestrator", "lock_timeout_seconds", default=300)

            # Check if lock has timed out
            elapsed = (datetime.now() - lock_time).total_seconds()
            if elapsed > lock_timeout:
                logger.warning(
                    f"Stale lock detected: lock held for {elapsed:.0f}s "
                    f"(timeout: {lock_timeout}s), removing"
                )
                self._lock_file.unlink()
                return

            # Check if process is still alive
            if not self._is_process_alive(pid):
                logger.warning(f"Dead process lock detected: PID {pid} no longer exists, removing")
                self._lock_file.unlink()
                return

        except (ValueError, OSError) as e:
            logger.warning(f"Error checking lock file: {e}, removing lock")
            try:
                self._lock_file.unlink()
            except OSError:
                pass

    def _is_process_alive(self, pid: int) -> bool:
        """Check if a process with the given PID is still running."""
        import os

        try:
            # Sending signal 0 checks if process exists without actually signaling
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            # Process does not exist
            return False
        except PermissionError:
            # Process exists but we don't have permission (still alive)
            return True

    def release_lock(self) -> None:
        """Release execution lock."""
        import fcntl

        if hasattr(self, "_lock_fd") and self._lock_fd:
            try:
                fcntl.flock(self._lock_fd.fileno(), fcntl.LOCK_UN)
                self._lock_fd.close()
                self._lock_file.unlink(missing_ok=True)
            except Exception:
                pass

    def run_cycle(
        self,
        generate_ideas: bool = True,
        idea_count: int = 1,
        trend_idea_count: int = 0,
        run_trend_analysis: bool = False,
        max_promotions: int = 5,
    ) -> dict:
        """
        Run one orchestration cycle.

        Args:
            generate_ideas: Whether to generate new ideas.
            idea_count: Number of traditional ideas to generate.
            trend_idea_count: Number of trend-based ideas to generate.
            run_trend_analysis: Whether to run trend analysis.
            max_promotions: Maximum promotions to process.

        Returns:
            Summary of actions taken.
        """
        if not self.acquire_lock():
            return {"error": "Could not acquire lock - another instance running"}

        try:
            results = {
                "ideas_generated": 0,
                "trend_ideas_generated": 0,
                "trends_analyzed": False,
                "plans_generated": 0,
                "plans_rejected": 0,
                "devs_started": 0,
                "errors": [],
            }

            # 0. Run trend analysis (if enabled)
            trend_analyses = None
            if run_trend_analysis or trend_idea_count > 0:
                try:
                    logger.info("Running trend analysis...")
                    trend_analyses = self.trend_generator.run_daily_analysis()
                    results["trends_analyzed"] = bool(trend_analyses)
                    if trend_analyses:
                        total_trends = sum(len(a.trends) for a in trend_analyses.values())
                        logger.info(
                            f"Analyzed {total_trends} trends across {len(trend_analyses)} periods"
                        )
                except Exception as e:
                    logger.error(f"Trend analysis failed: {e}")
                    results["errors"].append(f"Trend analysis: {e}")

            # 1. Generate new ideas (if enabled)
            if generate_ideas:
                try:
                    ideas = self.idea_generator.generate_ideas(count=idea_count)
                    results["ideas_generated"] = len(ideas)
                except Exception as e:
                    logger.error(f"Idea generation failed: {e}")
                    results["errors"].append(f"Idea generation: {e}")

            # 2. Generate trend-based ideas (if enabled)
            if trend_idea_count > 0:
                try:
                    trend_ideas = self.trend_generator.generate_trend_based_ideas(
                        count=trend_idea_count,
                        analyses=trend_analyses,
                    )
                    results["trend_ideas_generated"] = len(trend_ideas)
                except Exception as e:
                    logger.error(f"Trend-based idea generation failed: {e}")
                    results["errors"].append(f"Trend ideas: {e}")

            # 3. Process rejected plans FIRST (before promotions)
            # This ensures rejected plans reset their ideas before promotion processing
            try:
                rejected_plans = self.github.find_rejected_plans()
                for plan in rejected_plans[:max_promotions]:
                    try:
                        result = self._process_rejected_plan(plan)
                        if result:
                            results["plans_rejected"] += 1
                    except Exception as e:
                        logger.error(f"Rejected plan processing failed for #{plan.number}: {e}")
                        results["errors"].append(f"Reject plan #{plan.number}: {e}")
            except Exception as e:
                logger.error(f"Finding rejected plans failed: {e}")
                results["errors"].append(f"Find rejected plans: {e}")

            # 4. Process idea promotions (including newly reset ideas from rejected plans)
            try:
                promoted_ideas = self.github.find_ideas_to_promote()
                for idea in promoted_ideas[:max_promotions]:
                    try:
                        plan = self.plan_generator.generate_plan_from_idea(idea)
                        if plan:
                            results["plans_generated"] += 1
                    except Exception as e:
                        logger.error(f"Plan generation failed for #{idea.number}: {e}")
                        results["errors"].append(f"Plan for #{idea.number}: {e}")
            except Exception as e:
                logger.error(f"Finding promoted ideas failed: {e}")
                results["errors"].append(f"Find promoted ideas: {e}")

            # 4. Process plan promotions
            try:
                promoted_plans = self.github.find_plans_to_promote()
                for plan in promoted_plans[:max_promotions]:
                    try:
                        project_id = self.dev_scaffolder.scaffold_from_plan(plan)
                        if project_id:
                            results["devs_started"] += 1
                    except Exception as e:
                        logger.error(f"Dev scaffold failed for #{plan.number}: {e}")
                        results["errors"].append(f"Dev for #{plan.number}: {e}")
            except Exception as e:
                logger.error(f"Finding promoted plans failed: {e}")
                results["errors"].append(f"Find promoted plans: {e}")

            return results

        except GitHubRateLimitError as e:
            logger.error(f"GitHub rate limit hit: {e}")
            return {"error": f"GitHub rate limit: retry after {e.reset_time}"}

        except QuotaExhaustedError as e:
            logger.error(f"API quota exhausted: {e}")
            create_alert_file(
                alert_type="quota",
                provider=e.provider,
                model=e.model,
                stage="backlog",
                error=str(e),
                resolution="Check API quota and billing. Restart with: ao backlog",
                base_path=self.base_path,
            )
            return {"error": f"Quota exhausted: {e}"}

        finally:
            self.release_lock()

    def setup_labels(self) -> None:
        """Ensure all required labels exist in the repository."""
        logger.info("Setting up labels...")
        self.github.ensure_labels_exist()
        logger.info("Labels setup complete")

    def get_status(self) -> dict:
        """Get current backlog status."""
        try:
            backlog_ideas = self.github.find_backlog_ideas()
            backlog_plans = self.github.find_backlog_plans()
            ideas_to_promote = self.github.find_ideas_to_promote()
            plans_to_promote = self.github.find_plans_to_promote()

            # Count trend-based ideas
            trend_ideas = [i for i in backlog_ideas if i.has_label(Labels.SOURCE_TREND)]

            return {
                "backlog": {
                    "ideas": len(backlog_ideas),
                    "trend_ideas": len(trend_ideas),
                    "plans": len(backlog_plans),
                },
                "pending_promotion": {
                    "ideas_to_plan": len(ideas_to_promote),
                    "plans_to_dev": len(plans_to_promote),
                },
                "issues": {
                    "ideas": [{"number": i.number, "title": i.title} for i in backlog_ideas[:10]],
                    "plans": [{"number": p.number, "title": p.title} for p in backlog_plans[:10]],
                },
            }
        except Exception as e:
            return {"error": str(e)}

    def get_trend_status(self, days: int = 7) -> dict:
        """Get trend analysis status."""
        return self.trend_generator.get_trend_status(days=days)

    def _process_rejected_plan(self, plan_issue: GitHubIssue) -> bool:
        """
        Process a rejected plan: close it and reset the original idea for re-planning.

        Args:
            plan_issue: The rejected PLAN issue

        Returns:
            True if processed successfully
        """
        logger.info(f"Processing rejected plan #{plan_issue.number}: {plan_issue.title}")

        # Find the original idea number from the plan body
        idea_number = self._extract_idea_number_from_plan(plan_issue)

        if not idea_number:
            logger.warning(
                f"Could not find source idea for plan #{plan_issue.number}, "
                "closing plan without resetting idea"
            )
            # Still close the plan but can't reset the idea
            self.github.update_issue(
                plan_issue.number,
                state="closed",
                labels=[Labels.TYPE_PLAN, "rejected", "orphan"],
            )
            self.github.add_comment(
                plan_issue.number,
                "This plan was rejected but the source idea could not be found.\n\n"
                "The plan has been closed. Please manually re-promote the original idea if needed.",
            )
            return True

        # Reject the plan and reset the idea
        closed_plan, reset_idea = self.github.reject_plan(
            plan_issue_number=plan_issue.number,
            idea_issue_number=idea_number,
        )

        # Add comments explaining what happened
        self.github.add_comment(
            plan_issue.number,
            f"This plan was rejected by a human reviewer.\n\n"
            f"The original idea #{idea_number} has been reset and is ready for re-planning.\n\n"
            f"A new planning round will start automatically when the orchestrator runs.",
        )

        self.github.add_comment(
            idea_number,
            f"The plan (#{plan_issue.number}) generated from this idea was rejected.\n\n"
            f"This idea has been reset to the backlog with `promote:to-plan` label.\n"
            f"A new plan will be generated in the next orchestrator cycle.",
        )

        logger.info(
            f"Rejected plan #{plan_issue.number}, reset idea #{idea_number} for re-planning"
        )
        return True

    def _extract_idea_number_from_plan(self, plan_issue: GitHubIssue) -> int | None:
        """
        Extract the source idea number from a plan issue body.

        Args:
            plan_issue: The PLAN issue

        Returns:
            Idea issue number or None if not found
        """
        import re

        # Look for patterns like "Source Idea: #123" or "idea #123"
        patterns = [
            r"Source Idea:\s*#(\d+)",
            r"\*\*Source Idea:\*\*\s*#(\d+)",
            r"from idea #(\d+)",
            r"idea #(\d+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, plan_issue.body, re.IGNORECASE)
            if match:
                return int(match.group(1))

        return None

    def reject_plan_manually(self, plan_number: int) -> dict:
        """
        Manually reject a plan by issue number.

        This is for CLI use when a user wants to reject a specific plan.

        Args:
            plan_number: The PLAN issue number to reject

        Returns:
            Result summary
        """
        try:
            plan_issue = self.github.get_issue(plan_number)

            # Verify it's a plan
            if not plan_issue.has_label(Labels.TYPE_PLAN):
                return {"error": f"Issue #{plan_number} is not a PLAN issue"}

            # Verify it's not already closed
            if plan_issue.state == "closed":
                return {"error": f"Plan #{plan_number} is already closed"}

            # Process the rejection
            success = self._process_rejected_plan(plan_issue)

            if success:
                return {
                    "success": True,
                    "message": f"Plan #{plan_number} rejected and idea reset for re-planning",
                }
            else:
                return {"error": "Failed to process plan rejection"}

        except Exception as e:
            return {"error": str(e)}
