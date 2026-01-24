"""
Debate protocol for agent interactions.

Defines the rules and flow for multi-stage debates with diverse agent personas.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime


class DebatePhase(Enum):
    """Debate phase types."""
    DIVERGENCE = "divergence"     # Generate diverse ideas
    CONVERGENCE = "convergence"   # Filter and merge ideas
    PLANNING = "planning"         # Create actionable plans


class MessageType(Enum):
    """Types of debate messages."""
    INITIAL_IDEA = "initial_idea"
    ANALYSIS = "analysis"
    FEEDBACK = "feedback"
    CHALLENGE = "challenge"
    SUPPORT = "support"
    SYNTHESIS = "synthesis"
    EVALUATION = "evaluation"
    VOTE = "vote"
    PLAN_DRAFT = "plan_draft"
    PLAN_REVIEW = "plan_review"
    FINAL_PLAN = "final_plan"


@dataclass
class DebateMessage:
    """A single message in the debate."""
    id: str
    phase: DebatePhase
    round: int
    agent_id: str
    agent_name: str
    message_type: MessageType
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    references: List[str] = field(default_factory=list)  # IDs of referenced messages
    score: Optional[float] = None  # Relevance/quality score

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "phase": self.phase.value,
            "round": self.round,
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "message_type": self.message_type.value,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "references": self.references,
            "score": self.score,
        }


@dataclass
class DebateRound:
    """A single round within a phase."""
    round_num: int
    phase: DebatePhase
    topic: str
    messages: List[DebateMessage] = field(default_factory=list)
    summary: Optional[str] = None
    key_points: List[str] = field(default_factory=list)
    decisions: List[Dict[str, Any]] = field(default_factory=list)

    def add_message(self, message: DebateMessage):
        self.messages.append(message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "round_num": self.round_num,
            "phase": self.phase.value,
            "topic": self.topic,
            "messages": [m.to_dict() for m in self.messages],
            "summary": self.summary,
            "key_points": self.key_points,
            "decisions": self.decisions,
        }


@dataclass
class PhaseResult:
    """Result of a debate phase."""
    phase: DebatePhase
    rounds: List[DebateRound]
    output: Dict[str, Any]
    duration_seconds: float
    total_tokens: int
    total_cost: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase": self.phase.value,
            "rounds": [r.to_dict() for r in self.rounds],
            "output": self.output,
            "duration_seconds": self.duration_seconds,
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
        }


@dataclass
class DebateProtocolConfig:
    """Configuration for debate protocol."""
    # Divergence phase
    divergence_rounds: int = 3
    divergence_agents_per_round: int = 8
    min_ideas_to_generate: int = 20

    # Convergence phase
    convergence_rounds: int = 2
    convergence_agents_per_round: int = 4
    top_ideas_to_keep: int = 5
    merge_threshold: float = 0.7  # Similarity threshold for merging

    # Planning phase
    planning_rounds: int = 2
    planning_agents_per_round: int = 5
    require_unanimous_approval: bool = False
    min_approval_ratio: float = 0.7

    # General settings
    max_tokens_per_response: int = 2000
    temperature_divergence: float = 0.95  # Higher for creativity (v0.5.0: increased from 0.9)
    temperature_convergence: float = 0.5  # Lower for analysis
    temperature_planning: float = 0.7

    # Timeouts
    agent_timeout_seconds: int = 120
    round_timeout_seconds: int = 600

    def to_dict(self) -> Dict[str, Any]:
        return {
            "divergence_rounds": self.divergence_rounds,
            "divergence_agents_per_round": self.divergence_agents_per_round,
            "min_ideas_to_generate": self.min_ideas_to_generate,
            "convergence_rounds": self.convergence_rounds,
            "convergence_agents_per_round": self.convergence_agents_per_round,
            "top_ideas_to_keep": self.top_ideas_to_keep,
            "merge_threshold": self.merge_threshold,
            "planning_rounds": self.planning_rounds,
            "planning_agents_per_round": self.planning_agents_per_round,
            "require_unanimous_approval": self.require_unanimous_approval,
            "min_approval_ratio": self.min_approval_ratio,
            "max_tokens_per_response": self.max_tokens_per_response,
            "temperature_divergence": self.temperature_divergence,
            "temperature_convergence": self.temperature_convergence,
            "temperature_planning": self.temperature_planning,
        }


class DebateProtocol:
    """
    Protocol for managing multi-stage debates.

    Defines rules for:
    - Agent participation order
    - Message types allowed per phase
    - Scoring and evaluation criteria
    - Termination conditions
    """

    # SCAMPER creativity techniques for divergence phase
    SCAMPER_TECHNIQUES = {
        1: {
            "name": "Substitute & Combine",
            "description": "Substitute and Combine techniques",
            "prompt": """### Creativity Technique: Substitute & Combine

