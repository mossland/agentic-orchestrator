"""
Multi-stage debate system with diverse agent personas.

Orchestrates debates through three phases:
1. Divergence: Generate diverse ideas (16 agents)
2. Convergence: Filter and merge ideas (8 agents)
3. Planning: Create actionable plans (10 agents)
"""

import asyncio
import logging
import random
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable

from ..llm.router import HybridLLMRouter, LLMResponse
from ..personas import (
    AgentPersona,
    get_divergence_agents,
    get_convergence_agents,
    get_planning_agents,
    get_agent_by_id,
)
from ..personas.personalities import (
    ThinkingStyle,
    DecisionStyle,
    CommunicationStyle,
    ActionStyle,
)
from .protocol import (
    DebatePhase,
    DebateProtocol,
    DebateProtocolConfig,
    DebateMessage,
    DebateRound,
    PhaseResult,
    MessageType,
)

logger = logging.getLogger(__name__)


@dataclass
class Idea:
    """An idea generated during divergence phase."""
    id: str
    title: str
    content: str
    agent_id: str
    agent_name: str
    round_num: int
    scores: Dict[str, float] = field(default_factory=dict)
    merged_from: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def total_score(self) -> float:
        if not self.scores:
            return 0.0
        return sum(self.scores.values()) / len(self.scores)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "round_num": self.round_num,
            "scores": self.scores,
            "total_score": self.total_score,
            "merged_from": self.merged_from,
            "metadata": self.metadata,
        }


@dataclass
class MultiStageDebateResult:
    """Result of a complete multi-stage debate."""
    session_id: str
    topic: str
    context: str
    divergence_result: PhaseResult
    convergence_result: PhaseResult
    planning_result: PhaseResult
    final_plan: str
    all_ideas: List[Idea]
    selected_ideas: List[Idea]
    total_duration_seconds: float
    total_tokens: int
    total_cost: float
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "topic": self.topic,
            "context": self.context,
            "divergence_result": self.divergence_result.to_dict(),
            "convergence_result": self.convergence_result.to_dict(),
            "planning_result": self.planning_result.to_dict(),
            "final_plan": self.final_plan,
            "all_ideas": [i.to_dict() for i in self.all_ideas],
            "selected_ideas": [i.to_dict() for i in self.selected_ideas],
            "total_duration_seconds": self.total_duration_seconds,
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "created_at": self.created_at.isoformat(),
        }


