"""
Plan markdown parser for extracting structured data.

Parses Plan documents (markdown) into structured dataclasses for project generation.
"""

import re
import json
import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


@dataclass
class TechStack:
    """Technology stack configuration extracted from a Plan."""
    frontend: Optional[str] = None  # "nextjs", "react", "vue"
    backend: Optional[str] = None   # "fastapi", "express", "django"
    database: Optional[str] = None  # "postgresql", "sqlite", "mongodb"
    blockchain: Optional[str] = None  # "ethereum", "solana", "polygon"
    additional: List[str] = field(default_factory=list)  # Additional technologies

    def to_dict(self) -> Dict[str, Any]:
        return {
            "frontend": self.frontend,
            "backend": self.backend,
            "database": self.database,
            "blockchain": self.blockchain,
            "additional": self.additional,
        }


@dataclass
class APIEndpoint:
    """API endpoint extracted from Plan architecture."""
    method: str  # GET, POST, PUT, DELETE
    path: str    # /api/users
    description: str
    request_body: Optional[str] = None
    response_type: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "method": self.method,
            "path": self.path,
            "description": self.description,
            "request_body": self.request_body,
            "response_type": self.response_type,
        }


@dataclass
class ProjectTask:
    """Task/milestone extracted from Plan."""
    title: str
    description: str
    week: Optional[int] = None
    priority: str = "medium"  # low, medium, high

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "description": self.description,
            "week": self.week,
            "priority": self.priority,
        }


@dataclass
class DataEntity:
    """Data model/entity extracted from Plan."""
    name: str
    description: str
    fields: List[Dict[str, str]] = field(default_factory=list)  # [{"name": "id", "type": "string"}]
    relationships: List[str] = field(default_factory=list)  # ["User has many Posts"]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "fields": self.fields,
            "relationships": self.relationships,
        }


@dataclass
class ExternalService:
    """External API/service integration extracted from Plan."""
    name: str  # "Twitter API", "Coingecko"
    purpose: str  # "Sentiment analysis", "Price data"
    endpoints: List[str] = field(default_factory=list)  # API endpoints to use
    auth_type: Optional[str] = None  # "api_key", "oauth2"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "purpose": self.purpose,
            "endpoints": self.endpoints,
            "auth_type": self.auth_type,
        }


@dataclass
class UIComponent:
    """UI component/page extracted from Plan."""
    name: str
    type: str  # "page", "component", "widget"
    description: str
    features: List[str] = field(default_factory=list)  # Features this component implements

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "features": self.features,
        }


@dataclass
class SmartContractSpec:
    """Smart contract specification extracted from Plan."""
    name: str
    purpose: str
    functions: List[Dict[str, str]] = field(default_factory=list)  # [{"name": "transfer", "params": "...", "desc": "..."}]
    events: List[str] = field(default_factory=list)
    storage: List[Dict[str, str]] = field(default_factory=list)  # State variables

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "purpose": self.purpose,
            "functions": self.functions,
            "events": self.events,
            "storage": self.storage,
        }


@dataclass
class ParsedPlan:
    """Structured data extracted from a Plan document."""
    title: str
    summary: str
    tech_stack: TechStack
    features: List[str]
    api_endpoints: List[APIEndpoint]
    tasks: List[ProjectTask]
    target_users: Optional[str] = None
    duration_estimate: Optional[str] = None
    risks: List[str] = field(default_factory=list)
    kpis: List[str] = field(default_factory=list)
    raw_content: str = ""
    # Enhanced fields for high-quality code generation
    entities: List[DataEntity] = field(default_factory=list)
    external_services: List[ExternalService] = field(default_factory=list)
    ui_components: List[UIComponent] = field(default_factory=list)
    smart_contracts: List[SmartContractSpec] = field(default_factory=list)
    detailed_features: List[Dict[str, Any]] = field(default_factory=list)  # Rich feature specs

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "summary": self.summary,
            "tech_stack": self.tech_stack.to_dict(),
            "features": self.features,
            "api_endpoints": [e.to_dict() for e in self.api_endpoints],
            "tasks": [t.to_dict() for t in self.tasks],
            "target_users": self.target_users,
            "duration_estimate": self.duration_estimate,
            "risks": self.risks,
            "kpis": self.kpis,
            "entities": [e.to_dict() for e in self.entities],
            "external_services": [s.to_dict() for s in self.external_services],
            "ui_components": [c.to_dict() for c in self.ui_components],
            "smart_contracts": [c.to_dict() for c in self.smart_contracts],
            "detailed_features": self.detailed_features,
        }


