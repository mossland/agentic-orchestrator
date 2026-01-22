"""
OnChain data adapter for signal collection.

Collects signals from blockchain data:
- Ethereum network activity
- MOC token activity
- DeFi TVL changes
- Whale movements
"""

import asyncio
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import time

import httpx

from .base import BaseAdapter, AdapterConfig, AdapterResult, SignalData


class OnChainAdapter(BaseAdapter):
    """
    OnChain data adapter.

    Fetches blockchain data from various sources:
    - DefiLlama (TVL data)
    - Etherscan (Ethereum activity)
    - Public RPC endpoints
    """

    # DeFi protocols to track
    TRACKED_PROTOCOLS: List[str] = [
        "uniswap",
        "aave",
        "lido",
        "makerdao",
        "curve",
        "compound",
        "convex-finance",
        "rocket-pool",
        "instadapp",
        "yearn-finance",
    ]

    # Chains to monitor
    TRACKED_CHAINS: List[str] = [
        "ethereum",
        "polygon",
        "arbitrum",
        "optimism",
        "base",
        "solana",
    ]

    def __init__(
        self,
        config: Optional[AdapterConfig] = None,
        etherscan_api_key: Optional[str] = None,
        alchemy_api_key: Optional[str] = None,
    ):
        super().__init__(config or AdapterConfig(timeout=60))
        self.etherscan_api_key = etherscan_api_key or os.getenv("ETHERSCAN_API_KEY")
        self.alchemy_api_key = alchemy_api_key or os.getenv("ALCHEMY_API_KEY")

        # API endpoints
        self.defillama_api = "https://api.llama.fi"
        self.etherscan_api = "https://api.etherscan.io/api"

    @property
    def name(self) -> str:
        return "onchain"

    async def fetch(self) -> AdapterResult:
        """Fetch on-chain signals."""
        start_time = time.time()
        signals: List[SignalData] = []
        errors: List[str] = []

        # Fetch different types of on-chain data concurrently
        tasks = [
            self._fetch_defi_tvl(),
            self._fetch_chain_stats(),
            self._fetch_protocol_updates(),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                errors.append(str(result))
            elif isinstance(result, list):
                signals.extend(result)

        duration_ms = (time.time() - start_time) * 1000

        return AdapterResult(
            adapter_name=self.name,
            success=len(signals) > 0,
            signals=signals,
            error="; ".join(errors) if errors else None,
            duration_ms=duration_ms,
            metadata={
                "protocols_tracked": len(self.TRACKED_PROTOCOLS),
                "chains_tracked": len(self.TRACKED_CHAINS),
            }
        )

    async def _fetch_defi_tvl(self) -> List[SignalData]:
        """Fetch DeFi TVL data from DefiLlama."""
        signals: List[SignalData] = []

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # Get protocols TVL
                response = await client.get(f"{self.defillama_api}/protocols")
                response.raise_for_status()
                protocols = response.json()

                # Filter to tracked protocols and find significant changes
                for protocol in protocols:
                    name = protocol.get("slug", "").lower()
                    if name not in self.TRACKED_PROTOCOLS:
                        continue

                    tvl = protocol.get("tvl", 0)
                    change_1d = protocol.get("change_1d", 0)
                    change_7d = protocol.get("change_7d", 0)

                    # Only report significant changes (>5% in 24h or >10% in 7d)
                    if abs(change_1d or 0) > 5 or abs(change_7d or 0) > 10:
                        direction = "increased" if (change_1d or 0) > 0 else "decreased"

                        signal = SignalData(
                            source=self.name,
                            category="crypto",
                            title=f"DeFi TVL: {protocol.get('name')} {direction} {abs(change_1d or 0):.1f}%",
                            summary=f"TVL: ${tvl/1e9:.2f}B, 24h change: {change_1d:.1f}%, 7d change: {change_7d:.1f}%",
                            url=f"https://defillama.com/protocol/{name}",
                            raw_data={
                                "type": "defi_tvl",
                                "protocol": protocol.get("name"),
                                "slug": name,
                                "tvl": tvl,
                                "change_1d": change_1d,
                                "change_7d": change_7d,
                                "chains": protocol.get("chains", []),
                            },
                            metadata={"subtype": "tvl"}
                        )
                        signals.append(signal)

        except Exception as e:
            print(f"Error fetching DeFi TVL: {e}")

        return signals

    async def _fetch_chain_stats(self) -> List[SignalData]:
        """Fetch chain statistics from DefiLlama."""
        signals: List[SignalData] = []

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(f"{self.defillama_api}/v2/chains")
                response.raise_for_status()
                chains = response.json()

                for chain in chains:
                    name = chain.get("name", "").lower()
                    if name not in self.TRACKED_CHAINS:
                        continue

                    gecko_id = chain.get("gecko_id")
                    tvl = chain.get("tvl", 0)

                    signal = SignalData(
                        source=self.name,
                        category="crypto",
                        title=f"Chain Stats: {chain.get('name')} TVL ${tvl/1e9:.2f}B",
                        summary=f"Total Value Locked on {chain.get('name')}",
                        url=f"https://defillama.com/chain/{chain.get('name')}",
                        raw_data={
                            "type": "chain_stats",
                            "chain": chain.get("name"),
                            "gecko_id": gecko_id,
                            "tvl": tvl,
                        },
                        metadata={"subtype": "chain"}
                    )
                    signals.append(signal)

        except Exception as e:
            print(f"Error fetching chain stats: {e}")

        return signals

    async def _fetch_protocol_updates(self) -> List[SignalData]:
        """Fetch recent protocol updates and raises."""
        signals: List[SignalData] = []

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # Get recent raises/funding
                response = await client.get(f"{self.defillama_api}/raises")
                response.raise_for_status()
                raises = response.json()

                # Get raises from last 7 days
                for raise_event in raises.get("raises", [])[:20]:
                    amount = raise_event.get("amount")
                    if not amount:
                        continue

                    signal = SignalData(
                        source=self.name,
                        category="crypto",
                        title=f"Funding: {raise_event.get('name')} raised ${amount}M",
                        summary=f"Round: {raise_event.get('round', 'Unknown')}. Lead investors: {', '.join(raise_event.get('leadInvestors', [])[:3])}",
                        url=raise_event.get("source"),
                        raw_data={
                            "type": "funding",
                            "name": raise_event.get("name"),
                            "amount": amount,
                            "round": raise_event.get("round"),
                            "lead_investors": raise_event.get("leadInvestors", []),
                            "other_investors": raise_event.get("otherInvestors", []),
                            "chains": raise_event.get("chains", []),
                            "category": raise_event.get("category"),
                        },
                        metadata={"subtype": "funding"}
                    )
                    signals.append(signal)

        except Exception as e:
            print(f"Error fetching protocol updates: {e}")

        return signals

    async def _fetch_gas_prices(self) -> List[SignalData]:
        """Fetch current gas prices (if Etherscan API key available)."""
        signals: List[SignalData] = []

        if not self.etherscan_api_key:
            return signals

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    self.etherscan_api,
                    params={
                        "module": "gastracker",
                        "action": "gasoracle",
                        "apikey": self.etherscan_api_key
                    }
                )
                response.raise_for_status()
                data = response.json()

                if data.get("status") == "1":
                    result = data.get("result", {})
                    safe_gas = int(result.get("SafeGasPrice", 0))
                    propose_gas = int(result.get("ProposeGasPrice", 0))
                    fast_gas = int(result.get("FastGasPrice", 0))

                    # Report if gas is unusually high (>50 gwei) or low (<10 gwei)
                    if fast_gas > 50 or fast_gas < 10:
                        status = "high" if fast_gas > 50 else "low"
                        signal = SignalData(
                            source=self.name,
                            category="crypto",
                            title=f"Gas Alert: Ethereum gas is {status} ({fast_gas} gwei)",
                            summary=f"Safe: {safe_gas} gwei, Standard: {propose_gas} gwei, Fast: {fast_gas} gwei",
                            url="https://etherscan.io/gastracker",
                            raw_data={
                                "type": "gas_price",
                                "safe": safe_gas,
                                "standard": propose_gas,
                                "fast": fast_gas,
                            },
                            metadata={"subtype": "gas"}
                        )
                        signals.append(signal)

        except Exception as e:
            print(f"Error fetching gas prices: {e}")

        return signals

    async def health_check(self) -> Dict[str, Any]:
        """Check adapter health."""
        base_health = await super().health_check()

        # Check DefiLlama API
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.defillama_api}/protocols")
                base_health["defillama_status"] = "connected" if response.status_code == 200 else "error"
        except Exception as e:
            base_health["defillama_status"] = f"error: {e}"

        base_health["etherscan_api_key"] = bool(self.etherscan_api_key)
        base_health["alchemy_api_key"] = bool(self.alchemy_api_key)

        return base_health