class MultiStageDebate:
    """
    Orchestrates multi-stage debates with diverse agent personas.

    Flow:
    1. Divergence Phase (3 rounds)
       - 16 agents with different personalities generate ideas
       - Each round, 8 agents participate
       - Goal: Generate 20+ diverse ideas

    2. Convergence Phase (2 rounds)
       - 8 analyst agents evaluate and filter ideas
       - Score ideas on multiple criteria
       - Merge similar ideas
       - Select top 5 ideas

    3. Planning Phase (2 rounds)
       - 10 planning agents create and review plans
       - First round: Draft plans
       - Second round: Review and finalize
    """

    def __init__(
        self,
        router: HybridLLMRouter,
        protocol: Optional[DebateProtocol] = None,
        on_message: Optional[Callable[[DebateMessage], None]] = None,
        on_phase_complete: Optional[Callable[[PhaseResult], None]] = None,
    ):
        """
        Initialize multi-stage debate.

        Args:
            router: LLM router for model selection
            protocol: Debate protocol configuration
            on_message: Callback for each new message
            on_phase_complete: Callback when phase completes
        """
        self.router = router
        self.protocol = protocol or DebateProtocol()
        self.on_message = on_message
        self.on_phase_complete = on_phase_complete

        # Load agent personas
        self.divergence_agents = get_divergence_agents()
        self.convergence_agents = get_convergence_agents()
        self.planning_agents = get_planning_agents()

        # Session state
        self.session_id = str(uuid.uuid4())[:8]
        self.ideas: List[Idea] = []
        self.messages: List[DebateMessage] = []
        self.total_tokens = 0
        self.total_cost = 0.0

    async def run_debate(
        self,
        topic: str,
        context: str,
    ) -> MultiStageDebateResult:
        """
        Run complete multi-stage debate.

        Args:
            topic: Main topic for debate
            context: Background context (signals, trends, etc.)

        Returns:
            Complete debate result
        """
        start_time = datetime.utcnow()
        logger.info(f"Starting multi-stage debate: {topic}")
        logger.info(f"Session ID: {self.session_id}")

        # Phase 1: Divergence
        logger.info("=" * 50)
        logger.info("PHASE 1: DIVERGENCE")
        logger.info("=" * 50)
        divergence_result = await self._run_divergence_phase(topic, context)
        if self.on_phase_complete:
            self.on_phase_complete(divergence_result)

        # Phase 2: Convergence
        logger.info("=" * 50)
        logger.info("PHASE 2: CONVERGENCE")
        logger.info("=" * 50)
        convergence_result = await self._run_convergence_phase(topic)
        if self.on_phase_complete:
            self.on_phase_complete(convergence_result)

        # Phase 3: Planning
        logger.info("=" * 50)
        logger.info("PHASE 3: PLANNING")
        logger.info("=" * 50)
        planning_result = await self._run_planning_phase(topic)
        if self.on_phase_complete:
            self.on_phase_complete(planning_result)

        # Extract final plan
        final_plan = planning_result.output.get("final_plan", "No plan generated")

        # Calculate totals
        total_duration = (datetime.utcnow() - start_time).total_seconds()

        result = MultiStageDebateResult(
            session_id=self.session_id,
            topic=topic,
            context=context,
            divergence_result=divergence_result,
            convergence_result=convergence_result,
            planning_result=planning_result,
            final_plan=final_plan,
            all_ideas=self.ideas.copy(),
            selected_ideas=[i for i in self.ideas if i.total_score >= 7.0],
            total_duration_seconds=total_duration,
            total_tokens=self.total_tokens,
            total_cost=self.total_cost,
        )

        logger.info(f"Debate completed in {total_duration:.1f}s")
        logger.info(f"Total tokens: {self.total_tokens:,}")
        logger.info(f"Total cost: ${self.total_cost:.4f}")

        return result

    async def _run_divergence_phase(
        self,
        topic: str,
        context: str,
    ) -> PhaseResult:
        """Run divergence phase to generate diverse ideas."""
        phase_start = datetime.utcnow()
        rounds: List[DebateRound] = []
        phase_tokens = 0
        phase_cost = 0.0

        config = self.protocol.config
        agents = list(self.divergence_agents)

        for round_num in range(1, config.divergence_rounds + 1):
            logger.info(f"Divergence Round {round_num}")

            # Select agents for this round
            round_agents = self._select_agents_for_round(
                agents, config.divergence_agents_per_round
            )

            round_data = DebateRound(
                round_num=round_num,
                phase=DebatePhase.DIVERGENCE,
                topic=topic,
            )

            # Run agents in parallel
            tasks = []
            for agent in round_agents:
                task = self._run_divergence_agent(
                    agent=agent,
                    topic=topic,
                    context=context,
                    round_num=round_num,
                    previous_ideas=[i.title for i in self.ideas],
                )
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Agent error: {result}")
                    continue

                message, idea, tokens, cost = result
                round_data.add_message(message)
                if idea:
                    self.ideas.append(idea)
                phase_tokens += tokens
                phase_cost += cost

                if self.on_message:
                    self.on_message(message)

            # Check termination
            should_end, reason = self.protocol.should_end_phase(
                DebatePhase.DIVERGENCE,
                round_num,
                round_data.messages,
                len(self.ideas),
            )

            round_data.summary = f"Generated {len(round_data.messages)} responses, {len(self.ideas)} total ideas"
            rounds.append(round_data)

            if should_end:
                logger.info(f"Divergence ended: {reason}")
                break

        duration = (datetime.utcnow() - phase_start).total_seconds()
        self.total_tokens += phase_tokens
        self.total_cost += phase_cost

        return PhaseResult(
            phase=DebatePhase.DIVERGENCE,
            rounds=rounds,
            output={
                "ideas": [i.to_dict() for i in self.ideas],
                "total_ideas": len(self.ideas),
            },
            duration_seconds=duration,
            total_tokens=phase_tokens,
            total_cost=phase_cost,
        )

    async def _run_convergence_phase(self, topic: str) -> PhaseResult:
        """Run convergence phase to filter and score ideas."""
        phase_start = datetime.utcnow()
        rounds: List[DebateRound] = []
        phase_tokens = 0
        phase_cost = 0.0

        config = self.protocol.config
        agents = list(self.convergence_agents)

        for round_num in range(1, config.convergence_rounds + 1):
            logger.info(f"Convergence Round {round_num}")

            round_agents = self._select_agents_for_round(
                agents, config.convergence_agents_per_round
            )

            round_data = DebateRound(
                round_num=round_num,
                phase=DebatePhase.CONVERGENCE,
                topic=topic,
            )

            # Prepare ideas for evaluation
            ideas_for_eval = [i.to_dict() for i in self.ideas if i.total_score < 10]

            tasks = []
            for agent in round_agents:
                task = self._run_convergence_agent(
                    agent=agent,
                    topic=topic,
                    ideas=ideas_for_eval,
                    round_num=round_num,
                )
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Convergence agent error: {result}")
                    continue

                message, scores, tokens, cost = result
                round_data.add_message(message)

                # Apply scores to ideas
                for idea_id, score in scores.items():
                    idea = next((i for i in self.ideas if i.id == idea_id), None)
                    if idea:
                        idea.scores[message.agent_id] = score

                phase_tokens += tokens
                phase_cost += cost

                if self.on_message:
                    self.on_message(message)

            rounds.append(round_data)

        # Sort ideas by score and select top ones
        sorted_ideas = sorted(self.ideas, key=lambda x: x.total_score, reverse=True)
        selected_ideas = sorted_ideas[:config.top_ideas_to_keep]

        duration = (datetime.utcnow() - phase_start).total_seconds()
        self.total_tokens += phase_tokens
        self.total_cost += phase_cost

        return PhaseResult(
            phase=DebatePhase.CONVERGENCE,
            rounds=rounds,
            output={
                "selected_ideas": [i.to_dict() for i in selected_ideas],
                "all_scores": {i.id: i.total_score for i in self.ideas},
            },
            duration_seconds=duration,
            total_tokens=phase_tokens,
            total_cost=phase_cost,
        )

    async def _run_planning_phase(self, topic: str) -> PhaseResult:
        """Run planning phase to create final plan."""
        phase_start = datetime.utcnow()
        rounds: List[DebateRound] = []
        phase_tokens = 0
        phase_cost = 0.0

        config = self.protocol.config
        agents = list(self.planning_agents)

        # Get selected ideas
        sorted_ideas = sorted(self.ideas, key=lambda x: x.total_score, reverse=True)
        selected_ideas = sorted_ideas[:config.top_ideas_to_keep]

        draft_plan: Optional[str] = None
        approvals = 0
        total_votes = 0

        for round_num in range(1, config.planning_rounds + 1):
            logger.info(f"Planning Round {round_num}")

            round_agents = self._select_agents_for_round(
                agents, config.planning_agents_per_round
            )

            round_data = DebateRound(
                round_num=round_num,
                phase=DebatePhase.PLANNING,
                topic=topic,
            )

            if round_num == 1:
                # First round: Create draft plans
                tasks = []
                for agent in round_agents:
                    task = self._run_planning_agent_draft(
                        agent=agent,
                        topic=topic,
                        selected_ideas=[i.to_dict() for i in selected_ideas],
                        round_num=round_num,
                    )
                    tasks.append(task)

                results = await asyncio.gather(*tasks, return_exceptions=True)

                drafts = []
                for result in results:
                    if isinstance(result, Exception):
                        logger.error(f"Planning agent error: {result}")
                        continue

                    message, plan_content, tokens, cost = result
                    round_data.add_message(message)
                    drafts.append(plan_content)
                    phase_tokens += tokens
                    phase_cost += cost

                    if self.on_message:
                        self.on_message(message)

                # Merge drafts (simple: use first comprehensive one)
                if drafts:
                    draft_plan = max(drafts, key=len)

            else:
                # Subsequent rounds: Review and vote
                tasks = []
                for agent in round_agents:
                    task = self._run_planning_agent_review(
                        agent=agent,
                        topic=topic,
                        draft_plan=draft_plan or "",
                        round_num=round_num,
                    )
                    tasks.append(task)

                results = await asyncio.gather(*tasks, return_exceptions=True)

                for result in results:
                    if isinstance(result, Exception):
                        logger.error(f"Planning review error: {result}")
                        continue

                    message, is_approved, feedback, tokens, cost = result
                    round_data.add_message(message)
                    total_votes += 1
                    if is_approved:
                        approvals += 1
                    phase_tokens += tokens
                    phase_cost += cost

                    if self.on_message:
                        self.on_message(message)

            rounds.append(round_data)

        duration = (datetime.utcnow() - phase_start).total_seconds()
        self.total_tokens += phase_tokens
        self.total_cost += phase_cost

        return PhaseResult(
            phase=DebatePhase.PLANNING,
            rounds=rounds,
            output={
                "final_plan": draft_plan or "No plan generated",
                "approvals": approvals,
                "total_votes": total_votes,
                "approval_rate": approvals / total_votes if total_votes > 0 else 0,
            },
            duration_seconds=duration,
            total_tokens=phase_tokens,
            total_cost=phase_cost,
        )

    def _select_agents_for_round(
        self,
        agents: List[AgentPersona],
        count: int,
    ) -> List[AgentPersona]:
        """Select agents for a round, ensuring personality diversity."""
        if len(agents) <= count:
            return agents

        # Use diversity-aware selection
        selected = self._select_agents_with_diversity(agents, count)

        # Ensure at least one challenger is present
        selected = self._ensure_challenger_presence(selected, agents)

        return selected

    def _select_agents_with_diversity(
        self,
        agents: List[AgentPersona],
        count: int,
    ) -> List[AgentPersona]:
        """
        Select agents while maintaining personality axis balance.

        Balances across 4 personality axes:
        - Thinking: optimistic vs cautious
        - Decision: intuitive vs analytical
        - Communication: challenger vs supporter
        - Action: innovative vs pragmatic
        """
        selected: List[AgentPersona] = []

        # Track counts for each axis value
        personality_counts = {
            'thinking': {'optimistic': 0, 'cautious': 0},
            'decision': {'intuitive': 0, 'analytical': 0},
            'communication': {'challenger': 0, 'supporter': 0},
            'action': {'innovative': 0, 'pragmatic': 0},
        }

        # Shuffle agents for randomness
        shuffled = agents.copy()
        random.shuffle(shuffled)

        for agent in shuffled:
            if len(selected) >= count:
                break

            # Check if adding this agent maintains diversity
            if self._maintains_diversity(agent, personality_counts, len(selected)):
                selected.append(agent)
                self._update_personality_counts(agent, personality_counts)

        # If we couldn't fill with diversity constraints, add remaining randomly
        if len(selected) < count:
            remaining = [a for a in shuffled if a not in selected]
            for agent in remaining:
                if len(selected) >= count:
                    break
                selected.append(agent)
                self._update_personality_counts(agent, personality_counts)

        # Log diversity distribution
        logger.info(f"Selected agents personality distribution: {personality_counts}")

        return selected

    def _maintains_diversity(
        self,
        agent: AgentPersona,
        counts: dict,
        current_count: int,
    ) -> bool:
        """
        Check if adding this agent maintains reasonable diversity.

        Allows imbalance up to 2 agents difference per axis.
        """
        if current_count == 0:
            return True

        max_imbalance = 2  # Allow up to 2 agents difference

        personality = agent.personality

        # Check each axis
        thinking_val = personality.thinking.value
        decision_val = personality.decision.value
        communication_val = personality.communication.value
        action_val = personality.action.value

        # Get opposite values for each axis
        thinking_opposite = 'cautious' if thinking_val == 'optimistic' else 'optimistic'
        decision_opposite = 'analytical' if decision_val == 'intuitive' else 'intuitive'
        communication_opposite = 'supporter' if communication_val == 'challenger' else 'challenger'
        action_opposite = 'pragmatic' if action_val == 'innovative' else 'innovative'

        # Check if adding this agent would create too much imbalance
        if counts['thinking'][thinking_val] - counts['thinking'][thinking_opposite] >= max_imbalance:
            return False
        if counts['decision'][decision_val] - counts['decision'][decision_opposite] >= max_imbalance:
            return False
        if counts['communication'][communication_val] - counts['communication'][communication_opposite] >= max_imbalance:
            return False
        if counts['action'][action_val] - counts['action'][action_opposite] >= max_imbalance:
            return False

        return True

    def _update_personality_counts(
        self,
        agent: AgentPersona,
        counts: dict,
    ) -> None:
        """Update personality axis counts for the agent."""
        personality = agent.personality

        counts['thinking'][personality.thinking.value] += 1
        counts['decision'][personality.decision.value] += 1
        counts['communication'][personality.communication.value] += 1
        counts['action'][personality.action.value] += 1

    def _ensure_challenger_presence(
        self,
        selected: List[AgentPersona],
        all_agents: List[AgentPersona],
    ) -> List[AgentPersona]:
        """
        Ensure at least one challenger-type agent is present.

        Challenger types are agents with CommunicationStyle.CHALLENGER
        who can provide critical feedback and challenging questions.
        """
        # Check if any selected agent is a challenger
        has_challenger = any(
            agent.personality.communication == CommunicationStyle.CHALLENGER
            for agent in selected
        )

        if has_challenger:
            return selected

        # Find a challenger from all agents that's not already selected
        challengers = [
            a for a in all_agents
            if a.personality.communication == CommunicationStyle.CHALLENGER
            and a not in selected
        ]

        if challengers and selected:
            # Replace the last selected agent with a challenger
            challenger = random.choice(challengers)
            selected[-1] = challenger
            logger.info(f"Ensured challenger presence: replaced with {challenger.name}")

        return selected

    def _calculate_idea_similarity(
        self,
        existing_ideas: List[str],
    ) -> tuple[float, List[str]]:
        """
        Calculate overall similarity among existing ideas.

        Uses Jaccard similarity on tokenized titles.

        Returns:
            (average_similarity, list of most common keywords)
        """
        if len(existing_ideas) < 2:
            return 0.0, []

        # Tokenize all ideas
        all_tokens: List[set] = []
        token_counts: Dict[str, int] = {}

        for idea in existing_ideas:
            tokens = set(idea.lower().split())
            all_tokens.append(tokens)
            for token in tokens:
                if len(token) > 2:  # Ignore very short tokens
                    token_counts[token] = token_counts.get(token, 0) + 1

        # Calculate average pairwise similarity
        total_similarity = 0.0
        pair_count = 0

        for i in range(len(all_tokens)):
            for j in range(i + 1, len(all_tokens)):
                intersection = len(all_tokens[i] & all_tokens[j])
                union = len(all_tokens[i] | all_tokens[j])
                if union > 0:
                    total_similarity += intersection / union
                    pair_count += 1

        avg_similarity = total_similarity / pair_count if pair_count > 0 else 0.0

        # Find most common keywords (appearing in 50%+ of ideas)
        threshold = len(existing_ideas) / 2
        common_keywords = [
            token for token, count in token_counts.items()
            if count >= threshold
        ]

        return avg_similarity, sorted(common_keywords, key=lambda x: token_counts[x], reverse=True)[:5]

    def _get_similarity_feedback(
        self,
        previous_ideas: List[str],
    ) -> str:
        """
        Generate feedback about idea similarity for prompts.

        Helps agents understand how to differentiate their ideas.
        """
        if len(previous_ideas) < 3:
            return ""

        avg_similarity, common_keywords = self._calculate_idea_similarity(previous_ideas)

        feedback_parts = []

        if avg_similarity > 0.4:
            feedback_parts.append(
                f"\n⚠️ **주의**: 기존 아이디어들의 평균 유사도가 {avg_similarity*100:.0f}%로 높습니다. "
                "완전히 다른 관점이나 접근 방식을 시도해주세요."
            )

        if common_keywords:
            feedback_parts.append(
                f"\n📊 자주 등장하는 키워드: {', '.join(common_keywords)}\n"
                "→ 이 키워드들을 피하고 새로운 영역을 탐색해보세요."
            )

        if avg_similarity > 0.3:
            feedback_parts.append(
                "\n💡 차별화 힌트:\n"
                "- 다른 사용자층을 타겟팅해보세요\n"
                "- 다른 기술 스택이나 플랫폼을 고려해보세요\n"
                "- 완전히 다른 비즈니스 모델을 제안해보세요\n"
                "- 단기/장기 관점을 바꿔보세요"
            )

        return "\n".join(feedback_parts)

    async def _run_divergence_agent(
        self,
        agent: AgentPersona,
        topic: str,
        context: str,
        round_num: int,
        previous_ideas: List[str],
    ) -> tuple[DebateMessage, Optional[Idea], int, float]:
        """Run a single divergence agent."""
        personality_modifiers = agent.personality.get_behavior_modifiers()

        prompt = self.protocol.create_divergence_prompt(
            topic=topic,
            context=context,
            agent_personality=personality_modifiers,
            round_num=round_num,
            previous_ideas=previous_ideas,
        )

        # Add similarity feedback to encourage differentiation
        similarity_feedback = self._get_similarity_feedback(previous_ideas)
        if similarity_feedback:
            prompt += similarity_feedback

        system_prompt = f"""당신은 {agent.name}입니다.
역할: {agent.role}
전문분야: {', '.join(agent.expertise)}

{agent.system_prompt_template}

성향: {agent.personality.get_trait_description()}

당신의 고유한 관점과 전문성으로 의견을 제시하세요."""

        try:
            response = await self.router.route(
                prompt=prompt,
                task_type="idea_generation",
                system=system_prompt,
                quality="normal",
                temperature=self.protocol.get_temperature(DebatePhase.DIVERGENCE),
                max_tokens=self.protocol.config.max_tokens_per_response,
            )

            # Create message
            message = DebateMessage(
                id=f"div-{self.session_id}-{round_num}-{agent.id}",
                phase=DebatePhase.DIVERGENCE,
                round=round_num,
                agent_id=agent.id,
                agent_name=agent.name,
                message_type=MessageType.INITIAL_IDEA,
                content=response.content,
                metadata={
                    "model": response.model,
                    "provider": response.provider,
                    "role": agent.role,
                },
            )

            # Extract idea
            idea = self._extract_idea_from_response(
                response.content, agent, round_num
            )

            return message, idea, response.input_tokens + response.output_tokens, response.cost

        except Exception as e:
            logger.error(f"Divergence agent {agent.id} failed: {e}")
            raise

    async def _run_convergence_agent(
        self,
        agent: AgentPersona,
        topic: str,
        ideas: List[Dict[str, Any]],
        round_num: int,
    ) -> tuple[DebateMessage, Dict[str, float], int, float]:
        """Run a single convergence agent."""
        personality_modifiers = agent.personality.get_behavior_modifiers()

        prompt = self.protocol.create_convergence_prompt(
            topic=topic,
            ideas=ideas,
            agent_personality=personality_modifiers,
            round_num=round_num,
        )

        system_prompt = f"""당신은 {agent.name}입니다.
역할: {agent.role}
전문분야: {agent.expertise}

아이디어를 평가하고 점수를 매기는 것이 당신의 임무입니다.
각 아이디어에 1-10점 사이의 점수를 부여하세요."""

        try:
            response = await self.router.route(
                prompt=prompt,
                task_type="evaluation",
                system=system_prompt,
                quality="normal",
                temperature=self.protocol.get_temperature(DebatePhase.CONVERGENCE),
                max_tokens=self.protocol.config.max_tokens_per_response,
            )

            message = DebateMessage(
                id=f"conv-{self.session_id}-{round_num}-{agent.id}",
                phase=DebatePhase.CONVERGENCE,
                round=round_num,
                agent_id=agent.id,
                agent_name=agent.name,
                message_type=MessageType.EVALUATION,
                content=response.content,
                metadata={
                    "model": response.model,
                    "provider": response.provider,
                },
            )

            # Extract scores from response
            scores = self._extract_scores_from_response(response.content, ideas)

            return message, scores, response.input_tokens + response.output_tokens, response.cost

        except Exception as e:
            logger.error(f"Convergence agent {agent.id} failed: {e}")
            raise

    async def _run_planning_agent_draft(
        self,
        agent: AgentPersona,
        topic: str,
        selected_ideas: List[Dict[str, Any]],
        round_num: int,
    ) -> tuple[DebateMessage, str, int, float]:
        """Run planning agent to create draft plan."""
        personality_modifiers = agent.personality.get_behavior_modifiers()

        prompt = self.protocol.create_planning_prompt(
            topic=topic,
            selected_ideas=selected_ideas,
            agent_personality=personality_modifiers,
            agent_expertise=agent.expertise,
            round_num=round_num,
        )

        system_prompt = f"""당신은 {agent.name}입니다.
역할: {agent.role}
전문분야: {agent.expertise}

실행 가능한 기획안을 작성하는 것이 당신의 임무입니다."""

        try:
            response = await self.router.route(
                prompt=prompt,
                task_type="final_plan",
                system=system_prompt,
                quality="high",  # Use better model for planning
                temperature=self.protocol.get_temperature(DebatePhase.PLANNING),
                max_tokens=self.protocol.config.max_tokens_per_response * 2,
            )

            message = DebateMessage(
                id=f"plan-{self.session_id}-{round_num}-{agent.id}",
                phase=DebatePhase.PLANNING,
                round=round_num,
                agent_id=agent.id,
                agent_name=agent.name,
                message_type=MessageType.PLAN_DRAFT,
                content=response.content,
                metadata={
                    "model": response.model,
                    "provider": response.provider,
                },
            )

            return message, response.content, response.input_tokens + response.output_tokens, response.cost

        except Exception as e:
            logger.error(f"Planning agent {agent.id} failed: {e}")
            raise

    async def _run_planning_agent_review(
        self,
        agent: AgentPersona,
        topic: str,
        draft_plan: str,
        round_num: int,
    ) -> tuple[DebateMessage, bool, str, int, float]:
        """Run planning agent to review plan."""
        personality_modifiers = agent.personality.get_behavior_modifiers()

        prompt = self.protocol.create_planning_prompt(
            topic=topic,
            selected_ideas=[],
            agent_personality=personality_modifiers,
            agent_expertise=agent.expertise,
            round_num=round_num,
            draft_plan=draft_plan,
        )

        system_prompt = f"""당신은 {agent.name}입니다.
역할: {agent.role}
전문분야: {agent.expertise}

기획안을 검토하고 피드백을 제공하세요.
마지막에 [승인] 또는 [수정요청] 또는 [반대]를 명시하세요."""

        try:
            response = await self.router.route(
                prompt=prompt,
                task_type="quality_check",
                system=system_prompt,
                quality="normal",
                temperature=self.protocol.get_temperature(DebatePhase.PLANNING),
                max_tokens=self.protocol.config.max_tokens_per_response,
            )

            message = DebateMessage(
                id=f"review-{self.session_id}-{round_num}-{agent.id}",
                phase=DebatePhase.PLANNING,
                round=round_num,
                agent_id=agent.id,
                agent_name=agent.name,
                message_type=MessageType.PLAN_REVIEW,
                content=response.content,
                metadata={
                    "model": response.model,
                    "provider": response.provider,
                },
            )

            # Check approval
            is_approved = "[승인]" in response.content or "[approve]" in response.content.lower()

            return message, is_approved, response.content, response.input_tokens + response.output_tokens, response.cost

        except Exception as e:
            logger.error(f"Planning review agent {agent.id} failed: {e}")
            raise

    def _validate_idea_content(self, content: str) -> tuple[bool, list[str]]:
        """
        Validate idea content against quality requirements.

        Checks for:
        - Required sections presence
        - Minimum character counts per section
        - JSON structure if present

        Returns:
            (is_valid, list of validation errors)
        """
        import json
        import re

        errors = []

        # Try to extract JSON content first
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
        if json_match:
            try:
                idea_json = json.loads(json_match.group(1))

                # Validate JSON structure
                required_fields = ['idea_title', 'core_analysis', 'proposal']
                for field in required_fields:
                    if field not in idea_json:
                        errors.append(f"JSON 필드 '{field}' 누락")

                # Validate title length
                title = idea_json.get('idea_title', '')
                if len(title) < 30:
                    errors.append(f"제목이 너무 짧음 ({len(title)}자 < 30자)")

                # Validate core_analysis length
                core = idea_json.get('core_analysis', '')
                if len(core) < 100:
                    errors.append(f"핵심 분석이 너무 짧음 ({len(core)}자 < 100자)")

                # Validate proposal description
                proposal = idea_json.get('proposal', {})
                if isinstance(proposal, dict):
                    desc = proposal.get('description', '')
                    if len(desc) < 150:
                        errors.append(f"제안 설명이 너무 짧음 ({len(desc)}자 < 150자)")

                    features = proposal.get('core_features', [])
                    if len(features) < 3:
                        errors.append(f"핵심 기능이 부족함 ({len(features)}개 < 3개)")

                return len(errors) == 0, errors

            except json.JSONDecodeError:
                # JSON parsing failed, fall through to text validation
                pass

        # Text-based validation (fallback)
        required_sections = [
            ("핵심 분석", 80),
            ("기회", 80),
            ("제안", 120),
            ("로드맵", 60),
        ]

        for section_name, min_chars in required_sections:
            # Look for section header patterns
            patterns = [
                rf'\*\*{section_name}\*\*[:\s]*([\s\S]*?)(?=\n\*\*|\n##|\n\d+\.|$)',
                rf'##\s*{section_name}[:\s]*([\s\S]*?)(?=\n##|\n\*\*|\n\d+\.|$)',
                rf'\d+\.\s*{section_name}[:\s]*([\s\S]*?)(?=\n\d+\.|\n##|\n\*\*|$)',
            ]

            found = False
            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    section_content = match.group(1).strip()
                    if len(section_content) >= min_chars:
                        found = True
                        break
                    else:
                        errors.append(f"'{section_name}' 섹션이 너무 짧음 ({len(section_content)}자 < {min_chars}자)")
                        found = True
                        break

            if not found and section_name not in content:
                errors.append(f"'{section_name}' 섹션 누락")

        return len(errors) == 0, errors

    def _score_title_quality(self, title: str) -> float:
        """
        Score title quality on a scale of 0-10.

        Scoring criteria:
        - Length (30-80 chars optimal): up to 3 points
        - Contains tech keywords: up to 3 points
        - Contains numbers/metrics: up to 2 points
        - Mossland relevance: up to 2 points

        Returns:
            Quality score (0.0 - 10.0)
        """
        import re

        score = 0.0

        # Length score (30-80 characters optimal)
        title_len = len(title)
        if 30 <= title_len <= 80:
            score += 3.0
        elif title_len > 80:
            score += 2.0
        elif title_len >= 20:
            score += 1.0

        # Tech keywords score
        tech_keywords = [
            'AI', 'DeFi', 'NFT', 'DAO', 'Web3', 'GPT', 'LLM', 'SDK', 'API',
            'DEX', 'CEX', 'AMM', 'TVL', 'APY', 'APR', 'L2', 'ZK', 'EVM',
            'Solidity', 'React', 'Python', 'TypeScript', 'Rust',
            'Uniswap', 'Aave', 'OpenAI', 'Claude', 'Anthropic',
            '블록체인', '메타버스', '스마트컨트랙트', '토큰', '지갑',
            '에이전트', '자동화', '분석', '트래킹', '대시보드', '플랫폼'
        ]
        tech_matches = sum(1 for kw in tech_keywords if kw.lower() in title.lower())
        score += min(tech_matches * 1.0, 3.0)

        # Numbers/metrics score
        if re.search(r'\d+', title):
            score += 1.0
        if re.search(r'%|\$|USD|KRW|ETH|BTC', title, re.IGNORECASE):
            score += 1.0

        # Mossland relevance score
        mossland_keywords = ['mossland', 'moc', 'moss', '모스', '모스랜드', 'ar', 'metaverse', '메타버스']
        if any(kw in title.lower() for kw in mossland_keywords):
            score += 2.0

        return min(score, 10.0)

    def _extract_idea_from_response(
        self,
        content: str,
        agent: AgentPersona,
        round_num: int,
    ) -> Optional[Idea]:
        """Extract idea from agent response.

        Title requirements:
        - Minimum 30 characters for specificity
        - Must not be a generic section header
        - Should contain specific keywords (tech names, project names, numbers)

        Supports both JSON and text formats.
        """
        import re
        import json

        # First, try to extract from JSON format
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
        if json_match:
            try:
                idea_json = json.loads(json_match.group(1))
                title = idea_json.get('idea_title', '')

                # Validate JSON-based idea
                is_valid, errors = self._validate_idea_content(content)
                if not is_valid:
                    logger.warning(f"Idea validation failed for {agent.name}: {errors}")
                    # Continue anyway but log the issues

                # Score title quality
                title_score = self._score_title_quality(title)
                logger.info(f"Title quality score for '{title[:50]}...': {title_score}/10")

                if len(title) >= 30 and title_score >= 4.0:
                    return Idea(
                        id=f"idea-{self.session_id}-{round_num}-{agent.id}",
                        title=title[:200],
                        content=content,
                        agent_id=agent.id,
                        agent_name=agent.name,
                        round_num=round_num,
                        metadata={
                            "format": "json",
                            "title_score": title_score,
                            "validation_errors": errors if not is_valid else [],
                            "proposal": idea_json.get('proposal', {}),
                            "kpis": idea_json.get('kpis', []),
                        }
                    )
                else:
                    logger.warning(f"Title too short or low quality: '{title}' (score: {title_score})")

            except json.JSONDecodeError as e:
                logger.debug(f"JSON parsing failed, falling back to text extraction: {e}")

        # Fallback to text-based extraction
        lines = content.strip().split("\n")

        # Generic section headers to skip (expanded list)
        skip_headers = [
            '핵심 분석', '기회', '리스크', '제안', '우선순위', '실행', '개요', '목표',
            '요약', '결론', '배경', '현황', '분석', '전략', '방안', '계획', '일정',
            '기대 효과', '예상 결과', '참고', '부록', '첨부', '서론', '본론',
            '소개', '개요', '요점', '핵심', 'summary', 'introduction', 'conclusion',
            'overview', 'background', 'analysis', 'proposal'
        ]

        def is_generic_header(text: str) -> bool:
            text_lower = text.lower().strip()
            # Check for exact matches or patterns like "1. 핵심 분석"
            for skip in skip_headers:
                if skip in text_lower:
                    return True
            # Check for numbered generic headers
            if re.match(r'^[\d]+[\.\)]\s*[가-힣]{2,4}$', text_lower):
                return True
            return False

        def has_specific_content(text: str) -> bool:
            """Check if title contains specific keywords that make it valuable."""
            specific_patterns = [
                r'(AI|DeFi|NFT|DAO|Web3|GPT|LLM|SDK|API)',  # Tech acronyms
                r'(Uniswap|Aave|OpenAI|Mossland|모스랜드)',  # Project names
                r'\d+',  # Contains numbers (metrics, versions)
                r'(홀더|유저|개발자|크리에이터)',  # User types
                r'(플랫폼|시스템|서비스|도구|봇)',  # Product types
            ]
            for pattern in specific_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return True
            return False

        title = None

        # Priority 1: Look for "## 아이디어: [제목]" format
        idea_pattern = r"##\s*아이디어[:\s]+(.+)"
        match = re.search(idea_pattern, content)
        if match:
            potential = match.group(1).strip()
            if len(potential) >= 30 and not is_generic_header(potential):
                title = potential

        # Priority 2: Look for "프로젝트 명:" or "프로젝트명:" format
        if not title:
            project_pattern = r"프로젝트\s*명[:\s]+(.+)"
            match = re.search(project_pattern, content)
            if match:
                potential = match.group(1).strip()
                if len(potential) >= 30 and not is_generic_header(potential):
                    title = potential

        # Priority 3: Look for "서비스명:" or "제품명:" format
        if not title:
            service_pattern = r"(서비스|제품|솔루션)\s*명[:\s]+(.+)"
            match = re.search(service_pattern, content)
            if match:
                potential = match.group(2).strip()
                if len(potential) >= 30 and not is_generic_header(potential):
                    title = potential

        # Priority 4: Try to find title from headers or bold text
        if not title:
            for line in lines:
                line = line.strip()
                if is_generic_header(line):
                    continue
                if line.startswith("##") and "아이디어" not in line:
                    potential = line.lstrip("#").strip()
                    if len(potential) >= 30 and has_specific_content(potential):
                        title = potential
                        break
                if line.startswith("**") and line.endswith("**"):
                    potential = line.strip("*").strip()
                    if len(potential) >= 30 and has_specific_content(potential):
                        title = potential
                        break

        # Priority 5: Use first substantial line with specific content
        if not title:
            for line in lines:
                line = line.strip()
                if line.startswith("#") or line.startswith("*") or line.startswith("-"):
                    continue
                if is_generic_header(line):
                    continue
                if len(line) >= 30 and len(line) < 200 and has_specific_content(line):
                    title = line
                    break

        # Fallback: Generate descriptive title from content analysis
        if not title or len(title) < 30:
            # Extract meaningful keywords from content
            tech_matches = re.findall(r'(AI|DeFi|NFT|DAO|Web3|블록체인|메타버스|에이전트|스마트 컨트랙트)', content[:1000])
            action_matches = re.findall(r'(자동화|분석|트래킹|모니터링|대시보드|최적화|통합|연동)', content[:1000])
            target_matches = re.findall(r'(홀더|유저|개발자|커뮤니티|투자자)', content[:1000])

            tech = list(dict.fromkeys(tech_matches))[:2]  # Unique, max 2
            actions = list(dict.fromkeys(action_matches))[:1]
            targets = list(dict.fromkeys(target_matches))[:1]

            parts = []
            if targets:
                parts.append(f"{targets[0]}를 위한")
            if tech:
                parts.append(' + '.join(tech))
            if actions:
                parts.append(f"{actions[0]} 시스템")
            else:
                parts.append("솔루션")

            if parts:
                title = f"Mossland {' '.join(parts)} 구축 방안"
            else:
                title = f"Mossland 생태계 확장을 위한 {agent.role} 관점의 혁신 전략"

            # Ensure minimum length
            if len(title) < 30:
                title = f"{agent.name}의 Mossland 생태계 혁신 아이디어 - {agent.role} 전문가 제안"

        # Validate content and score title
        is_valid, validation_errors = self._validate_idea_content(content)
        title_score = self._score_title_quality(title)

        if not is_valid:
            logger.warning(f"Text-based idea validation issues for {agent.name}: {validation_errors}")

        logger.info(f"Title quality score (text): '{title[:50]}...': {title_score}/10")

        return Idea(
            id=f"idea-{self.session_id}-{round_num}-{agent.id}",
            title=title[:200],  # Allow longer titles (up to 200 chars)
            content=content,
            agent_id=agent.id,
            agent_name=agent.name,
            round_num=round_num,
            metadata={
                "format": "text",
                "title_score": title_score,
                "validation_errors": validation_errors if not is_valid else [],
            }
        )

    def _extract_scores_from_response(
        self,
        content: str,
        ideas: List[Dict[str, Any]],
    ) -> Dict[str, float]:
        """Extract scores for ideas from evaluation response."""
        scores = {}

        # Simple heuristic: look for numbers 1-10 near idea references
        import re

        for idea in ideas:
            idea_id = idea.get("id", "")
            idea_title = idea.get("title", "")

            # Look for patterns like "아이디어 1: 8점" or "점수: 7"
            patterns = [
                rf"{re.escape(idea_title)}[^0-9]*(\d+)",
                rf"아이디어\s*\d+[^0-9]*(\d+)점",
                rf"점수[:\s]*(\d+)",
            ]

            for pattern in patterns:
                match = re.search(pattern, content)
                if match:
                    try:
                        score = float(match.group(1))
                        if 1 <= score <= 10:
                            scores[idea_id] = score
                            break
                    except ValueError:
                        continue

            # Default score if not found
            if idea_id not in scores:
                scores[idea_id] = 5.0  # Neutral score

        return scores


async def run_multi_stage_debate(
    router: HybridLLMRouter,
    topic: str,
    context: str,
    config: Optional[DebateProtocolConfig] = None,
    on_message: Optional[Callable[[DebateMessage], None]] = None,
    on_phase_complete: Optional[Callable[[PhaseResult], None]] = None,
) -> MultiStageDebateResult:
    """
    Convenience function to run a multi-stage debate.

    Args:
        router: LLM router
        topic: Debate topic
        context: Background context
        config: Optional protocol configuration
        on_message: Message callback
        on_phase_complete: Phase completion callback

    Returns:
        Debate result
    """
    protocol = DebateProtocol(config) if config else None
    debate = MultiStageDebate(
        router=router,
        protocol=protocol,
        on_message=on_message,
        on_phase_complete=on_phase_complete,
    )
    return await debate.run_debate(topic, context)
