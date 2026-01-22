"""
Scheduled task implementations.

These tasks are executed by PM2 on a schedule.
"""

import asyncio
import logging
import sys
from datetime import datetime
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


async def _signal_collect_async():
    """Async implementation of signal collection."""
    from ..adapters import (
        RSSAdapter,
        GitHubEventsAdapter,
        OnChainAdapter,
        SocialMediaAdapter,
        NewsAPIAdapter,
    )
    from ..signals import SignalAggregator, SignalScorer, SignalStorage
    from ..db import get_database, SignalRepository
    from ..cache import get_cache

    logger.info("=" * 60)
    logger.info("Starting signal collection cycle")
    logger.info("=" * 60)

    start_time = datetime.utcnow()

    try:
        # Initialize components
        db = get_database()
        cache = get_cache()
        repo = SignalRepository(db.get_session())

        # Initialize adapters
        adapters = [
            RSSAdapter(),
            GitHubEventsAdapter(),
            OnChainAdapter(),
            SocialMediaAdapter(),
            NewsAPIAdapter(),
        ]

        # Create aggregator
        aggregator = SignalAggregator(adapters=adapters)
        scorer = SignalScorer()
        storage = SignalStorage(repo, cache)

        # Fetch signals
        logger.info("Fetching signals from all adapters...")
        signals = await aggregator.fetch_all()
        logger.info(f"Fetched {len(signals)} raw signals")

        # Score signals
        logger.info("Scoring signals for Mossland relevance...")
        scored_signals = scorer.score_batch(signals)
        high_relevance = [s for s in scored_signals if s.get('score', 0) >= 7.0]
        logger.info(f"Found {len(high_relevance)} high-relevance signals")

        # Store signals
        logger.info("Storing signals in database...")
        stored_count = await storage.store_batch(scored_signals)
        logger.info(f"Stored {stored_count} new signals")

        # Cleanup old signals
        logger.info("Cleaning up old signals...")
        deleted_count = await storage.cleanup_old_signals(days=30)
        logger.info(f"Deleted {deleted_count} old signals")

        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"Signal collection completed in {duration:.1f}s")
        logger.info(f"Summary: {len(signals)} fetched, {stored_count} stored, {deleted_count} deleted")

    except Exception as e:
        logger.error(f"Signal collection failed: {e}", exc_info=True)
        raise


def signal_collect():
    """Collect signals from all adapters."""
    asyncio.run(_signal_collect_async())


async def _run_debate_async(topic: Optional[str] = None):
    """Async implementation of debate execution."""
    from ..llm import HybridLLMRouter
    from ..debate import MultiStageDebate, run_multi_stage_debate
    from ..signals import SignalStorage
    from ..db import get_database, SignalRepository, DebateRepository

    logger.info("=" * 60)
    logger.info("Starting multi-stage debate cycle")
    logger.info("=" * 60)

    start_time = datetime.utcnow()

    try:
        # Initialize components
        db = get_database()
        signal_repo = SignalRepository(db.get_session())
        debate_repo = DebateRepository(db.get_session())

        # Get topic from high-relevance signals if not provided
        if not topic:
            logger.info("Selecting topic from recent high-relevance signals...")
            signals = await signal_repo.get_recent_high_relevance(limit=10)
            if signals:
                # Create topic from top signals
                topics = [s.title for s in signals[:3]]
                topic = f"Mossland 생태계 전략 토론: {', '.join(topics)}"
            else:
                topic = "Mossland 생태계의 다음 분기 전략 방향"

        logger.info(f"Debate topic: {topic}")

        # Get context from recent signals
        context_signals = await signal_repo.get_recent(limit=20)
        context = "\n".join([
            f"- [{s.source}] {s.title}: {s.summary[:200] if s.summary else 'No summary'}"
            for s in context_signals
        ])

        # Initialize LLM router
        router = HybridLLMRouter()

        # Callback for progress logging
        def on_message(msg):
            logger.info(f"[{msg.phase.value}] {msg.agent_name}: {msg.message_type.value}")

        def on_phase_complete(result):
            logger.info(f"Phase {result.phase.value} completed: {result.duration_seconds:.1f}s, ${result.total_cost:.4f}")

        # Run debate
        logger.info("Starting multi-stage debate...")
        result = await run_multi_stage_debate(
            router=router,
            topic=topic,
            context=context,
            on_message=on_message,
            on_phase_complete=on_phase_complete,
        )

        # Store results
        logger.info("Storing debate results...")
        await debate_repo.create_from_result(result)

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
        raise


def run_debate(topic: Optional[str] = None):
    """Run multi-stage debate."""
    asyncio.run(_run_debate_async(topic))


async def _process_backlog_async():
    """Async implementation of backlog processing."""
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
        pending_ideas = await idea_repo.get_by_status('pending')
        logger.info(f"Found {len(pending_ideas)} pending ideas")

        # Get approved plans awaiting implementation
        approved_plans = await plan_repo.get_by_status('approved')
        logger.info(f"Found {len(approved_plans)} approved plans")

        # Update stale items
        stale_count = await idea_repo.mark_stale(days=30)
        logger.info(f"Marked {stale_count} stale ideas")

        # Generate report
        stats = {
            'pending_ideas': len(pending_ideas),
            'approved_plans': len(approved_plans),
            'stale_items': stale_count,
        }

        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"Backlog processing completed in {duration:.1f}s")
        logger.info(f"Stats: {stats}")

    except Exception as e:
        logger.error(f"Backlog processing failed: {e}", exc_info=True)
        raise


def process_backlog():
    """Process pending backlog items."""
    asyncio.run(_process_backlog_async())


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
            await cache.set('health_check', 'ok', ttl=60)
            result = await cache.get('health_check')
            if result == 'ok':
                health_status['components']['cache'] = {'status': 'healthy'}
                logger.info("Cache: healthy")
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
            await cache.set('system_health', health_status, ttl=300)
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