**Substitute**: Replace components of existing solutions with something else.
- What if we replace existing technology with AI/blockchain?
- What if we replace centralized elements with decentralization?
- What if we replace manual processes with automation?

**Combine**: Merge different concepts/technologies/markets.
- DeFi + GameFi = ?
- NFT + Real-world assets = ?
- AI Agents + DAO Governance = ?

💡 Example: "Smart Contract + Insurance + AI Underwriting = Automatic Insurance Claim Payment System"
""",
        },
        2: {
            "name": "Adapt & Modify",
            "description": "Adapt and Modify techniques",
            "prompt": """### Creativity Technique: Adapt & Modify

**Adapt**: Apply success stories from other industries to Web3.
- What if we apply Uber's matching system to DeFi?
- What if we apply Netflix's recommendation algorithm to NFT marketplaces?
- What if we apply gaming guild systems to DAOs?

**Modify**: Change the scale, form, or attributes of existing ideas.
- What if we shrink to micro-scale? (micro-loans, micro-investments)
- What if we scale to global level?
- What if we make it real-time?

💡 Example: "Airbnb + Metaverse = Virtual Real Estate Rental Platform"
""",
        },
        3: {
            "name": "Put to Other Use & Eliminate & Reverse",
            "description": "Put to Other Use, Eliminate, and Reverse techniques",
            "prompt": """### Creativity Technique: Put to Other Use & Eliminate & Reverse

**Put to Other Use**: Find new applications for existing technologies/assets.
- Where else can NFTs be used besides art?
- How can DeFi protocols be applied outside of finance?
- What if tokens are used for purposes other than investment?

**Eliminate**: Simplify by removing unnecessary elements.
- What if we eliminate intermediaries?
- How can we remove KYC while maintaining regulatory compliance?
- How can we eliminate gas fees?

**Reverse**: Think in the opposite direction.
- What if the platform pays users instead of users paying the platform?
- What if we consume liquidity instead of providing it?
- What if we incentivize burning tokens instead of minting?

💡 Example: "Reverse Auction + NFT = NFT Marketplace Where Buyers Set Prices"
""",
        },
    }

    # Lateral thinking prompts for Phase 2
    LATERAL_THINKING = {
        1: {
            "name": "Blue Sky Thinking",
            "description": "Unconstrained imaginative thinking",
            "prompt": """### Lateral Thinking Technique: Blue Sky Thinking

Forget all constraints and imagine freely:
- What would you build with unlimited funding?
- What solutions would be possible without technical limitations?
- What if regulations fully supported your vision?
- What if all users were familiar with Web3?

⚠️ In this round, dismiss any thoughts of "it's impossible."
""",
        },
        2: {
            "name": "Paradox Approach",
            "description": "Finding new perspectives through paradoxical thinking",
            "prompt": """### Lateral Thinking Technique: Paradox Approach

Think in reverse to gain new insights:
- Instead of solving the problem, ask "How would we make the problem worse?"
- Instead of making profit, think "How would we lose money?"
- Instead of increasing users, consider "How would we make users leave?"

Flip the insights from these paradoxes to derive real solutions.
""",
        },
        3: {
            "name": "Cross-Domain Innovation",
            "description": "Borrowing ideas from other industries",
            "prompt": """### Lateral Thinking Technique: Cross-Domain Innovation

Apply success patterns from completely different industries to Web3:

**Industries to Reference:**
- 🎮 Gaming: Level-ups, Quests, Guilds, Season Passes
- 🏥 Healthcare: Prevention, Monitoring, Personalization
- 🚗 Mobility: Sharing Economy, Autonomous Driving, MaaS
- 🎵 Entertainment: Streaming, Fandoms, Creator Economy
- 🏭 Manufacturing: Lean Production, JIT, Quality Control
- 📚 Education: Gamification, Micro-learning, Credentials

