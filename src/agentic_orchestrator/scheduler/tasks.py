"""
Scheduled task implementations.

These tasks are executed by PM2 on a schedule.
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta
from typing import Optional, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def _calculate_time_decay(collected_at: datetime, now: datetime = None) -> float:
    """
    Calculate time decay factor for signal scoring.

    Decay schedule (v0.5.0):
    - 0-1 hours: 100% weight
    - 1-6 hours: 90% weight
    - 6-12 hours: 80% weight
    - 12-24 hours: 60% weight
    - 24-48 hours: 40% weight
    - 48+ hours: 20% weight

    Args:
        collected_at: When the signal was collected
        now: Current time (defaults to UTC now)

    Returns:
        Decay factor between 0.2 and 1.0
    """
    if now is None:
        now = datetime.utcnow()

    age_hours = (now - collected_at).total_seconds() / 3600

    if age_hours <= 1:
        return 1.0
    elif age_hours <= 6:
        return 0.9
    elif age_hours <= 12:
        return 0.8
    elif age_hours <= 24:
        return 0.6
    elif age_hours <= 48:
        return 0.4
    else:
        return 0.2


def _apply_time_decay_to_signals(signals: List, now: datetime = None) -> List:
    """
    Apply time decay weighting to signal scores.

    Modifies signals in-place by adding a 'decay_factor' attribute
    and adjusting their effective score.

    Args:
        signals: List of signal objects with collected_at attribute
        now: Current time (defaults to UTC now)

    Returns:
        Signals with decay factor applied
    """
    if now is None:
        now = datetime.utcnow()

    for signal in signals:
        collected_at = signal.collected_at or now
        decay = _calculate_time_decay(collected_at, now)

        # Store decay factor in metadata if possible
        if hasattr(signal, 'metadata') and isinstance(signal.metadata, dict):
            signal.metadata['time_decay'] = decay
        elif hasattr(signal, 'extra_metadata') and isinstance(signal.extra_metadata, dict):
            signal.extra_metadata['time_decay'] = decay

        # Apply decay to score if it exists
        if hasattr(signal, 'score') and signal.score is not None:
            original_score = signal.score
            signal.score = original_score * decay

            logger.debug(
                f"Time decay applied: {signal.title[:50]}... "
                f"(original: {original_score:.2f}, decay: {decay:.2f}, final: {signal.score:.2f})"
            )

    return signals


async def _ensure_bilingual(text: str) -> tuple[str, Optional[str]]:
    """
    Ensure text is available in both English and Korean.

    Uses ContentTranslator for bidirectional translation:
    - Korean text -> translates to English, keeps Korean
    - English text -> keeps English, translates to Korean

    Returns:
        Tuple of (english_text, korean_text)
    """
    if not text or len(text.strip()) < 5:
        return (text or "", None)

    try:
        from ..translation.translator import ContentTranslator

        translator = ContentTranslator()
        english_text, korean_text = await translator.ensure_bilingual(text)
        return (english_text or text, korean_text)

    except Exception as e:
        logger.warning(f"Translation failed for text: {text[:50]}... Error: {e}")

    return (text, None)


async def _signal_collect_async():
    """Async implementation of signal collection."""
    from ..signals import SignalAggregator, SignalStorage

    logger.info("=" * 60)
    logger.info("Starting signal collection cycle")
    logger.info("=" * 60)

    start_time = datetime.utcnow()

    try:
        # Initialize aggregator (uses default adapters internally)
        aggregator = SignalAggregator()
        storage = SignalStorage()

        # Fetch and score signals from all adapters
        # Note: collect_all() handles fetching, scoring, and saving to DB
        logger.info("Fetching signals from all adapters...")
        signals = await aggregator.collect_all(save_to_db=True, deduplicate=True)
        logger.info(f"Collected {len(signals)} signals")

        # Cleanup old signals
        logger.info("Cleaning up old signals...")
        deleted_count = storage.cleanup_old_signals(days=30)
        logger.info(f"Deleted {deleted_count} old signals")

        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"Signal collection completed in {duration:.1f}s")
        logger.info(f"Summary: {len(signals)} collected, {deleted_count} old signals deleted")

    except Exception as e:
        logger.error(f"Signal collection failed: {e}", exc_info=True)
        raise


def signal_collect():
    """Collect signals from all adapters."""
    asyncio.run(_signal_collect_async())


async def _analyze_trends_async():
    """Async implementation of trend analysis from signals."""
    import uuid
    from ..trends import TrendAnalyzer
    from ..trends.models import FeedItem
    from ..llm import HybridLLMRouter
    from ..db import get_database, TrendRepository, SignalRepository

    logger.info("=" * 60)
    logger.info("Starting trend analysis cycle")
    logger.info("=" * 60)

    start_time = datetime.utcnow()

    try:
        # Initialize components
        router = HybridLLMRouter()
        analyzer = TrendAnalyzer(router=router)
        db = get_database()
        session = db.get_session()
        signal_repo = SignalRepository(session)
        trend_repo = TrendRepository(session)

        # Get recent signals (last 48 hours)
        logger.info("Fetching recent signals...")
        signals = signal_repo.get_recent(hours=48, limit=200)
        logger.info(f"Found {len(signals)} signals to analyze")

        if not signals:
            logger.warning("No signals found for trend analysis")
            return

        # Apply time decay weighting to signals (v0.5.0)
        now = datetime.utcnow()
        signals = _apply_time_decay_to_signals(signals, now)
        logger.info(f"Applied time decay to {len(signals)} signals")

        # Log decay distribution
        decay_buckets = {'fresh': 0, 'recent': 0, 'moderate': 0, 'old': 0}
        for s in signals:
            decay = s.metadata.get('time_decay', 1.0) if hasattr(s, 'metadata') and isinstance(s.metadata, dict) else 1.0
            if decay >= 0.9:
                decay_buckets['fresh'] += 1
            elif decay >= 0.6:
                decay_buckets['recent'] += 1
            elif decay >= 0.4:
                decay_buckets['moderate'] += 1
            else:
                decay_buckets['old'] += 1
        logger.info(f"Signal freshness: {decay_buckets}")

        # Convert signals to FeedItem format
        feed_items = []
        for s in signals:
            feed_items.append(FeedItem(
                title=s.title or "",
                link=s.url or "",
                summary=s.summary or "",
                source=s.source or "unknown",
                category=s.category or "other",
                published=s.collected_at or datetime.utcnow(),
            ))

        logger.info(f"Converted {len(feed_items)} signals to FeedItems")

        # Analyze trends for 24h period (most relevant for current signals)
        logger.info("Analyzing 24h trends...")
        analysis = await analyzer.analyze_trends(feed_items, "24h", max_trends=10)

        # Save trends to database with bilingual content
        saved_count = 0
        for trend in analysis.trends:
            try:
                # Ensure bilingual content (English main field, Korean *_ko field)
                name_en, name_ko = await _ensure_bilingual(trend.topic)
                desc_en, description_ko = await _ensure_bilingual(trend.summary)

                trend_repo.create({
                    'id': str(uuid.uuid4())[:8],
                    'period': trend.time_period,
                    'name': name_en or trend.topic,
                    'name_ko': name_ko,
                    'description': desc_en or trend.summary,
                    'description_ko': description_ko,
                    'score': trend.score,
                    'signal_count': trend.article_count,
                    'category': trend.category,
                    'keywords': trend.keywords,
                    'analysis_data': {
                        'web3_relevance': trend.web3_relevance,
                        'idea_seeds': trend.idea_seeds,
                        'sources': trend.sources,
                        'sample_headlines': trend.sample_headlines,
                    },
                    'analyzed_at': datetime.utcnow(),
                })
                saved_count += 1
            except Exception as e:
                logger.warning(f"Failed to save trend '{trend.topic}': {e}")

        session.commit()
        logger.info(f"Saved {saved_count} trends to database")

        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"Trend analysis completed in {duration:.1f}s")
        logger.info(f"Summary: {len(signals)} signals analyzed, {saved_count} trends identified")

    except Exception as e:
        logger.error(f"Trend analysis failed: {e}", exc_info=True)
        raise


def analyze_trends():
    """Analyze trends from recent signals."""
    asyncio.run(_analyze_trends_async())


def _generate_debate_topic(signals: list) -> str:
    """Generate a focused, descriptive debate topic from signal themes.

    Analyzes signal titles and sources to create a specific, actionable topic.
    """
    if not signals:
        return "Mossland 생태계 확장을 위한 AI 에이전트 및 DeFi 통합 전략 수립"

    # Category keywords for topic generation with action verbs
    category_themes = {
        'defi': {
            'name': 'DeFi',
            'keywords': ['tvl', 'yield', 'liquidity', 'swap', 'lending', 'aave', 'uniswap', 'compound', 'curve', 'staking', 'protocol'],
            'actions': ['수익률 최적화', '유동성 공급', '프로토콜 통합', '리스크 관리']
        },
        'nft': {
            'name': 'NFT/메타버스',
            'keywords': ['nft', 'metaverse', 'opensea', 'blur', 'collection', 'mint', 'digital asset', 'virtual'],
            'actions': ['자산 가치화', 'NFT 유틸리티 확장', '메타버스 연동', '크리에이터 경제']
        },
        'market': {
            'name': '시장 분석',
            'keywords': ['price', 'bitcoin', 'btc', 'eth', 'market', 'trading', 'volume', 'bull', 'bear'],
            'actions': ['투자 전략', '시장 대응', '포트폴리오 최적화', '리스크 헤지']
        },
        'regulation': {
            'name': '규제/컴플라이언스',
            'keywords': ['regulation', 'sec', 'law', 'policy', 'government', 'ban', 'legal', 'compliance'],
            'actions': ['규제 대응', '컴플라이언스 강화', '리스크 완화', '투명성 확보']
        },
        'gaming': {
            'name': '게임/GameFi',
            'keywords': ['game', 'gaming', 'play', 'p2e', 'earn', 'esports', 'player'],
            'actions': ['P2E 모델 혁신', '게임 이코노미 설계', '사용자 경험 개선', '커뮤니티 성장']
        },
        'ai': {
            'name': 'AI/자동화',
            'keywords': ['ai', 'artificial', 'machine', 'learning', 'gpt', 'llm', 'agent', 'automation', 'model'],
            'actions': ['AI 에이전트 개발', '자동화 시스템 구축', '지능형 서비스', '데이터 분석']
        },
        'dao': {
            'name': 'DAO/거버넌스',
            'keywords': ['dao', 'governance', 'vote', 'proposal', 'treasury', 'community', 'decentralized'],
            'actions': ['거버넌스 개선', '커뮤니티 참여 확대', '의사결정 최적화', '투명성 강화']
        },
        'security': {
            'name': '보안',
            'keywords': ['security', 'hack', 'exploit', 'audit', 'vulnerability', 'protection'],
            'actions': ['보안 강화', '스마트 컨트랙트 감사', '위협 탐지', '자산 보호']
        },
    }

    # Collect all text for analysis
    all_text = ' '.join([s.title.lower() for s in signals if s.title])

    # Find dominant theme with scoring
    theme_scores = {}
    for theme_key, theme_data in category_themes.items():
        score = sum(1 for kw in theme_data['keywords'] if kw in all_text)
        if score > 0:
            theme_scores[theme_key] = (theme_data, score)

    # Get top theme
    if theme_scores:
        top_theme_key, (theme_data, _) = max(theme_scores.items(), key=lambda x: x[1][1])
        theme_name = theme_data['name']
        action = theme_data['actions'][0]  # Primary action

        # Extract key entity from highest scored signal
        top_signal = signals[0]

        # Extract meaningful phrases
        title = top_signal.title or ""
        # Remove common prefixes and get core content
        title_clean = title.replace(':', ' - ').replace('|', ' - ')
        title_parts = [p.strip() for p in title_clean.split(' - ') if len(p.strip()) > 5]

        if title_parts:
            # Use the most informative part
            key_entity = max(title_parts[:2], key=len)[:60] if title_parts else ''

            # Generate descriptive topic
            return f"[{theme_name}] {key_entity}에 대한 Mossland의 {action} 전략 및 구체적 실행 방안"
        else:
            return f"[{theme_name}] 최신 트렌드 기반 Mossland {action} 전략 - MVP 개발 방향 논의"

    # Fallback: use top signal's source and create actionable topic
    top_signal = signals[0]
    source = getattr(top_signal, 'source', 'MARKET').upper() if hasattr(top_signal, 'source') else 'MARKET'
    title_short = (top_signal.title or '시장 동향')[:50]

    return f"[{source}] {title_short} - Mossland 생태계 연동 및 신규 서비스 개발 방안"


async def _auto_score_and_save_ideas(
    router,
    ideas: list,
    topic: str,
    context: str,
    debate_session_id: str,
    db_session,
    final_plan_content: Optional[str] = None,
    promote_threshold: float = 7.0,
    archive_threshold: float = 4.0,
    max_per_cycle: int = 3,
):
    """
    Auto-score debate ideas and save them to the ideas table.

    Also creates GitHub Issues for tracking.
    Includes Korean translation for all saved ideas and plans.
    For high-scoring plans, triggers automatic project generation.

    Args:
        router: HybridLLMRouter for scoring
        ideas: List of ideas from debate result
        topic: Debate topic (for context)
        context: Debate context
        debate_session_id: ID of the debate session
        db_session: SQLAlchemy session
        final_plan_content: Final plan content from debate (for project generation)
        promote_threshold: Score threshold for auto-promotion
        archive_threshold: Score below which to archive
        max_per_cycle: Maximum ideas to promote per cycle
    """
    import uuid
    from ..scoring import IdeaScorer
    from ..db import IdeaRepository, PlanRepository
    from ..translation import ContentTranslator

    logger.info("=" * 40)
    logger.info("Starting auto-scoring for debate ideas")
    logger.info("=" * 40)

    scorer = IdeaScorer(
        router=router,
        promote_threshold=promote_threshold,
        archive_threshold=archive_threshold,
    )
    idea_repo = IdeaRepository(db_session)
    plan_repo = PlanRepository(db_session)
    translator = ContentTranslator(router=router)

    # Initialize GitHub client (optional - won't fail if not configured)
    github_client = None
    try:
        from ..github_client import GitHubClient, Labels
        github_client = GitHubClient()
        logger.info("GitHub integration enabled")
    except Exception as e:
        logger.warning(f"GitHub integration disabled: {e}")

    promoted_count = 0
    archived_count = 0
    pending_count = 0

    for idea in ideas:
        try:
            # Build idea content string
            idea_title = getattr(idea, 'title', str(idea)[:100])
            idea_content = getattr(idea, 'content', getattr(idea, 'description', str(idea)))
            idea_summary = idea_content[:500] if idea_content else idea_title

            # Score the idea
            score_context = f"토론 주제: {topic}\n\n{context[:500]}"
            score, decision = await scorer.score_and_decide(
                idea_content=f"제목: {idea_title}\n내용: {idea_content}",
                context=score_context,
            )

            # Create idea in database
            idea_id = str(uuid.uuid4())[:8]
            status = 'pending'

            if decision == 'promote' and promoted_count < max_per_cycle:
                status = 'promoted'
                promoted_count += 1
                logger.info(f"Auto-promoting: {idea_title[:50]}... (score: {score.total:.1f})")
            elif decision == 'archive':
                status = 'archived'
                archived_count += 1
                logger.info(f"Archived: {idea_title[:50]}... (score: {score.total:.1f})")
            else:
                status = 'scored'
                pending_count += 1
                logger.info(f"Scored (pending): {idea_title[:50]}... (score: {score.total:.1f})")

            # Create GitHub Issue for the idea (if GitHub is configured)
            github_issue_url = None
            github_issue_id = None
            if github_client:
                try:
                    # Build issue body
                    issue_body = f"""## Idea Summary
{idea_summary}

