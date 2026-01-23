"""
Auto-scoring module for ideas.

Provides automatic scoring of ideas based on feasibility, relevance, novelty, and impact.
"""

import json
import re
from dataclasses import dataclass, asdict
from typing import Optional

from ..llm.router import HybridLLMRouter
from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class IdeaScore:
    """Score breakdown for an idea."""
    feasibility: float  # 실현 가능성 (0-10): 1-2주 내 MVP 구현 가능성
    relevance: float    # Mossland 관련성 (0-10): Mossland/Web3 생태계 적합성
    novelty: float      # 참신성 (0-10): 기존 솔루션 대비 차별화
    impact: float       # 영향력 (0-10): 사용자 가치 및 비즈니스 임팩트

    @property
    def total(self) -> float:
        """Calculate weighted average score."""
        return (self.feasibility + self.relevance + self.novelty + self.impact) / 4

    def should_promote(self, threshold: float = 7.0) -> bool:
        """Check if idea should be auto-promoted to planning phase."""
        return self.total >= threshold

    def should_archive(self, threshold: float = 4.0) -> bool:
        """Check if idea should be archived (low quality)."""
        return self.total < threshold

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            **asdict(self),
            'total': self.total,
        }


class IdeaScorer:
    """
    Auto-scorer for ideas generated from debates.

    Uses local LLM to evaluate ideas on multiple dimensions and
    determine whether they should be promoted to planning or archived.
    """

    SCORE_PROMPT = """당신은 Web3 프로젝트 아이디어 평가 전문가입니다. 다음 아이디어를 4가지 차원에서 0-10점으로 평가해주세요.

## 평가할 아이디어
{idea_content}

## 추가 컨텍스트
{context}

## 평가 기준

1. **feasibility (실현 가능성)**: 1-2주 내 MVP로 구현 가능한가?
   - 10: 기존 라이브러리/API로 즉시 구현 가능
   - 7-9: 약간의 개발 필요하지만 단기간 구현 가능
   - 4-6: 상당한 개발 노력 필요
   - 1-3: 복잡한 인프라나 대규모 팀 필요

2. **relevance (Mossland 관련성)**: Mossland/Web3 생태계와 관련이 있는가?
   - 10: Mossland 핵심 비즈니스와 직접 연관
   - 7-9: Web3/블록체인 생태계에 명확한 적용점
   - 4-6: 간접적 연관성 존재
   - 1-3: 관련성 낮음

3. **novelty (참신성)**: 기존 솔루션과 차별화되는가?
   - 10: 시장에 없는 완전히 새로운 접근
   - 7-9: 기존 솔루션의 의미있는 개선
   - 4-6: 기존 솔루션과 비슷하지만 일부 차별점
   - 1-3: 이미 많은 유사 솔루션 존재

4. **impact (영향력)**: 사용자 가치와 비즈니스 임팩트가 있는가?
   - 10: 대규모 사용자 문제 해결, 높은 수익 잠재력
   - 7-9: 명확한 사용자 니즈, 괜찮은 비즈니스 모델
   - 4-6: 제한된 사용자 그룹, 작은 비즈니스 임팩트
   - 1-3: 사용자 가치 불분명, 비즈니스 모델 부재

## 응답 형식
JSON으로만 응답해주세요:
```json
{{
  "feasibility": <0-10 사이 숫자>,
  "relevance": <0-10 사이 숫자>,
  "novelty": <0-10 사이 숫자>,
  "impact": <0-10 사이 숫자>,
  "reasoning": "<각 점수에 대한 간단한 이유>"
}}
```"""

    def __init__(
        self,
        router: Optional[HybridLLMRouter] = None,
        promote_threshold: float = 7.0,
        archive_threshold: float = 4.0,
    ):
        """
        Initialize idea scorer.

        Args:
            router: HybridLLMRouter for LLM calls (uses local models)
            promote_threshold: Minimum score to auto-promote to planning
            archive_threshold: Score below which ideas are archived
        """
        self._router = router
        self.promote_threshold = promote_threshold
        self.archive_threshold = archive_threshold

    @property
    def router(self) -> HybridLLMRouter:
        """Lazy-loaded HybridLLMRouter."""
        if self._router is None:
            self._router = HybridLLMRouter()
        return self._router

    async def score_idea(
        self,
        idea_content: str,
        context: str = "",
    ) -> IdeaScore:
        """
        Score an idea using local LLM.

        Args:
            idea_content: The idea content to score
            context: Additional context (debate topic, trends, etc.)

        Returns:
            IdeaScore with scores for each dimension
        """
        prompt = self.SCORE_PROMPT.format(
            idea_content=idea_content,
            context=context or "추가 컨텍스트 없음",
        )

        try:
            response = await self.router.route(
                prompt=prompt,
                task_type="evaluation",
                force_local=True,
                quality="normal",
            )

            score = self._parse_score_response(response.content)
            logger.info(
                f"Scored idea: feasibility={score.feasibility}, "
                f"relevance={score.relevance}, novelty={score.novelty}, "
                f"impact={score.impact}, total={score.total:.2f}"
            )
            return score

        except Exception as e:
            logger.error(f"Failed to score idea: {e}")
            # Return neutral score on error
            return IdeaScore(
                feasibility=5.0,
                relevance=5.0,
                novelty=5.0,
                impact=5.0,
            )

    def _parse_score_response(self, response: str) -> IdeaScore:
        """Parse LLM response into IdeaScore."""
        try:
            # Extract JSON from response
            json_match = re.search(r"```json\s*(.*?)\s*```", response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find raw JSON
                json_str = response

            data = json.loads(json_str)

            return IdeaScore(
                feasibility=float(data.get("feasibility", 5.0)),
                relevance=float(data.get("relevance", 5.0)),
                novelty=float(data.get("novelty", 5.0)),
                impact=float(data.get("impact", 5.0)),
            )

        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
            logger.warning(f"Failed to parse score response: {e}")
            logger.debug(f"Response was: {response[:500]}")
            # Return neutral score
            return IdeaScore(
                feasibility=5.0,
                relevance=5.0,
                novelty=5.0,
                impact=5.0,
            )

    async def score_and_decide(
        self,
        idea_content: str,
        context: str = "",
    ) -> tuple[IdeaScore, str]:
        """
        Score an idea and decide its fate.

        Args:
            idea_content: The idea content to score
            context: Additional context

        Returns:
            Tuple of (IdeaScore, decision) where decision is one of:
            - "promote": Should be promoted to planning
            - "archive": Should be archived (low quality)
            - "pending": Needs further review (middle score)
        """
        score = await self.score_idea(idea_content, context)

        if score.should_promote(self.promote_threshold):
            return score, "promote"
        elif score.should_archive(self.archive_threshold):
            return score, "archive"
        else:
            return score, "pending"


__all__ = ["IdeaScore", "IdeaScorer"]