Present ideas in the format: "Applying [Pattern Y] from [Industry X] to Mossland would..."
""",
        },
    }

    # Allowed message types per phase
    PHASE_MESSAGE_TYPES = {
        DebatePhase.DIVERGENCE: [
            MessageType.INITIAL_IDEA,
            MessageType.ANALYSIS,
            MessageType.FEEDBACK,
            MessageType.CHALLENGE,
            MessageType.SUPPORT,
        ],
        DebatePhase.CONVERGENCE: [
            MessageType.EVALUATION,
            MessageType.SYNTHESIS,
            MessageType.VOTE,
            MessageType.FEEDBACK,
        ],
        DebatePhase.PLANNING: [
            MessageType.PLAN_DRAFT,
            MessageType.PLAN_REVIEW,
            MessageType.FEEDBACK,
            MessageType.FINAL_PLAN,
        ],
    }

    def __init__(self, config: Optional[DebateProtocolConfig] = None):
        self.config = config or DebateProtocolConfig()

    def get_allowed_message_types(self, phase: DebatePhase) -> List[MessageType]:
        """Get allowed message types for a phase."""
        return self.PHASE_MESSAGE_TYPES.get(phase, [])

    def validate_message(self, message: DebateMessage) -> tuple[bool, str]:
        """
        Validate a debate message.

        Returns:
            (is_valid, error_message)
        """
        allowed_types = self.get_allowed_message_types(message.phase)
        if message.message_type not in allowed_types:
            return False, f"Message type {message.message_type} not allowed in {message.phase}"

        if not message.content or len(message.content.strip()) < 10:
            return False, "Message content too short"

        return True, ""

    def should_end_phase(
        self,
        phase: DebatePhase,
        current_round: int,
        messages: List[DebateMessage],
        ideas_count: int = 0,
    ) -> tuple[bool, str]:
        """
        Check if a phase should end.

        Returns:
            (should_end, reason)
        """
        if phase == DebatePhase.DIVERGENCE:
            if current_round >= self.config.divergence_rounds:
                return True, "max_rounds_reached"
            if ideas_count >= self.config.min_ideas_to_generate:
                return True, "sufficient_ideas"

        elif phase == DebatePhase.CONVERGENCE:
            if current_round >= self.config.convergence_rounds:
                return True, "max_rounds_reached"

        elif phase == DebatePhase.PLANNING:
            if current_round >= self.config.planning_rounds:
                return True, "max_rounds_reached"
            # Check for consensus
            if self._check_consensus(messages):
                return True, "consensus_reached"

        return False, "continue"

    def _check_consensus(self, messages: List[DebateMessage]) -> bool:
        """Check if planning phase reached consensus."""
        votes = [m for m in messages if m.message_type == MessageType.VOTE]
        if not votes:
            return False

        approvals = sum(1 for v in votes if "approve" in v.content.lower())
        total = len(votes)

        if self.config.require_unanimous_approval:
            return approvals == total

        return (approvals / total) >= self.config.min_approval_ratio if total > 0 else False

    def get_temperature(self, phase: DebatePhase) -> float:
        """Get recommended temperature for a phase."""
        temps = {
            DebatePhase.DIVERGENCE: self.config.temperature_divergence,
            DebatePhase.CONVERGENCE: self.config.temperature_convergence,
            DebatePhase.PLANNING: self.config.temperature_planning,
        }
        return temps.get(phase, 0.7)

    def get_creativity_technique(self, round_num: int, use_lateral: bool = False) -> str:
        """Get creativity technique prompt for the given round.

        Args:
            round_num: Current round number (1-indexed)
            use_lateral: Use lateral thinking instead of SCAMPER

        Returns:
            Creativity technique prompt string
        """
        techniques = self.LATERAL_THINKING if use_lateral else self.SCAMPER_TECHNIQUES
        # Cycle through techniques if round_num exceeds available techniques
        technique_key = ((round_num - 1) % len(techniques)) + 1
        technique = techniques.get(technique_key, techniques[1])
        return technique["prompt"]

    def create_divergence_prompt(
        self,
        topic: str,
        context: str,
        agent_personality: Dict[str, str],
        round_num: int,
        previous_ideas: List[str],
    ) -> str:
        """Create prompt for divergence phase with SCAMPER creativity techniques."""
        personality_desc = "\n".join(f"- {k}: {v}" for k, v in agent_personality.items())

        # Get creativity technique for this round
        # Use SCAMPER for odd rounds, Lateral Thinking for even rounds
        use_lateral = (round_num % 2 == 0)
        creativity_prompt = self.get_creativity_technique(round_num, use_lateral=use_lateral)

        previous_section = ""
        if previous_ideas:
            # Calculate Jaccard similarity hints for novelty
            previous_section = f"""