## Auto-Score Results
- **Total Score**: {score.total:.1f}/10
- **Feasibility**: {score.feasibility:.1f}/10
- **Relevance**: {score.relevance:.1f}/10
- **Novelty**: {score.novelty:.1f}/10
- **Impact**: {score.impact:.1f}/10

## Decision: {decision.upper()}

## Context
**Debate Topic**: {topic}
**Debate Session**: {debate_session_id}

---
*Auto-generated by MOSS.AO Orchestrator*
"""
                    # Determine labels based on status
                    issue_labels = [Labels.TYPE_IDEA, Labels.GENERATED_BY_ORCHESTRATOR]
                    if status == 'promoted':
                        issue_labels.append(Labels.PROMOTE_TO_PLAN)
                    elif status == 'archived':
                        issue_labels.append('archived')
                    else:
                        issue_labels.append(Labels.STATUS_BACKLOG)

                    issue = github_client.create_issue(
                        title=f"[Idea] {idea_title[:100]}",
                        body=issue_body,
                        labels=issue_labels,
                    )
                    github_issue_url = issue.html_url
                    github_issue_id = issue.number
                    logger.info(f"Created GitHub Issue #{issue.number} for idea: {idea_title[:50]}...")
                except Exception as e:
                    logger.warning(f"Failed to create GitHub Issue for idea: {e}")

            # Translate idea fields (bilingual: detect language, provide both EN and KO)
            try:
                logger.info(f"Processing bilingual translation for idea: {idea_title[:50]}...")
                # ensure_bilingual returns (english, korean) tuple
                title_en, title_ko = await translator.ensure_bilingual(idea_title[:500])
                summary_en, summary_ko = await translator.ensure_bilingual(idea_summary)
                if idea_content:
                    desc_en, desc_ko = await translator.ensure_bilingual(idea_content)
                else:
                    desc_en, desc_ko = None, None
            except Exception as e:
                logger.warning(f"Bilingual translation failed for idea: {e}")
                # Fallback: use original content for both fields
                title_en, title_ko = idea_title[:500], idea_title[:500]
                summary_en, summary_ko = idea_summary, idea_summary
                desc_en, desc_ko = idea_content, idea_content

            # Save idea to database (main fields: English, *_ko fields: Korean)
            db_idea = idea_repo.create({
                'id': idea_id,
                'title': title_en or idea_title[:500],
                'title_ko': title_ko or idea_title[:500],
                'summary': summary_en or idea_summary,
                'summary_ko': summary_ko or idea_summary,
                'description': desc_en or idea_content,
                'description_ko': desc_ko or idea_content,
                'source_type': 'debate',
                'debate_session_id': debate_session_id,
                'status': status,
                'score': score.total,
                'github_issue_id': github_issue_id,
                'github_issue_url': github_issue_url,
                'extra_metadata': {
                    'auto_score': score.to_dict(),
                    'debate_topic': topic,
                },
            })

            # If promoted, create a draft plan
            if status == 'promoted':
                plan_github_url = None
                plan_github_id = None

                # Create GitHub Issue for the plan
                if github_client:
                    try:
                        plan_body = f"""## Plan for: {idea_title}

