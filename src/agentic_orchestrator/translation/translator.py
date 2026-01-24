"""
ContentTranslator - Bidirectional translation between English and Korean.

Uses llama3.3:70b for high-quality translation of ideas and plans.
Automatically detects source language and translates accordingly:
- Korean content → English (main field) + Korean (*_ko field)
- English content → English (main field) + Korean translation (*_ko field)
"""

import logging
from typing import Optional, Dict, Tuple

from ..llm.router import HybridLLMRouter
from ..db.models import Idea, Plan

logger = logging.getLogger(__name__)


class ContentTranslator:
    """Bidirectional content translator for English and Korean."""

    # Translation model (local, free)
    DEFAULT_MODEL = "llama3.3:70b"

    # System prompts for each direction
    SYSTEM_PROMPT_KO_TO_EN = """You are a professional English translator specializing in technology and startup content.

Your task is to translate Korean text to natural, fluent English.

Guidelines:
1. Maintain the original tone, style, and formatting
2. Keep technical terms as they are (e.g., API, SDK, NFT, DeFi, Web3, Mossland)
3. Use professional English suitable for business/tech documents
4. Preserve any markdown formatting in the original text
5. Do not add explanations or comments - only provide the translation
6. If the text contains section headers, translate them properly

Output only the translated English text, nothing else."""

    SYSTEM_PROMPT_EN_TO_KO = """You are a professional Korean translator specializing in technology and startup content.

Your task is to translate English text to natural, fluent Korean.

Guidelines:
1. Maintain the original tone, style, and formatting
2. Keep technical terms in English where appropriate (e.g., API, SDK, NFT, DeFi, Web3, Mossland)
3. Use professional Korean suitable for business/tech documents
4. Preserve any markdown formatting in the original text
5. Do not add explanations or comments - only provide the translation
6. If the text contains section headers, translate them properly

Output only the translated Korean text, nothing else."""

    def __init__(self, router: Optional[HybridLLMRouter] = None):
        """Initialize translator with LLM router."""
        self.router = router or HybridLLMRouter()

    def _detect_language(self, text: str) -> str:
        """
        Detect if text is primarily Korean or English.

        Args:
            text: Text to analyze

        Returns:
            'ko' if Korean, 'en' if English
        """
        if not text:
            return 'en'

        # Count Korean characters (Hangul syllables range)
        korean_chars = sum(1 for c in text if '\uac00' <= c <= '\ud7af')
        # Count ASCII letters
        ascii_chars = sum(1 for c in text if c.isascii() and c.isalpha())

        total_chars = korean_chars + ascii_chars
        if total_chars == 0:
            return 'en'

        korean_ratio = korean_chars / total_chars
        return 'ko' if korean_ratio > 0.3 else 'en'

    async def translate_to_english(self, text: str) -> str:
        """
        Translate Korean text to English.

        Args:
            text: Korean text to translate

        Returns:
            Translated English text
        """
        if not text or not text.strip():
            return ""

        # Skip if already mostly English
        if self._detect_language(text) == 'en':
            logger.info("Text appears to already be English, skipping translation")
            return text

        prompt = f"""Translate the following Korean text to English:

---
{text}
---

English translation:"""

        try:
            response = await self.router.route(
                prompt=prompt,
                system=self.SYSTEM_PROMPT_KO_TO_EN,
                model=self.DEFAULT_MODEL,
                task_type="translation",
                quality="high",
                temperature=0.3,
                force_local=True,
            )

            translated = response.content.strip()

            # Remove any wrapper text the model might add
            if translated.lower().startswith("english translation:"):
                translated = translated[len("English translation:"):].strip()

            # Remove markdown separator markers that the model might add
            if translated.startswith("---"):
                translated = translated[3:].strip()
            if translated.endswith("---"):
                translated = translated[:-3].strip()

            logger.info(
                f"Translated KO→EN ({len(text)} chars -> {len(translated)} chars) "
                f"using {response.model}"
            )

            return translated

        except Exception as e:
            logger.error(f"Translation KO→EN failed: {e}")
            return ""

    async def translate_to_korean(self, text: str) -> str:
        """
        Translate English text to Korean.

        Args:
            text: English text to translate

        Returns:
            Translated Korean text
        """
        if not text or not text.strip():
            return ""

        # Skip if already mostly Korean
        if self._detect_language(text) == 'ko':
            logger.info("Text appears to already be Korean, skipping translation")
            return text

        prompt = f"""Translate the following English text to Korean:

---
{text}
---

Korean translation:"""

        try:
            response = await self.router.route(
                prompt=prompt,
                system=self.SYSTEM_PROMPT_EN_TO_KO,
                model=self.DEFAULT_MODEL,
                task_type="translation",
                quality="high",
                temperature=0.3,
                force_local=True,
            )

            translated = response.content.strip()

            # Remove any wrapper text the model might add
            if translated.startswith("Korean translation:"):
                translated = translated[len("Korean translation:"):].strip()

            # Remove markdown separator markers that the model might add
            if translated.startswith("---"):
                translated = translated[3:].strip()
            if translated.endswith("---"):
                translated = translated[:-3].strip()

            logger.info(
                f"Translated EN→KO ({len(text)} chars -> {len(translated)} chars) "
                f"using {response.model}"
            )

            return translated

        except Exception as e:
            logger.error(f"Translation EN→KO failed: {e}")
            return ""

    async def ensure_bilingual(self, text: str) -> Tuple[str, str]:
        """
        Ensure text is available in both English and Korean.

        Args:
            text: Original text (can be Korean or English)

        Returns:
            Tuple of (english_text, korean_text)
        """
        if not text or not text.strip():
            return ("", "")

        source_lang = self._detect_language(text)

        if source_lang == 'ko':
            # Original is Korean, translate to English
            korean_text = text
            english_text = await self.translate_to_english(text)
        else:
            # Original is English, translate to Korean
            english_text = text
            korean_text = await self.translate_to_korean(text)

        return (english_text, korean_text)

    async def translate_idea_bilingual(self, idea_data: Dict) -> Dict:
        """
        Process idea data to ensure bilingual content.

        If content is Korean: translate to English for main fields, keep Korean in *_ko
        If content is English: keep English in main fields, translate to Korean for *_ko

        Args:
            idea_data: Dict with title, summary, description

        Returns:
            Updated dict with both main and *_ko fields populated
        """
        result = dict(idea_data)

        # Process title
        if idea_data.get('title'):
            en, ko = await self.ensure_bilingual(idea_data['title'])
            result['title'] = en if en else idea_data['title']
            result['title_ko'] = ko if ko else idea_data['title']

        # Process summary
        if idea_data.get('summary'):
            en, ko = await self.ensure_bilingual(idea_data['summary'])
            result['summary'] = en if en else idea_data['summary']
            result['summary_ko'] = ko if ko else idea_data['summary']

        # Process description
        if idea_data.get('description'):
            en, ko = await self.ensure_bilingual(idea_data['description'])
            result['description'] = en if en else idea_data['description']
            result['description_ko'] = ko if ko else idea_data['description']

        return result

    async def translate_plan_bilingual(self, plan_data: Dict) -> Dict:
        """
        Process plan data to ensure bilingual content.

        Args:
            plan_data: Dict with title, final_plan

        Returns:
            Updated dict with both main and *_ko fields populated
        """
        result = dict(plan_data)

        # Process title
        if plan_data.get('title'):
            en, ko = await self.ensure_bilingual(plan_data['title'])
            result['title'] = en if en else plan_data['title']
            result['title_ko'] = ko if ko else plan_data['title']

        # Process final_plan (can be long)
        if plan_data.get('final_plan'):
            en, ko = await self.ensure_bilingual(plan_data['final_plan'])
            result['final_plan'] = en if en else plan_data['final_plan']
            result['final_plan_ko'] = ko if ko else plan_data['final_plan']

        return result