Ideas proposed in previous rounds:
{chr(10).join(f"- {idea}" for idea in previous_ideas[:10])}

⚠️ Please present a **clearly different** new perspective from the ideas above.
- Similar ideas will receive lower scores
- Try completely new approaches
"""

        return f"""You are an expert with the following characteristics:
{personality_desc}

## Discussion Topic
{topic}

## Background Information
{context}

{previous_section}

{creativity_prompt}

## Instructions
Based on your characteristics and expertise, please present **specific and actionable ideas** on this topic.
Use the creativity techniques above to derive novel ideas that differ from existing ones.

### Idea Writing Rules (Must Follow)

**Title Rules:**
- Must start with `## Idea: [Title]` format
- Title must be at least 30 characters, specific and descriptive
- Bad examples: "AI-based Service", "Token Economy Improvement"
- Good examples: "GPT-5 Based DeFi Position Auto-Rebalancing Agent Development", "Real-time Metaverse Asset Value Tracker for Mossland NFT Holders"

**Content Rules:**
Each idea must **include** the following sections:

1. **Core Analysis** (100+ characters)
   - Current market/technology situation analysis
   - Specific reasons why this idea is needed now

2. **Opportunity or Risk** (150+ characters)
   - Include quantitative data or specific examples
   - Differentiation from competitive services

3. **Specific Proposal** (200+ characters)
   - List 3-5 core features
   - Suggest tech stack (e.g., Next.js, Solidity, Python, etc.)
   - Define MVP scope

4. **Execution Roadmap** (100+ characters)
   - Specific schedule like Week 1, Week 2
   - Required resources (number of developers, estimated cost, etc.)

5. **Success Metrics**
   - 2-3 measurable KPIs
   - Include target numbers (e.g., "500 DAU within 1 month of launch")

Please provide in-depth analysis and proposals that showcase your expertise.
This is Round {round_num} statement.

---

### 📝 Output Format (You MUST use the JSON structure below)

```json
{{
  "idea_title": "Specific title of 30+ characters (must include tech names, project names, numbers)",
  "core_analysis": "Current market/technology situation analysis (100+ characters)",
  "opportunity_risk": {{
    "opportunities": "Opportunity factors (100+ characters, include quantitative data)",
    "risks": "Risk factors (50+ characters)",
    "differentiators": "Differentiation from competitive services"
  }},
  "proposal": {{
    "description": "Specific proposal description (200+ characters)",
    "core_features": ["Core Feature 1", "Core Feature 2", "Core Feature 3"],
    "tech_stack": ["React/Next.js", "Python/FastAPI", "Solidity"],
    "mvp_scope": "MVP scope definition"
  }},
  "roadmap": {{
    "week1": "Week 1 plan",
    "week2": "Week 2 plan",
    "resources": "Required resources (number of developers, estimated cost)"
  }},
  "kpis": [
    {{"metric": "DAU", "target": "500 users", "measurement": "Analytics dashboard"}},
    {{"metric": "Transaction Volume", "target": "$10,000/day", "measurement": "On-chain data"}}
  ]
}}
```

⚠️ **IMPORTANT**: You must follow the JSON format exactly. Ideas will not be saved if the format is incorrect.
**IMPORTANT**: All content must be written in English.
"""

    def create_convergence_prompt(
        self,
        topic: str,
        ideas: List[Dict[str, Any]],
        agent_personality: Dict[str, str],
        round_num: int,
    ) -> str:
        """Create prompt for convergence phase."""
        personality_desc = "\n".join(f"- {k}: {v}" for k, v in agent_personality.items())

        ideas_section = ""
        for i, idea in enumerate(ideas, 1):
            ideas_section += f"""