### Source Idea
{idea_summary}

### Auto-Promotion Details
- **Idea Score**: {score.total:.1f}/10
- **Auto-promoted**: Yes (score >= {promote_threshold})

### Idea Issue
{f'Related to #{github_issue_id}' if github_issue_id else 'No linked issue'}

---
*Auto-generated by MOSS.AO Orchestrator*
"""
                        plan_labels = [Labels.TYPE_PLAN, Labels.GENERATED_BY_ORCHESTRATOR, Labels.STATUS_BACKLOG]
                        plan_issue = github_client.create_issue(
                            title=f"[Plan] {idea_title[:100]}",
                            body=plan_body,
                            labels=plan_labels,
                        )
                        plan_github_url = plan_issue.html_url
                        plan_github_id = plan_issue.number
                        logger.info(f"Created GitHub Issue #{plan_issue.number} for plan")
                    except Exception as e:
                        logger.warning(f"Failed to create GitHub Issue for plan: {e}")

                try:
                    # Translate plan title (bilingual)
                    plan_title_original = f"Plan: {idea_title[:200]}"
                    try:
                        plan_title_en, plan_title_ko = await translator.ensure_bilingual(plan_title_original)
                    except Exception as e:
                        logger.warning(f"Plan title translation failed: {e}")
                        plan_title_en, plan_title_ko = plan_title_original, plan_title_original

                    plan_id = str(uuid.uuid4())[:8]

                    # Determine plan status based on score
                    # High-scoring plans (>= 8.0) are auto-approved for project generation
                    project_config = _load_project_config()
                    auto_gen_min_score = project_config.get("auto_generate", {}).get("min_score", 8.0)
                    plan_status = 'approved' if score.total >= auto_gen_min_score else 'draft'

                    # Translate final_plan content if available
                    plan_final_content_en = final_plan_content
                    plan_final_content_ko = None
                    if final_plan_content:
                        try:
                            plan_final_content_en, plan_final_content_ko = await translator.ensure_bilingual(final_plan_content)
                        except Exception as e:
                            logger.warning(f"Final plan translation failed: {e}")
                            plan_final_content_en = final_plan_content

                    plan_repo.create({
                        'id': plan_id,
                        'idea_id': idea_id,
                        'debate_session_id': debate_session_id,
                        'title': plan_title_en or plan_title_original,
                        'title_ko': plan_title_ko or plan_title_original,
                        'version': 1,
                        'status': plan_status,
                        'final_plan': plan_final_content_en,
                        'final_plan_ko': plan_final_content_ko,
                        'github_issue_id': plan_github_id,
                        'github_issue_url': plan_github_url,
                        'extra_metadata': {
                            'auto_promoted': True,
                            'promotion_score': score.total,
                            'auto_approved': plan_status == 'approved',
                        },
                    })
                    logger.info(f"Created {plan_status} plan for promoted idea: {idea_id} (score: {score.total:.1f})")
                    if plan_final_content_en:
                        logger.info(f"Plan includes final_plan content: {len(plan_final_content_en)} chars")

                    # Auto-generate project for high-scoring plans
                    if plan_status == 'approved':
                        logger.info(f"Plan score {score.total:.1f} >= {auto_gen_min_score}, triggering auto project generation")
                        try:
                            await _auto_generate_project(
                                plan_id=plan_id,
                                plan_score=score.total,
                                router=router,
                                db_session=db_session,
                            )
                        except Exception as e:
                            logger.warning(f"Auto project generation failed for plan {plan_id}: {e}")
                            # Don't fail the whole process if project generation fails

                except Exception as e:
                    logger.warning(f"Failed to create plan for idea {idea_id}: {e}")

        except Exception as e:
            logger.warning(f"Failed to score/save idea: {e}")
            continue

    db_session.commit()

    # Cleanup GitHub client
    if github_client:
        try:
            github_client.close()
        except Exception:
            pass

    logger.info(f"Auto-scoring complete: {promoted_count} promoted, {archived_count} archived, {pending_count} pending")
    if github_client:
        logger.info("GitHub Issues created for all processed ideas")


def _load_project_config() -> dict:
    """Load project generation configuration from config.yaml."""
    import yaml
    from pathlib import Path

    config_path = Path(__file__).parent.parent.parent.parent / "config.yaml"
    default_config = {
        "auto_generate": {
            "enabled": True,
            "min_score": 8.0,
            "max_concurrent": 1,
        },
        "llm": {
            "parsing": "glm-4.7-flash",
            "code_generation": "qwen2.5:32b",
            "architecture": "llama3.3:70b",
            "fallback": "phi4:14b",
        },
        "output_dir": "projects",
    }

    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
            project_config = config.get("project", {})
            # Merge with defaults
            for key, value in default_config.items():
                if key not in project_config:
                    project_config[key] = value
                elif isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        if sub_key not in project_config[key]:
                            project_config[key][sub_key] = sub_value
            return project_config
    except Exception as e:
        logger.warning(f"Failed to load project config, using defaults: {e}")
        return default_config


async def _auto_generate_project(
    plan_id: str,
    plan_score: float,
    router,
    db_session,
) -> bool:
    """
    Automatically generate a project from a high-scoring plan.

    Args:
        plan_id: ID of the plan
        plan_score: Score of the plan (for logging)
        router: HybridLLMRouter for LLM calls
        db_session: SQLAlchemy session

    Returns:
        True if project was generated successfully
    """
    from ..project import ProjectScaffold
    from ..db import ProjectRepository, PlanRepository

    # Load project config
    project_config = _load_project_config()
    auto_config = project_config.get("auto_generate", {})

    if not auto_config.get("enabled", True):
        logger.info("Auto project generation is disabled in config")
        return False

    min_score = auto_config.get("min_score", 8.0)
    if plan_score < min_score:
        logger.info(f"Plan score {plan_score:.1f} below threshold {min_score}, skipping auto-generation")
        return False

    logger.info("=" * 40)
    logger.info(f"Starting auto project generation for plan: {plan_id}")
    logger.info(f"Plan score: {plan_score:.1f} (threshold: {min_score})")
    logger.info("=" * 40)

    try:
        # Check if project already exists
        project_repo = ProjectRepository(db_session)
        existing = project_repo.get_by_plan(plan_id)
        if existing and existing.status == "ready":
            logger.info(f"Project already exists for plan {plan_id}, skipping")
            return True

        # Update plan status to approved for project generation
        plan_repo = PlanRepository(db_session)
        plan = plan_repo.get_by_id(plan_id)
        if plan and plan.status != "approved":
            plan_repo.update_status(plan_id, "approved")
            db_session.flush()
            logger.info(f"Updated plan status to 'approved' for auto-generation")

        # Generate project
        scaffold = ProjectScaffold(
            router=router,
            projects_dir=project_config.get("output_dir", "projects"),
            db_session=db_session,
        )

        result = await scaffold.generate_project(
            plan_id=plan_id,
            force_regenerate=False,
        )

        if result.success:
            logger.info(f"Project generated successfully: {result.project_path}")
            logger.info(f"Files generated: {result.files_generated}")
            logger.info(f"Tech stack: {result.tech_stack}")
            db_session.commit()
            return True
        else:
            logger.warning(f"Project generation failed: {result.error}")
            return False

    except Exception as e:
        logger.error(f"Auto project generation failed: {e}", exc_info=True)
        return False


def _generate_debate_topic_from_trend(trend) -> tuple[str, str]:
    """Generate debate topic and context from a trend.

    Args:
        trend: Trend object from database

    Returns:
        Tuple of (topic, context)
    """
    # Build topic from trend
    category = trend.category.upper() if trend.category else "TECH"
    topic = f"[{category}] {trend.name} - Mossland 전략적 대응 방안"

    # Build context from trend analysis data
    context_parts = [f"트렌드 요약: {trend.description or trend.name}"]

    analysis_data = trend.analysis_data or {}
    if analysis_data.get('web3_relevance'):
        context_parts.append(f"Web3 관련성: {analysis_data['web3_relevance']}")
    if analysis_data.get('idea_seeds'):
        seeds = analysis_data['idea_seeds']
        if isinstance(seeds, list):
            context_parts.append(f"아이디어 시드: {', '.join(seeds[:5])}")

    keywords = trend.keywords or []
    if keywords:
        context_parts.append(f"주요 키워드: {', '.join(keywords[:10])}")

    context = "\n".join(context_parts)
    return topic, context


def _load_debate_config():
    """Load debate configuration from config.yaml."""
    from ..debate.protocol import DebateProtocolConfig
    import yaml
    from pathlib import Path

    config_path = Path(__file__).parent.parent.parent.parent / "config.yaml"
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
            debate_config = config.get("debate", {})
            test_mode = debate_config.get("test_mode", False)

            if test_mode:
                logger.info("Using TEST MODE debate configuration (reduced agents)")
                settings = debate_config.get("test", {})
            else:
                logger.info("Using NORMAL debate configuration")
                settings = debate_config.get("normal", {})

            return DebateProtocolConfig(
                divergence_rounds=settings.get("divergence_rounds", 3),
                divergence_agents_per_round=settings.get("divergence_agents_per_round", 8),
                convergence_rounds=settings.get("convergence_rounds", 2),
                convergence_agents_per_round=settings.get("convergence_agents_per_round", 4),
                planning_rounds=settings.get("planning_rounds", 2),
                planning_agents_per_round=settings.get("planning_agents_per_round", 5),
            )
    except Exception as e:
        logger.warning(f"Failed to load debate config, using defaults: {e}")
        return DebateProtocolConfig()


async def _run_debate_async(topic: Optional[str] = None):
    """Async implementation of debate execution."""
    from ..llm import HybridLLMRouter
    from ..debate import MultiStageDebate, run_multi_stage_debate
    from ..signals import SignalStorage
    from ..db import get_database, SignalRepository, DebateRepository, TrendRepository

    logger.info("=" * 60)
    logger.info("Starting multi-stage debate cycle")
    logger.info("=" * 60)

    # Load debate configuration
    debate_config = _load_debate_config()
    logger.info(f"Debate config: {debate_config.divergence_agents_per_round} divergence agents/round, "
                f"{debate_config.divergence_rounds} rounds")

    start_time = datetime.utcnow()
    debate_session = None
    db = None
    trend_context = None

    try:
        # Initialize components
        db = get_database()
        session = db.get_session()
        signal_repo = SignalRepository(session)
        debate_repo = DebateRepository(session)
        trend_repo = TrendRepository(session)

        # Get topic from trends first, then fall back to signals
        if not topic:
            # Try to use recent trends first
            logger.info("Checking for recent trends...")
            recent_trends = trend_repo.get_latest(period="24h", limit=5)

            if recent_trends:
                # Use the top trend
                top_trend = recent_trends[0]
                topic, trend_context = _generate_debate_topic_from_trend(top_trend)
                logger.info(f"Using trend-based topic: {topic}")
            else:
                # Fall back to signal-based topic generation
                logger.info("No recent trends found, selecting topic from signals...")
                signals = signal_repo.get_recent(limit=10, min_score=0.7)
                if signals:
                    topic = _generate_debate_topic(signals[:5])
                else:
                    topic = "Mossland 생태계의 다음 분기 전략 방향"

        logger.info(f"Debate topic: {topic}")

        # Build context: use trend context if available, supplement with signals
        if trend_context:
            context = trend_context + "\n\n--- 최근 관련 신호 ---\n"
        else:
            context = ""

        # Add context from recent signals
        context_signals = signal_repo.get_recent(limit=20)
        context += "\n".join([
            f"- [{s.source}] {s.title}: {s.summary[:200] if s.summary else 'No summary'}"
            for s in context_signals
        ])

        # Create debate session in database BEFORE starting
        import uuid
        session_id = str(uuid.uuid4())[:8]
        debate_session = debate_repo.create_session({
            'id': session_id,
            'topic': topic,
            'context': context,
            'phase': 'divergence',
            'round_number': 1,
            'max_rounds': 3,
            'status': 'active',
            'participants': [],
            'started_at': start_time,
        })
        session.commit()
        logger.info(f"Created debate session: {session_id}")

        # Initialize LLM router
        router = HybridLLMRouter()

        # Collect participants during debate
        all_participants = set()

        # Callback for progress logging and saving messages
        def on_message(msg):
            logger.info(f"[{msg.phase.value}] {msg.agent_name}: {msg.message_type.value}")
            all_participants.add(msg.agent_name)
            # Save message to database
            try:
                debate_repo.add_message({
                    'session_id': session_id,
                    'agent_id': msg.agent_id,
                    'agent_name': msg.agent_name,
                    'agent_handle': getattr(msg, 'agent_handle', None),
                    'message_type': msg.message_type.value,
                    'content': msg.content if hasattr(msg, 'content') else '',
                    'token_count': getattr(msg, 'token_count', 0),
                    'model_used': getattr(msg, 'model', None),
                })
            except Exception as e:
                logger.warning(f"Failed to save message: {e}")

        def on_phase_complete(result):
            logger.info(f"Phase {result.phase.value} completed: {result.duration_seconds:.1f}s, ${result.total_cost:.4f}")
            # Update session phase
            try:
                debate_repo.update_session(
                    session_id,
                    phase=result.phase.value,
                    round_number=result.round_number if hasattr(result, 'round_number') else 1,
                    participants=list(all_participants),
                )
                session.commit()
            except Exception as e:
                logger.warning(f"Failed to update session phase: {e}")

        # Run debate
        logger.info("Starting multi-stage debate...")
        result = await run_multi_stage_debate(
            router=router,
            topic=topic,
            context=context,
            config=debate_config,
            on_message=on_message,
            on_phase_complete=on_phase_complete,
        )

        # Save final results to database
        try:
            ideas_data = [idea.to_dict() for idea in result.all_ideas] if result.all_ideas else []
            debate_repo.update_session(
                session_id,
                status='completed',
                phase='planning',
                outcome='completed',
                final_plan=result.final_plan,
                ideas_generated=ideas_data,
                summary=f"Generated {len(result.all_ideas)} ideas, selected {len(result.selected_ideas)}",
                total_tokens=result.total_tokens,
                total_cost=result.total_cost,
                completed_at=datetime.utcnow(),
                participants=list(all_participants),
            )
            session.commit()
            logger.info(f"Saved debate results to database: {session_id}")
        except Exception as e:
            logger.error(f"Failed to save debate results: {e}", exc_info=True)

        # Auto-score and save ideas to ideas table
        if result.all_ideas:
            await _auto_score_and_save_ideas(
                router=router,
                ideas=result.all_ideas,
                topic=topic,
                context=context,
                debate_session_id=session_id,
                db_session=session,
                final_plan_content=result.final_plan,  # Pass final plan for project generation
            )

        # Log results
        logger.info("Debate results summary:")
        logger.info(f"  Session ID: {result.session_id}")
        logger.info(f"  Topic: {result.topic}")
        logger.info(f"  Final plan length: {len(result.final_plan) if result.final_plan else 0} chars")

        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"Debate completed in {duration:.1f}s")
        logger.info(f"Total cost: ${result.total_cost:.4f}")
        logger.info(f"Ideas generated: {len(result.all_ideas)}")
        logger.info(f"Ideas selected: {len(result.selected_ideas)}")

        # Log final plan summary
        if result.final_plan:
            logger.info("Final plan generated successfully")
            logger.info(f"Plan length: {len(result.final_plan)} characters")

    except Exception as e:
        logger.error(f"Debate execution failed: {e}", exc_info=True)
        # Mark session as failed if it was created
        if debate_session and db:
            try:
                session = db.get_session()
                debate_repo = DebateRepository(session)
                debate_repo.update_session(
                    debate_session.id,
                    status='cancelled',
                    outcome='error',
                    summary=f"Error: {str(e)}",
                    completed_at=datetime.utcnow(),
                )
                session.commit()
            except Exception:
                pass
        raise


def run_debate(topic: Optional[str] = None):
    """Run multi-stage debate."""
    asyncio.run(_run_debate_async(topic))


def _process_backlog():
    """Implementation of backlog processing."""
    from ..db import get_database, IdeaRepository, PlanRepository

    logger.info("=" * 60)
    logger.info("Starting backlog processing cycle")
    logger.info("=" * 60)

    start_time = datetime.utcnow()

    try:
        db = get_database()
        idea_repo = IdeaRepository(db.get_session())
        plan_repo = PlanRepository(db.get_session())

        # Get pending ideas
        pending_ideas = idea_repo.get_by_status('pending')
        logger.info(f"Found {len(pending_ideas)} pending ideas")

        # Get approved plans awaiting implementation
        approved_plans = plan_repo.get_by_status('approved')
        logger.info(f"Found {len(approved_plans)} approved plans")

        # Get ideas by status for summary
        idea_counts = idea_repo.count_by_status()
        logger.info(f"Idea status summary: {idea_counts}")

        # Generate report
        stats = {
            'pending_ideas': len(pending_ideas),
            'approved_plans': len(approved_plans),
            'idea_counts': idea_counts,
        }

        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"Backlog processing completed in {duration:.1f}s")
        logger.info(f"Stats: {stats}")

    except Exception as e:
        logger.error(f"Backlog processing failed: {e}", exc_info=True)
        raise


def process_backlog():
    """Process pending backlog items."""
    _process_backlog()


async def _health_check_async():
    """Async implementation of health check."""
    from ..llm import HybridLLMRouter
    from ..db import get_database
    from ..cache import get_cache
    from ..providers.ollama import OllamaProvider

    logger.info("Running system health check...")

    health_status = {
        'timestamp': datetime.utcnow().isoformat(),
        'status': 'healthy',
        'components': {},
    }

    try:
        # Check database
        try:
            db = get_database()
            db.get_session()
            health_status['components']['database'] = {'status': 'healthy'}
            logger.info("Database: healthy")
        except Exception as e:
            health_status['components']['database'] = {'status': 'unhealthy', 'error': str(e)}
            health_status['status'] = 'degraded'
            logger.error(f"Database: unhealthy - {e}")

        # Check cache
        try:
            cache = get_cache()
            cache.set('health_check', 'ok', ttl=60)
            result = cache.get('health_check')
            cache_health = cache.health_check()
            if result == 'ok':
                health_status['components']['cache'] = {
                    'status': 'healthy',
                    'type': cache_health.get('type', 'unknown'),
                }
                logger.info(f"Cache: healthy ({cache_health.get('type', 'unknown')})")
            else:
                health_status['components']['cache'] = {'status': 'degraded'}
                logger.warning("Cache: degraded")
        except Exception as e:
            health_status['components']['cache'] = {'status': 'unhealthy', 'error': str(e)}
            logger.warning(f"Cache: unhealthy - {e}")

        # Check Ollama
        try:
            ollama = OllamaProvider()
            ollama_health = await ollama.health_check()
            if ollama_health.get('status') == 'healthy':
                health_status['components']['ollama'] = {
                    'status': 'healthy',
                    'models': ollama_health.get('models', []),
                }
                logger.info(f"Ollama: healthy ({len(ollama_health.get('models', []))} models)")
            else:
                health_status['components']['ollama'] = {'status': 'degraded'}
                health_status['status'] = 'degraded'
                logger.warning("Ollama: degraded")
        except Exception as e:
            health_status['components']['ollama'] = {'status': 'unhealthy', 'error': str(e)}
            health_status['status'] = 'degraded'
            logger.error(f"Ollama: unhealthy - {e}")

        # Check LLM router
        try:
            router = HybridLLMRouter()
            router_health = await router.health_check()
            health_status['components']['llm_router'] = {
                'status': router_health.get('status', 'unknown'),
                'budget': router_health.get('budget', {}),
            }
            logger.info(f"LLM Router: {router_health.get('status')}")
        except Exception as e:
            health_status['components']['llm_router'] = {'status': 'unhealthy', 'error': str(e)}
            logger.error(f"LLM Router: unhealthy - {e}")

        # Log final status
        logger.info(f"Health check completed: {health_status['status']}")

        # Store health status in cache
        try:
            cache = get_cache()
            cache.set('system_health', health_status, ttl=300)
        except Exception:
            pass

    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        health_status['status'] = 'unhealthy'
        health_status['error'] = str(e)

    return health_status


def health_check():
    """Check system health."""
    result = asyncio.run(_health_check_async())
    if result['status'] != 'healthy':
        sys.exit(1)
