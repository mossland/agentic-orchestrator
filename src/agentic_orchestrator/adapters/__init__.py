"""
Signal adapters for Agentic Orchestrator.

Provides adapters for collecting signals from various sources:
- RSS feeds
- GitHub events
- OnChain data (Ethereum, MOC)
- Social media (Twitter/X, Reddit, Farcaster)
- News APIs
"""

from .base import BaseAdapter, AdapterConfig, AdapterResult
from .rss import RSSAdapter
from .github_events import GitHubEventsAdapter
from .onchain import OnChainAdapter
from .social import SocialMediaAdapter
from .news import NewsAPIAdapter

__all__ = [
    # Base
    "BaseAdapter",
    "AdapterConfig",
    "AdapterResult",
    # Adapters
    "RSSAdapter",
    "GitHubEventsAdapter",
    "OnChainAdapter",
    "SocialMediaAdapter",
    "NewsAPIAdapter",
]