### Idea {i}: {idea.get('title', 'Untitled')}
Proposer: {idea.get('agent', 'Unknown')}
Content: {idea.get('content', '')}
Score: {idea.get('score', 'N/A')}
"""

        return f"""You are an evaluation expert with the following characteristics:
{personality_desc}

## Discussion Topic
{topic}

## Ideas to Evaluate
{ideas_section}

## Evaluation Criteria (Weighted - Detailed evaluation basis required for each item)

**Weight Distribution:**
- Feasibility: 25%
- Mossland Relevance: 20%
- **Novelty: 30%** ⬆️ (Most important - differentiation from existing solutions)
- Impact: 15%
- Urgency: 10%

1. **Feasibility** (1-10, weight 25%)
   - Possibility of MVP implementation within 1-2 weeks
   - Maturity of required tech stack
   - Complexity relative to team capabilities

2. **Mossland Relevance** (1-10, weight 20%)
   - Synergy effects within Mossland ecosystem
   - Use of MOC token or NFT
   - Community value creation

3. **Novelty** (1-10, weight 30%) ⭐ Key criterion
   - Differentiation from existing market solutions
   - Technical newness
   - Business model innovation
   - ⚠️ Lower score if similar idea already exists
   - 💡 Higher score for completely new approaches

4. **Impact** (1-10, weight 15%)
   - Potential for new user acquisition
   - Revenue model possibility
   - Viral growth potential

5. **Urgency** (1-10, weight 10%)
   - Market timing
   - Competitor trends
   - Mossland roadmap fit

## Instructions

### Detailed Evaluation for Each Idea (Required)
```
### Idea N: [Title]
- Feasibility: X/10 - [specific basis, 50+ characters]
- Impact: X/10 - [specific basis, 50+ characters]
- Innovation: X/10 - [specific basis, 50+ characters]
- Risk: X/10 - [specific basis, 50+ characters]
- Urgency: X/10 - [specific basis, 50+ characters]
- **Total Score**: XX/50
```

### Final Analysis
1. **Top 3 Ideas** selection and reasons (100+ characters each)
   - Evaluate novelty (30% weight) with particular importance
2. **Similar Idea Consolidation Plan** (if applicable)
   - Boldly merge or give lower scores to duplicate ideas
3. **Final Recommendation**: 1 idea and reason (150+ characters)
   - Select the most novel yet feasible idea

### Weighted Score Calculation
```
Final Score = (Feasibility × 0.25) + (Relevance × 0.20) + (Novelty × 0.30) + (Impact × 0.15) + (Urgency × 0.10)
```

This is Round {round_num} evaluation. Please evaluate novelty as the most important criterion.
**IMPORTANT**: All content must be written in English.
"""

    def create_planning_prompt(
        self,
        topic: str,
        selected_ideas: List[Dict[str, Any]],
        agent_personality: Dict[str, str],
        agent_expertise: str,
        round_num: int,
        draft_plan: Optional[str] = None,
    ) -> str:
        """Create prompt for planning phase."""
        personality_desc = "\n".join(f"- {k}: {v}" for k, v in agent_personality.items())

        ideas_section = "\n".join(
            f"- {idea.get('title', 'Untitled')}: {idea.get('summary', idea.get('content', '')[:200])}"
            for idea in selected_ideas
        )

        if draft_plan:
            return f"""You are an expert in {agent_expertise} with the following personality traits:
{personality_desc}

## Discussion Topic
{topic}

## Current Draft Plan
{draft_plan}

## Instructions
From the perspective of {agent_expertise}, review this plan and provide feedback:

1. **Strengths**: What's good about this plan
2. **Weaknesses**: Areas that need improvement
3. **Risks**: Expected risk factors
4. **Specific Suggestions**: How can this be improved?

Finally, judge this plan as one of [Approved/Needs Revision/Rejected].
This is Round {round_num} review.
**IMPORTANT**: All content must be written in English.
"""
        else:
            return f"""You are an expert in {agent_expertise} with the following personality traits:
{personality_desc}

## Discussion Topic
{topic}

## Selected Ideas
{ideas_section}

## Instructions
Based on the above ideas, create a **detailed and actionable implementation plan**.

### Plan Writing Rules (Must Follow)

