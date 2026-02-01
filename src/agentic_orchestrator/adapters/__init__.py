"""
Signal adapters for Agentic Orchestrator.

Provides adapters for collecting signals from various sources:
- RSS feeds
- GitHub events
- OnChain data (Ethereum, MOC, DEX volume, Whale alerts)
- Social media (Twitter/X, Reddit, Discord)
- Web3 social (Lens Protocol, Farcaster)
- News APIs
"""

from .base import BaseAdapter, AdapterConfig, AdapterResult, SignalData
from .rss import RSSAdapter
from .github_events import GitHubEventsAdapter
from .onchain import OnChainAdapter
from .social import SocialMediaAdapter
from .news import NewsAPIAdapter
from .twitter import TwitterAdapter
from .discord import DiscordAdapter
from .lens import LensAdapter
from .farcaster import FarcasterAdapter
from .coingecko import CoingeckoAdapter
from .threads import ThreadsAdapter

__all__ = [
    # Base
    "BaseAdapter",
    "AdapterConfig",
    "AdapterResult",
    "SignalData",
    # Core Adapters
    "RSSAdapter",
    "GitHubEventsAdapter",
    "OnChainAdapter",
    "SocialMediaAdapter",
    "NewsAPIAdapter",
    # New Adapters (v0.5.0)
    "TwitterAdapter",
    "DiscordAdapter",
    "LensAdapter",
    "FarcasterAdapter",
    "CoingeckoAdapter",
    # New Adapters (v0.6.6)
    "ThreadsAdapter",
]
