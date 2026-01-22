"""
Base adapter class for signal collection.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
import asyncio
import hashlib


@dataclass
class AdapterConfig:
    """Configuration for adapters."""
    enabled: bool = True
    timeout: int = 30  # seconds
    max_retries: int = 3
    retry_delay: int = 5  # seconds
    rate_limit: Optional[float] = None  # requests per second
    batch_size: int = 50


@dataclass
class SignalData:
    """Raw signal data from adapters."""
    source: str
    category: str
    title: str
    summary: Optional[str] = None
    url: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None
    collected_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def id(self) -> str:
        """Generate unique ID based on content."""
        content = f"{self.source}:{self.title}:{self.url or ''}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source,
            "category": self.category,
            "title": self.title,
            "summary": self.summary,
            "url": self.url,
            "raw_data": self.raw_data,
            "collected_at": self.collected_at.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class AdapterResult:
    """Result from adapter fetch operation."""
    adapter_name: str
    success: bool
    signals: List[SignalData] = field(default_factory=list)
    error: Optional[str] = None
    duration_ms: float = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def count(self) -> int:
        return len(self.signals)


class BaseAdapter(ABC):
    """
    Base class for all signal adapters.

    Subclasses must implement:
    - name: Adapter name
    - fetch(): Fetch signals from the source
    """

    def __init__(self, config: Optional[AdapterConfig] = None):
        self.config = config or AdapterConfig()
        self._last_fetch: Optional[datetime] = None

    @property
    @abstractmethod
    def name(self) -> str:
        """Adapter name."""
        pass

    @property
    def source_type(self) -> str:
        """Source type for signals."""
        return self.name.lower().replace(" ", "_")

    @abstractmethod
    async def fetch(self) -> AdapterResult:
        """
        Fetch signals from the source.

        Returns:
            AdapterResult with fetched signals
        """
        pass

    async def fetch_with_retry(self) -> AdapterResult:
        """Fetch with retry logic."""
        last_error = None

        for attempt in range(self.config.max_retries):
            try:
                result = await asyncio.wait_for(
                    self.fetch(),
                    timeout=self.config.timeout
                )
                self._last_fetch = datetime.utcnow()
                return result

            except asyncio.TimeoutError:
                last_error = f"Timeout after {self.config.timeout}s"
            except Exception as e:
                last_error = str(e)

            if attempt < self.config.max_retries - 1:
                await asyncio.sleep(self.config.retry_delay)

        return AdapterResult(
            adapter_name=self.name,
            success=False,
            error=f"Failed after {self.config.max_retries} attempts: {last_error}"
        )

    def is_enabled(self) -> bool:
        """Check if adapter is enabled."""
        return self.config.enabled

    def get_last_fetch(self) -> Optional[datetime]:
        """Get last fetch time."""
        return self._last_fetch

    async def health_check(self) -> Dict[str, Any]:
        """Check adapter health."""
        return {
            "name": self.name,
            "enabled": self.config.enabled,
            "last_fetch": self._last_fetch.isoformat() if self._last_fetch else None,
        }
