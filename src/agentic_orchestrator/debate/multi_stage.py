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
        """Select agents for a round, ensuring diversity."""
        if len(agents) <= count:
            return agents

        # Shuffle and select
        shuffled = agents.copy()
        random.shuffle(shuffled)
        return shuffled[:count]

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

        system_prompt = f"""당신은 {agent.name}입니다.
역할: {agent.role}
전문분야: {agent.expertise}
{agent.backstory}

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

    def _extract_idea_from_response(
        self,
        content: str,
        agent: AgentPersona,
        round_num: int,
    ) -> Optional[Idea]:
        """Extract idea from agent response."""
        lines = content.strip().split("\n")

        # Try to find title (look for headers or first meaningful line)
        title = None
        for line in lines:
            line = line.strip()
            if line.startswith("#"):
                title = line.lstrip("#").strip()
                break
            if line.startswith("**") and line.endswith("**"):
                title = line.strip("*").strip()
                break
            if len(line) > 10 and len(line) < 100:
                title = line
                break

        if not title:
            title = f"{agent.name}의 제안"

        return Idea(
            id=f"idea-{self.session_id}-{round_num}-{agent.id}",
            title=title[:100],
            content=content,
            agent_id=agent.id,
            agent_name=agent.name,
            round_num=round_num,
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