class PlanParser:
    """
    Parser for Plan markdown documents.

    Extracts structured information from Plan documents using:
    1. Regex-based section extraction
    2. LLM-based parsing for complex content (optional)
    """

    # Section header patterns
    SECTION_PATTERNS = {
        "overview": r"(?:##?\s*(?:프로젝트\s*)?개요|project\s*overview|summary)",
        "tech_stack": r"(?:##?\s*기술\s*(?:스택|아키텍처)|technical?\s*(?:stack|architecture))",
        "features": r"(?:##?\s*(?:핵심\s*)?기능|features?|functionality)",
        "api": r"(?:##?\s*API|endpoints?|routes?)",
        "tasks": r"(?:##?\s*(?:실행\s*)?계획|tasks?|roadmap|milestones?|timeline)",
        "risks": r"(?:##?\s*리스크|risks?|challenges?)",
        "kpis": r"(?:##?\s*(?:성과\s*)?지표|KPIs?|metrics?|success\s*criteria)",
    }

    # Tech detection patterns
    TECH_PATTERNS = {
        "frontend": {
            "nextjs": r"\b(?:next\.?js|next\s+js)\b",
            "react": r"\b(?:react|react\.?js)\b",
            "vue": r"\b(?:vue|vue\.?js|nuxt)\b",
            "angular": r"\b(?:angular)\b",
            "svelte": r"\b(?:svelte|sveltekit)\b",
        },
        "backend": {
            "fastapi": r"\b(?:fastapi|fast\s*api)\b",
            "express": r"\b(?:express|express\.?js|node\.?js)\b",
            "django": r"\b(?:django)\b",
            "flask": r"\b(?:flask)\b",
            "nestjs": r"\b(?:nest\.?js)\b",
        },
        "database": {
            "postgresql": r"\b(?:postgres|postgresql|pg)\b",
            "sqlite": r"\b(?:sqlite)\b",
            "mongodb": r"\b(?:mongo|mongodb)\b",
            "mysql": r"\b(?:mysql)\b",
            "redis": r"\b(?:redis)\b",
        },
        "blockchain": {
            "ethereum": r"\b(?:ethereum|eth|solidity|evm)\b",
            "solana": r"\b(?:solana|sol)\b",
            "polygon": r"\b(?:polygon|matic)\b",
            "arbitrum": r"\b(?:arbitrum|arb)\b",
        },
    }

    def __init__(self, router=None):
        """
        Initialize the parser.

        Args:
            router: Optional LLM router for enhanced parsing
        """
        self.router = router

    def parse(self, content: str, title: str = "") -> ParsedPlan:
        """
        Parse a Plan markdown document.

        Args:
            content: Plan document content (markdown)
            title: Plan title (optional, extracted from content if not provided)

        Returns:
            ParsedPlan with extracted structured data
        """
        if not content:
            return ParsedPlan(
                title=title or "Untitled Project",
                summary="",
                tech_stack=TechStack(),
                features=[],
                api_endpoints=[],
                tasks=[],
                raw_content="",
            )

        # Extract title from content if not provided
        if not title:
            title = self._extract_title(content)

        # Extract sections
        sections = self._extract_sections(content)

        # Parse each section
        summary = self._extract_summary(sections.get("overview", ""), content)
        tech_stack = self._detect_tech_stack(content)
        features = self._extract_features(sections.get("features", ""))
        api_endpoints = self._extract_api_endpoints(sections.get("api", ""))
        tasks = self._extract_tasks(sections.get("tasks", ""))
        risks = self._extract_list(sections.get("risks", ""))
        kpis = self._extract_list(sections.get("kpis", ""))

        # Extract additional metadata
        target_users = self._extract_target_users(sections.get("overview", ""), content)
        duration = self._extract_duration(sections.get("overview", ""), sections.get("tasks", ""))

        return ParsedPlan(
            title=title,
            summary=summary,
            tech_stack=tech_stack,
            features=features,
            api_endpoints=api_endpoints,
            tasks=tasks,
            target_users=target_users,
            duration_estimate=duration,
            risks=risks,
            kpis=kpis,
            raw_content=content,
        )

    async def parse_with_llm(self, content: str, title: str = "") -> ParsedPlan:
        """
        Parse a Plan using LLM for enhanced extraction.

        Falls back to regex-based parsing if LLM is unavailable.

        Args:
            content: Plan document content
            title: Plan title

        Returns:
            ParsedPlan with extracted structured data
        """
        if not self.router:
            logger.warning("No LLM router configured, using regex-based parsing")
            return self.parse(content, title)

        try:
            # First do regex-based parsing for structure
            base_parsed = self.parse(content, title)

            # Use LLM to enhance/validate tech stack detection
            prompt = f"""Analyze this project plan and extract the technology stack in JSON format.

Plan Content:
{content[:3000]}

Return ONLY a JSON object with this structure (no markdown, no explanation):
{{
    "frontend": "nextjs" or "react" or "vue" or null,
    "backend": "fastapi" or "express" or "django" or null,
    "database": "postgresql" or "sqlite" or "mongodb" or null,
    "blockchain": "ethereum" or "solana" or null,
    "additional": ["list", "of", "other", "techs"]
}}"""

            response = await self.router.route(
                prompt=prompt,
                task_type="parsing",
                model="glm-4.7-flash",
                temperature=0.1,
                max_tokens=500,
            )

            # Parse LLM response
            try:
                # Extract JSON from response
                json_match = re.search(r'\{[\s\S]*\}', response.content)
                if json_match:
                    tech_data = json.loads(json_match.group())
                    base_parsed.tech_stack = TechStack(
                        frontend=tech_data.get("frontend"),
                        backend=tech_data.get("backend"),
                        database=tech_data.get("database"),
                        blockchain=tech_data.get("blockchain"),
                        additional=tech_data.get("additional", []),
                    )
            except json.JSONDecodeError:
                logger.warning("Failed to parse LLM tech stack response")

            return base_parsed

        except Exception as e:
            logger.error(f"LLM parsing failed: {e}")
            return self.parse(content, title)

    def _extract_title(self, content: str) -> str:
        """Extract title from markdown content."""
        # Look for H1 header
        h1_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if h1_match:
            return h1_match.group(1).strip()

        # Look for "Plan:" prefix
        plan_match = re.search(r'Plan:\s*(.+?)(?:\n|$)', content, re.IGNORECASE)
        if plan_match:
            return plan_match.group(1).strip()

        # Use first non-empty line
        lines = content.strip().split('\n')
        for line in lines:
            clean = line.strip().lstrip('#').strip()
            if clean:
                return clean[:100]

        return "Untitled Project"

    def _extract_sections(self, content: str) -> Dict[str, str]:
        """Extract named sections from markdown."""
        sections = {}

        for name, pattern in self.SECTION_PATTERNS.items():
            # Find section header
            header_match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
            if header_match:
                start = header_match.end()
                # Find next section header
                next_header = re.search(r'^##?\s+', content[start:], re.MULTILINE)
                if next_header:
                    sections[name] = content[start:start + next_header.start()].strip()
                else:
                    sections[name] = content[start:].strip()

        return sections

    def _extract_summary(self, overview_section: str, full_content: str) -> str:
        """Extract project summary."""
        if overview_section:
            # Get first paragraph
            paragraphs = overview_section.split('\n\n')
            for para in paragraphs:
                clean = para.strip()
                if clean and not clean.startswith(('-', '*', '#', '|')):
                    return clean[:500]

        # Fallback: first meaningful paragraph from full content
        paragraphs = full_content.split('\n\n')
        for para in paragraphs:
            clean = para.strip()
            if clean and not clean.startswith('#') and len(clean) > 50:
                return clean[:500]

        return ""

    def _detect_tech_stack(self, content: str) -> TechStack:
        """Detect technology stack from content."""
        content_lower = content.lower()
        tech_stack = TechStack()
        additional = []

        for category, patterns in self.TECH_PATTERNS.items():
            for tech, pattern in patterns.items():
                if re.search(pattern, content_lower, re.IGNORECASE):
                    if category == "frontend" and not tech_stack.frontend:
                        tech_stack.frontend = tech
                    elif category == "backend" and not tech_stack.backend:
                        tech_stack.backend = tech
                    elif category == "database" and not tech_stack.database:
                        tech_stack.database = tech
                    elif category == "blockchain" and not tech_stack.blockchain:
                        tech_stack.blockchain = tech
                    else:
                        if tech not in additional:
                            additional.append(tech)

        tech_stack.additional = additional
        return tech_stack

    def _extract_features(self, features_section: str) -> List[str]:
        """Extract feature list."""
        return self._extract_list(features_section)

    def _extract_list(self, section: str) -> List[str]:
        """Extract bullet points from a section."""
        items = []
        if not section:
            return items

        # Match bullet points
        bullet_pattern = r'^[\s]*[-*•]\s*(.+)$'
        for line in section.split('\n'):
            match = re.match(bullet_pattern, line)
            if match:
                item = match.group(1).strip()
                if item and len(item) > 2:
                    items.append(item)

        # Also match numbered lists
        numbered_pattern = r'^\s*\d+[.)]\s*(.+)$'
        for line in section.split('\n'):
            match = re.match(numbered_pattern, line)
            if match:
                item = match.group(1).strip()
                if item and len(item) > 2 and item not in items:
                    items.append(item)

        return items[:20]  # Limit to 20 items

    def _extract_api_endpoints(self, api_section: str) -> List[APIEndpoint]:
        """Extract API endpoints from content."""
        endpoints = []
        if not api_section:
            return endpoints

        # Pattern for API definitions like "GET /api/users - Get all users"
        api_pattern = r'(GET|POST|PUT|DELETE|PATCH)\s+([/\w{}:-]+)\s*[-:]\s*(.+)'

        for line in api_section.split('\n'):
            match = re.search(api_pattern, line, re.IGNORECASE)
            if match:
                endpoints.append(APIEndpoint(
                    method=match.group(1).upper(),
                    path=match.group(2),
                    description=match.group(3).strip(),
                ))

        return endpoints[:20]  # Limit to 20 endpoints

    def _extract_tasks(self, tasks_section: str) -> List[ProjectTask]:
        """Extract tasks/milestones from content."""
        tasks = []
        if not tasks_section:
            return tasks

        # Look for week/phase patterns
        week_pattern = r'(?:Week|주|Phase|단계)\s*(\d+)'
        current_week = None

        for line in tasks_section.split('\n'):
            # Check for week header
            week_match = re.search(week_pattern, line, re.IGNORECASE)
            if week_match:
                current_week = int(week_match.group(1))
                continue

            # Extract task items
            bullet_match = re.match(r'[\s]*[-*•]\s*(.+)', line)
            if bullet_match:
                task_text = bullet_match.group(1).strip()
                if task_text and len(task_text) > 5:
                    tasks.append(ProjectTask(
                        title=task_text[:100],
                        description=task_text,
                        week=current_week,
                        priority="medium",
                    ))

        return tasks[:30]  # Limit to 30 tasks

    def _extract_target_users(self, overview: str, full_content: str) -> Optional[str]:
        """Extract target user description."""
        # Look for user/audience patterns
        patterns = [
            r'(?:대상\s*사용자|target\s*(?:users?|audience))[\s:]+(.+?)(?:\n|$)',
            r'(?:타겟|for)\s+(.+?)(?:를|에게|users?|developers?)',
        ]

        for pattern in patterns:
            match = re.search(pattern, overview or full_content, re.IGNORECASE)
            if match:
                return match.group(1).strip()[:200]

        return None

    def _extract_duration(self, overview: str, tasks_section: str) -> Optional[str]:
        """Extract project duration estimate."""
        content = (overview or "") + (tasks_section or "")

        # Look for duration patterns
        patterns = [
            r'(\d+)\s*(?:weeks?|주)',
            r'(\d+)\s*(?:months?|개월)',
            r'(?:duration|기간)[\s:]+([^.\n]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(0).strip()[:50]

        return None

    # External service patterns for detection
    EXTERNAL_SERVICE_PATTERNS = {
        "twitter": {
            "name": "Twitter/X API",
            "pattern": r"\b(?:twitter|x\.com|tweet|nitter)\b",
            "purpose": "Social media data, sentiment analysis",
            "auth_type": "oauth2",
        },
        "coingecko": {
            "name": "Coingecko API",
            "pattern": r"\b(?:coingecko|coin\s*gecko)\b",
            "purpose": "Cryptocurrency price and market data",
            "auth_type": "api_key",
        },
        "etherscan": {
            "name": "Etherscan API",
            "pattern": r"\b(?:etherscan)\b",
            "purpose": "Ethereum blockchain data",
            "auth_type": "api_key",
        },
        "alchemy": {
            "name": "Alchemy API",
            "pattern": r"\b(?:alchemy)\b",
            "purpose": "Blockchain RPC and enhanced APIs",
            "auth_type": "api_key",
        },
        "infura": {
            "name": "Infura API",
            "pattern": r"\b(?:infura)\b",
            "purpose": "Ethereum node access",
            "auth_type": "api_key",
        },
        "openai": {
            "name": "OpenAI API",
            "pattern": r"\b(?:openai|gpt|chatgpt)\b",
            "purpose": "AI/ML text generation and analysis",
            "auth_type": "api_key",
        },
        "dune": {
            "name": "Dune Analytics",
            "pattern": r"\b(?:dune\s*analytics|dune)\b",
            "purpose": "On-chain analytics and queries",
            "auth_type": "api_key",
        },
        "nansen": {
            "name": "Nansen",
            "pattern": r"\b(?:nansen)\b",
            "purpose": "On-chain wallet analytics",
            "auth_type": "api_key",
        },
        "defillama": {
            "name": "DefiLlama API",
            "pattern": r"\b(?:defillama|defi\s*llama)\b",
            "purpose": "DeFi TVL and protocol data",
            "auth_type": None,
        },
        "websocket": {
            "name": "WebSocket Server",
            "pattern": r"\b(?:websocket|ws://|wss://|실시간|real-?time)\b",
            "purpose": "Real-time bidirectional communication",
            "auth_type": None,
        },
    }

    def _extract_external_services(self, content: str) -> List[ExternalService]:
        """Extract external service integrations from content."""
        services = []
        content_lower = content.lower()

        for key, config in self.EXTERNAL_SERVICE_PATTERNS.items():
            if re.search(config["pattern"], content_lower, re.IGNORECASE):
                services.append(ExternalService(
                    name=config["name"],
                    purpose=config["purpose"],
                    endpoints=[],
                    auth_type=config["auth_type"],
                ))

        return services

    def _extract_entities_basic(self, content: str) -> List[DataEntity]:
        """Basic entity extraction using patterns."""
        entities = []

        # Common entity patterns
        entity_patterns = [
            (r"\b(?:User|사용자|Member)\b", "User", "User account and profile"),
            (r"\b(?:Wallet|지갑|Address)\b", "Wallet", "Blockchain wallet"),
            (r"\b(?:Transaction|트랜잭션|거래)\b", "Transaction", "Transaction record"),
            (r"\b(?:Alert|알림|Notification)\b", "Alert", "Notification/alert"),
            (r"\b(?:Sentiment|감성|Opinion)\b", "Sentiment", "Sentiment analysis result"),
            (r"\b(?:Token|토큰|Coin)\b", "Token", "Cryptocurrency token"),
            (r"\b(?:Price|가격|Market)\b", "MarketData", "Market price data"),
            (r"\b(?:Portfolio|포트폴리오)\b", "Portfolio", "User portfolio"),
            (r"\b(?:Setting|설정|Config)\b", "Setting", "User settings"),
        ]

        seen = set()
        for pattern, name, desc in entity_patterns:
            if re.search(pattern, content, re.IGNORECASE) and name not in seen:
                seen.add(name)
                entities.append(DataEntity(
                    name=name,
                    description=desc,
                    fields=[],
                    relationships=[],
                ))

        return entities

    def _extract_ui_components_basic(self, content: str) -> List[UIComponent]:
        """Basic UI component extraction."""
        components = []

        # Common UI patterns
        ui_patterns = [
            (r"\b(?:Dashboard|대시보드)\b", "Dashboard", "page", "Main dashboard view"),
            (r"\b(?:Chart|차트|Graph)\b", "Chart", "component", "Data visualization chart"),
            (r"\b(?:Alert|알림)\s*(?:List|목록)?\b", "AlertList", "component", "Alert/notification list"),
            (r"\b(?:Settings?|설정)\s*(?:Page|페이지)?\b", "Settings", "page", "Settings page"),
            (r"\b(?:Profile|프로필)\b", "Profile", "page", "User profile page"),
            (r"\b(?:Login|로그인|Auth)\b", "Auth", "page", "Authentication page"),
            (r"\b(?:Search|검색)\b", "Search", "component", "Search functionality"),
            (r"\b(?:Table|테이블|List|목록)\b", "DataTable", "component", "Data table/list view"),
            (r"\b(?:Modal|모달|Dialog)\b", "Modal", "component", "Modal dialog"),
            (r"\b(?:Sidebar|사이드바|Nav)\b", "Sidebar", "component", "Navigation sidebar"),
        ]

        seen = set()
        for pattern, name, comp_type, desc in ui_patterns:
            if re.search(pattern, content, re.IGNORECASE) and name not in seen:
                seen.add(name)
                components.append(UIComponent(
                    name=name,
                    type=comp_type,
                    description=desc,
                    features=[],
                ))

        return components

    async def parse_deep_with_llm(self, content: str, title: str = "") -> ParsedPlan:
        """
        Deep parsing using LLM for comprehensive extraction.

        This extracts entities, services, UI components, and detailed features
        for high-quality code generation.

        Args:
            content: Plan document content
            title: Plan title

        Returns:
            ParsedPlan with comprehensive extracted data
        """
        # Start with basic parsing
        base_parsed = self.parse(content, title)

        # Add basic extractions
        base_parsed.external_services = self._extract_external_services(content)
        base_parsed.entities = self._extract_entities_basic(content)
        base_parsed.ui_components = self._extract_ui_components_basic(content)

        if not self.router:
            logger.warning("No LLM router, using basic extraction only")
            return base_parsed

        try:
            # Deep extraction with LLM
            deep_prompt = f"""Analyze this project plan and extract detailed specifications for code generation.

Plan Content:
{content[:4000]}

Return ONLY a JSON object with this exact structure (no markdown, no explanation):
{{
    "entities": [
        {{
            "name": "EntityName",
            "description": "What this entity represents",
            "fields": [
                {{"name": "id", "type": "string", "description": "Primary key"}},
                {{"name": "createdAt", "type": "datetime", "description": "Creation timestamp"}}
            ],
            "relationships": ["Entity has many OtherEntity"]
        }}
    ],
    "api_endpoints": [
        {{
            "method": "GET",
            "path": "/api/resource",
            "description": "What this endpoint does",
            "request_body": "{{ field: type }}",
            "response_type": "{{ field: type }}"
        }}
    ],
    "ui_components": [
        {{
            "name": "ComponentName",
            "type": "page|component|widget",
            "description": "What this component does",
            "features": ["feature1", "feature2"]
        }}
    ],
    "smart_contracts": [
        {{
            "name": "ContractName",
            "purpose": "What this contract does",
            "functions": [
                {{"name": "functionName", "params": "param1: type", "description": "What it does"}}
            ],
            "events": ["EventName(indexed param1, param2)"],
            "storage": [{{"name": "varName", "type": "mapping(address => uint256)"}}]
        }}
    ],
    "detailed_features": [
        {{
            "name": "Feature Name",
            "description": "Detailed description",
            "components_needed": ["Component1", "Component2"],
            "apis_needed": ["/api/endpoint1"],
            "priority": "high|medium|low"
        }}
    ]
}}

Extract ALL relevant entities, endpoints, components, and features from the plan.
Be comprehensive but realistic based on what's actually described in the plan."""

            response = await self.router.route(
                prompt=deep_prompt,
                task_type="parsing",
                model="qwen2.5:32b",  # Use larger model for complex extraction
                temperature=0.2,
                max_tokens=4000,
            )

            # Parse LLM response
            try:
                json_match = re.search(r'\{[\s\S]*\}', response.content)
                if json_match:
                    data = json.loads(json_match.group())

                    # Update entities
                    if data.get("entities"):
                        base_parsed.entities = [
                            DataEntity(
                                name=e.get("name", "Unknown"),
                                description=e.get("description", ""),
                                fields=e.get("fields", []),
                                relationships=e.get("relationships", []),
                            )
                            for e in data["entities"]
                        ]

                    # Update API endpoints
                    if data.get("api_endpoints"):
                        base_parsed.api_endpoints = [
                            APIEndpoint(
                                method=e.get("method", "GET"),
                                path=e.get("path", "/"),
                                description=e.get("description", ""),
                                request_body=e.get("request_body"),
                                response_type=e.get("response_type"),
                            )
                            for e in data["api_endpoints"]
                        ]

                    # Update UI components
                    if data.get("ui_components"):
                        base_parsed.ui_components = [
                            UIComponent(
                                name=c.get("name", "Component"),
                                type=c.get("type", "component"),
                                description=c.get("description", ""),
                                features=c.get("features", []),
                            )
                            for c in data["ui_components"]
                        ]

                    # Update smart contracts
                    if data.get("smart_contracts"):
                        base_parsed.smart_contracts = [
                            SmartContractSpec(
                                name=c.get("name", "Contract"),
                                purpose=c.get("purpose", ""),
                                functions=c.get("functions", []),
                                events=c.get("events", []),
                                storage=c.get("storage", []),
                            )
                            for c in data["smart_contracts"]
                        ]

                    # Update detailed features
                    if data.get("detailed_features"):
                        base_parsed.detailed_features = data["detailed_features"]

                    logger.info(f"Deep parsing extracted: {len(base_parsed.entities)} entities, "
                               f"{len(base_parsed.api_endpoints)} endpoints, "
                               f"{len(base_parsed.ui_components)} components")

            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse LLM deep extraction response: {e}")

        except Exception as e:
            logger.error(f"Deep LLM parsing failed: {e}")

        return base_parsed
