"""
Trend analysis using LLM.

Analyzes feed items to identify trending topics using Claude.
"""

import json
import re
from datetime import datetime

from ..providers.claude import ClaudeProvider, create_claude_provider
from ..utils.config import Config, load_config
from ..utils.logging import get_logger
from .models import FeedItem, Trend, TrendAnalysis

logger = get_logger(__name__)


class TrendAnalyzer:
    """
    Analyzes feed items to identify trending topics.

    Uses Claude to extract and score trends from news articles.
    """

    # Maximum articles to include in a single analysis prompt
    MAX_ARTICLES_PER_ANALYSIS = 100

    # System message for trend analysis
    SYSTEM_MESSAGE = """You are an expert trend analyst specializing in technology,
cryptocurrency, and Web3 industries. Your task is to identify the most significant
trending topics from news headlines and summaries.

Focus on:
1. Topics that appear across multiple sources
2. Emerging technologies and protocols
3. Market-moving events and announcements
4. Regulatory developments
5. Major product launches or updates

Prioritize trends with:
- High relevance to Web3/blockchain ecosystem
- Potential for building micro-services or tools
- Clear user needs or pain points
- Technical feasibility for small teams"""

    def __init__(
        self,
        claude: ClaudeProvider | None = None,
        config: Config | None = None,
        dry_run: bool = False,
    ):
        """
        Initialize trend analyzer.

        Args:
            claude: Claude provider for LLM analysis.
            config: Configuration object.
            dry_run: If True, skip LLM calls and return mock data.
        """
        self._claude = claude
        self.config = config or load_config()
        self.dry_run = dry_run

    @property
    def claude(self) -> ClaudeProvider:
        """Lazy-loaded Claude provider."""
        if self._claude is None:
            self._claude = create_claude_provider(dry_run=self.dry_run)
        return self._claude

    def analyze_trends(
        self,
        items: list[FeedItem],
        period: str,
        max_trends: int = 10,
    ) -> TrendAnalysis:
        """
        Analyze feed items to identify trends.

        Args:
            items: List of feed items to analyze.
            period: Time period being analyzed (24h, 1w, 1m).
            max_trends: Maximum number of trends to identify.

        Returns:
            TrendAnalysis containing identified trends.
        """
        if not items:
            logger.warning(f"[{period}] No items to analyze - returning empty analysis")
            return TrendAnalysis(
                date=datetime.utcnow(),
                period=period,
                trends=[],
                raw_article_count=0,
                sources_analyzed=[],
            )

        analysis_items = items[: self.MAX_ARTICLES_PER_ANALYSIS]
        sources = list({item.source for item in analysis_items})
        categories = list({item.category for item in analysis_items})

        logger.info(
            f"[{period}] Analyzing {len(analysis_items)} items from {len(sources)} sources: {sources}"
        )

        if self.dry_run:
            logger.info(f"[{period}] [DRY RUN] Skipping Claude API call")
            return self._create_mock_analysis(analysis_items, period, sources, categories)

        prompt = self._build_analysis_prompt(analysis_items, period, max_trends)
        logger.info(f"[{period}] Sending prompt to Claude ({len(prompt)} chars)")

        try:
            response = self.claude.chat(
                user_message=prompt,
                system_message=self.SYSTEM_MESSAGE,
            )

            response_len = len(response) if response else 0
            logger.info(f"[{period}] Claude response received: {response_len} chars")

            if not response or not response.strip():
                logger.error(f"[{period}] Empty response from Claude! repr={repr(response)}")
                return TrendAnalysis(
                    date=datetime.utcnow(),
                    period=period,
                    trends=[],
                    raw_article_count=len(analysis_items),
                    sources_analyzed=sources,
                    categories_analyzed=categories,
                )

            if response_len < 100:
                logger.warning(f"[{period}] Suspiciously short response: {response}")

            trends = self._parse_trends_response(response, period)
            logger.info(f"[{period}] Parsed {len(trends)} trends successfully")

            if len(trends) == 0:
                logger.warning(f"[{period}] No trends parsed! Response preview: {response[:500]}")

            return TrendAnalysis(
                date=datetime.utcnow(),
                period=period,
                trends=trends,
                raw_article_count=len(analysis_items),
                sources_analyzed=sources,
                categories_analyzed=categories,
            )

        except Exception as e:
            logger.error(f"[{period}] Trend analysis exception: {type(e).__name__}: {e}")
            import traceback

            logger.error(f"[{period}] Traceback: {traceback.format_exc()}")
            return TrendAnalysis(
                date=datetime.utcnow(),
                period=period,
                trends=[],
                raw_article_count=len(analysis_items),
                sources_analyzed=sources,
                categories_analyzed=categories,
            )

    def _build_analysis_prompt(
        self,
        items: list[FeedItem],
        period: str,
        max_trends: int,
    ) -> str:
        """
        Build the analysis prompt with grouped headlines.

        Args:
            items: Feed items to include.
            period: Time period label.
            max_trends: Maximum trends to request.

        Returns:
            Formatted prompt string.
        """
        # Group items by category
        grouped: dict[str, list[FeedItem]] = {}
        for item in items:
            if item.category not in grouped:
                grouped[item.category] = []
            grouped[item.category].append(item)

        # Build headlines section
        headlines_parts = []
        for category, category_items in grouped.items():
            headlines_parts.append(f"\n### {category.upper()}")
            for item in category_items[:20]:  # Limit per category
                summary_preview = (
                    item.summary[:100] + "..." if len(item.summary) > 100 else item.summary
                )
                headlines_parts.append(f"- [{item.source}] {item.title}\n  {summary_preview}")

        headlines_text = "\n".join(headlines_parts)

        # Map period to human-readable
        period_labels = {
            "24h": "last 24 hours",
            "1w": "past week",
            "1m": "past month",
        }
        period_label = period_labels.get(period, period)

        return f"""Analyze these {period_label} news headlines to identify the top {max_trends} trending topics.

## Headlines by Category
{headlines_text}

## Instructions
Identify the most significant trends from these headlines. For each trend:
1. Provide a concise topic name (3-5 words)
2. List relevant keywords
3. Explain why it's trending
4. Assess its relevance to Web3/blockchain
5. Suggest potential project ideas

Respond with a JSON object in this exact format:
```json
{{
  "trends": [
    {{
      "topic": "AI Agent Frameworks Surge",
      "keywords": ["agents", "autonomous", "LLM", "orchestration"],
      "summary": "Multiple major announcements of AI agent frameworks...",
      "category": "ai",
      "score": 8.5,
      "article_count": 12,
      "sources": ["TechCrunch", "Hacker News"],
      "sample_headlines": ["OpenAI Releases Agent SDK", "LangChain 2.0 Announced"],
      "web3_relevance": "AI agents can automate DeFi operations, DAO governance...",
      "idea_seeds": ["On-chain AI agent marketplace", "Autonomous trading bots"]
    }}
  ]
}}
```

Focus on actionable insights and Web3 opportunities."""

    def _parse_trends_response(
        self,
        response: str,
        period: str,
    ) -> list[Trend]:
        """
        Parse Claude's response into Trend objects.

        Args:
            response: Raw response from Claude.
            period: Time period for the analysis.

        Returns:
            List of Trend objects.
        """
        trends = []

        # Debug: Log raw response length and preview
        logger.debug(f"Raw response length: {len(response)} chars")
        if len(response) < 500:
            logger.debug(f"Full response: {response}")
        else:
            logger.debug(f"Response preview (first 500 chars): {response[:500]}...")

        try:
            # Extract JSON from response
            json_match = re.search(r"```json\s*(.*?)\s*```", response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                logger.debug(f"Found JSON in code block, length: {len(json_str)} chars")
            else:
                # Try to find raw JSON
                logger.debug("No JSON code block found, trying to parse raw response")
                json_str = response

            # Debug: Log JSON string preview before parsing
            if len(json_str) < 200:
                logger.debug(f"JSON to parse: {json_str}")
            else:
                logger.debug(f"JSON preview (first 200 chars): {json_str[:200]}...")

            data = json.loads(json_str)

            if "trends" not in data:
                logger.warning("Response missing 'trends' key")
                return trends

            for trend_data in data["trends"]:
                try:
                    trend = Trend(
                        topic=trend_data.get("topic", "Unknown"),
                        keywords=trend_data.get("keywords", []),
                        score=float(trend_data.get("score", 5.0)),
                        time_period=period,
                        sources=trend_data.get("sources", []),
                        article_count=int(trend_data.get("article_count", 0)),
                        sample_headlines=trend_data.get("sample_headlines", []),
                        category=trend_data.get("category", "general"),
                        summary=trend_data.get("summary", ""),
                        web3_relevance=trend_data.get("web3_relevance", ""),
                        idea_seeds=trend_data.get("idea_seeds", []),
                    )
                    trends.append(trend)
                except (KeyError, ValueError, TypeError) as e:
                    logger.warning(f"Failed to parse trend: {e}")
                    continue

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse trends JSON: {e}")
            logger.error(f"JSON parse error at position {e.pos}: {e.msg}")
            # Show context around the error position
            if hasattr(e, "doc") and e.doc:
                start = max(0, e.pos - 50)
                end = min(len(e.doc), e.pos + 50)
                logger.error(f"Context around error: ...{e.doc[start:end]}...")
            # Try to extract trends from plain text as fallback
            logger.info("Attempting fallback text parsing...")
            trends = self._parse_trends_fallback(response, period)

        return sorted(trends, key=lambda t: t.score, reverse=True)

    def _parse_trends_fallback(
        self,
        response: str,
        period: str,
    ) -> list[Trend]:
        """
        Fallback parsing when JSON parsing fails.

        Attempts to extract trends from structured text.
        """
        trends = []

        # Look for numbered trends
        trend_pattern = r"(?:^|\n)\d+\.\s*\*?\*?([^*\n]+)\*?\*?"
        matches = re.findall(trend_pattern, response)

        for i, topic in enumerate(matches[:10]):
            topic = topic.strip()
            if topic:
                trends.append(
                    Trend(
                        topic=topic,
                        keywords=[],
                        score=10.0 - i,  # Decreasing score by position
                        time_period=period,
                        sources=[],
                        article_count=0,
                        sample_headlines=[],
                        category="general",
                        summary="(Parsed from text fallback)",
                        web3_relevance="",
                        idea_seeds=[],
                    )
                )

        return trends

    def _create_mock_analysis(
        self,
        items: list[FeedItem],
        period: str,
        sources: list[str],
        categories: list[str],
    ) -> TrendAnalysis:
        """Create mock analysis for dry run mode."""
        mock_trends = [
            Trend(
                topic="Mock AI Trend",
                keywords=["ai", "llm", "agents"],
                score=9.0,
                time_period=period,
                sources=sources[:3],
                article_count=len(items),
                sample_headlines=["Mock headline 1", "Mock headline 2"],
                category="ai",
                summary="This is a mock trend for testing purposes.",
                web3_relevance="Could be integrated with blockchain for transparency.",
                idea_seeds=["Mock idea 1", "Mock idea 2"],
            ),
            Trend(
                topic="Mock Crypto Trend",
                keywords=["defi", "protocol", "token"],
                score=8.5,
                time_period=period,
                sources=sources[:2],
                article_count=len(items) // 2,
                sample_headlines=["Mock crypto headline"],
                category="crypto",
                summary="Another mock trend for testing.",
                web3_relevance="Directly related to Web3.",
                idea_seeds=["Mock DeFi idea"],
            ),
        ]

        return TrendAnalysis(
            date=datetime.utcnow(),
            period=period,
            trends=mock_trends,
            raw_article_count=len(items),
            sources_analyzed=sources,
            categories_analyzed=categories,
        )

    def analyze_all_periods(
        self,
        items: list[FeedItem],
    ) -> dict[str, TrendAnalysis]:
        """
        Analyze trends across all configured time periods.

        Args:
            items: All fetched feed items.

        Returns:
            Dictionary mapping period to TrendAnalysis.
        """
        from .feeds import FeedFetcher

        fetcher = FeedFetcher(self.config)
        results: dict[str, TrendAnalysis] = {}

        periods = self.config.get("trends", "periods", default=["24h", "1w", "1m"])

        for period in periods:
            filtered_items = fetcher.filter_by_period(items, period)
            analysis = self.analyze_trends(filtered_items, period)
            results[period] = analysis
            logger.info(
                f"Analyzed {period}: {len(analysis.trends)} trends from "
                f"{analysis.raw_article_count} articles"
            )

        return results