**Project Title Rules:**
- Title must be at least 30 characters, capturing the core value of the project
- Bad example: "DeFi Tool", "NFT Platform"
- Good example: "AI-Powered DeFi Portfolio Auto-Rebalancing System Integrated with Mossland Ecosystem"

---

### 1. Project Overview (Write in Detail)
- **Project Name**: [Specific and descriptive name]
- **One-line Description**: [Core value explained in under 50 characters]
- **Goals**: [At least 3 specific goals to achieve]
- **Target Users**: [Who will use this, expected number of users]
- **Estimated Duration**: [Total development period, MVP vs full version]
- **Estimated Cost**: [Labor costs, infrastructure costs, etc.]

### 2. Technical Architecture
- **Frontend**: [React/Next.js/Vue etc. + reason for choice]
- **Backend**: [Python/Node.js etc. + reason for choice]
- **Database**: [PostgreSQL/MongoDB etc. + reason for choice]
- **Blockchain Integration**: [Which chain, which protocol]
- **External APIs**: [External services to be used]
- **System Architecture Diagram**: [Brief text description]

### 3. Detailed Execution Plan

#### Week 1: Foundation Setup
- [ ] Task 1: [Specific task description]
- [ ] Task 2: [Specific task description]
- **Milestone**: [Completion criteria for this week]

#### Week 2: Core Feature Development
- [ ] Task 1: [Specific task description]
- [ ] Task 2: [Specific task description]
- **Milestone**: [Completion criteria for this week]

### 4. Risk Management
| Risk | Probability | Impact | Mitigation Strategy |
|------|-------------|--------|---------------------|
| [Specific risk] | High/Medium/Low | High/Medium/Low | [Response plan] |

### 5. Key Performance Indicators (KPIs)
| Metric | Target | Measurement Method | Measurement Frequency |
|--------|--------|-------------------|----------------------|
| DAU | 500 users | Analytics | Daily |
| Trading Volume | $10,000/day | On-chain data | Daily |

### 6. Future Expansion Plans
- Phase 2 Features: [...]
- Long-term Vision: [...]

Write an in-depth and actionable plan that showcases your expertise in {agent_expertise}.
This is Round {round_num} planning.
**IMPORTANT**: All content must be written in English.
"""

    def format_debate_summary(
        self,
        phase_results: List[PhaseResult],
        final_plan: str,
    ) -> str:
        """Format complete debate summary."""
        summary_parts = [
            "# Multi-Agent Debate Results",
            "",
            f"Generated at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
            "",
        ]

        # Phase summaries
        for result in phase_results:
            phase_name = {
                DebatePhase.DIVERGENCE: "Divergence Phase",
                DebatePhase.CONVERGENCE: "Convergence Phase",
                DebatePhase.PLANNING: "Planning Phase",
            }.get(result.phase, result.phase.value)

            summary_parts.append(f"## {phase_name}")
            summary_parts.append(f"- Rounds: {len(result.rounds)}")
            summary_parts.append(f"- Duration: {result.duration_seconds:.1f}s")
            summary_parts.append(f"- Tokens Used: {result.total_tokens:,}")
            summary_parts.append(f"- Cost: ${result.total_cost:.4f}")
            summary_parts.append("")

            if result.output:
                if result.phase == DebatePhase.DIVERGENCE:
                    ideas = result.output.get("ideas", [])
                    summary_parts.append(f"### Ideas Generated: {len(ideas)}")
                    for idea in ideas[:5]:
                        summary_parts.append(f"- {idea.get('title', 'Untitled')}")

                elif result.phase == DebatePhase.CONVERGENCE:
                    selected = result.output.get("selected_ideas", [])
                    summary_parts.append(f"### Selected Ideas: {len(selected)}")
                    for idea in selected:
                        summary_parts.append(f"- {idea.get('title', 'Untitled')} (Score: {idea.get('score', 'N/A')})")

                elif result.phase == DebatePhase.PLANNING:
                    summary_parts.append("### Planning Review Results")
                    approvals = result.output.get("approvals", 0)
                    total = result.output.get("total_votes", 0)
                    summary_parts.append(f"- Approvals: {approvals}/{total}")

            summary_parts.append("")

        # Final plan
        summary_parts.append("---")
        summary_parts.append("")
        summary_parts.append("# Final Implementation Plan")
        summary_parts.append("")
        summary_parts.append(final_plan)

        return "\n".join(summary_parts)
