"""
Hermes AI Integration for BO2 Emblem Studio
============================================
Provides integration with Hermes Agent for intelligent emblem generation.
Supports multiple AI providers via Hermes Agent's unified interface.
"""

import os
import json
import asyncio
import aiohttp
import logging
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class AIProvider(Enum):
    """Supported AI providers via Hermes."""
    LOCAL = "local"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    NVIDIA = "nvidia"
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"
    LM_STUDIO = "lm_studio"
    VLLM = "vllm"
    CUSTOM = "custom"


@dataclass
class HermesConfig:
    """Configuration for Hermes AI connection."""
    provider: AIProvider = AIProvider.LOCAL
    endpoint: str = "http://localhost:8080"
    api_key: str = ""
    model: str = "nemotron-3-ultra"
    timeout: int = 60
    temperature: float = 0.7
    max_tokens: int = 4096
    # Custom provider settings
    custom_headers: Dict[str, str] = field(default_factory=dict)
    custom_body: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EmblemConcept:
    """Structured concept for emblem generation."""
    name: str
    description: str
    style: str = "default"
    color_scheme: str = "auto"
    symmetry: str = "bilateral"  # bilateral, radial, asymmetric
    complexity: int = 3  # 1-5
    elements: List[str] = field(default_factory=list)
    color_palette: List[Tuple[float, float, float]] = field(default_factory=list)
    composition_notes: str = ""


@dataclass
class EmblemPlan:
    """Complete plan for emblem generation."""
    concept: EmblemConcept
    layers: List[Dict[str, Any]] = field(default_factory=list)
    reasoning: str = ""
    estimated_layers: int = 0
    warnings: List[str] = field(default_factory=list)


class EmblemPromptBuilder:
    """Builds structured prompts for emblem generation."""
    
    SYSTEM_PROMPT = """You are an expert Black Ops 2 emblem designer. You create emblems using the BO2/Plutonium T6 emblem editor system.

EMBLEM SYSTEM SPECIFICATIONS:
- 32 layers maximum (index 0-31, lower index = further back)
- Each layer: shape_id (0-260), color (RGBA 0-1), position (pos_x, pos_y), scale (scale_x, scale_y log2), rotation (degrees), outlined (bool), flipped (bool)
- Coordinate system: center=(0,0), +Y=DOWN, pos 0.5 = edge of canvas
- Scale: true_scale = 2^scale_value (0=full size, -1=half, 1=double)
- Rotation: degrees, clockwise positive
- Shape categories: tools (137-197), type (217-252), emblems (38-136, 253-259), gear (0-37,260), ranks (198-216)

KEY SHAPES:
- 192: Full Circle (essential for round shapes)
- 137: Half Circle (jaws, eye sockets)
- 137 flipped: mirrored half circle
- 185: Heart (noses, details)
- 187: Triangle Wide (noses, teeth)
- 195: Rectangle Medium (teeth, straight edges)
- 183: Curved Line (cracks, details)
- 145/146: Ninja Star/Half Star (stars, spikes)
- 194: Diamond (eyes, geometric)
- 192: Full Circle (eyes, base shapes)
- 137/138: Half/Quarter Circle (organic curves)
- 139: Half Heart (ears, details)
- 145/146/147: Star/Shuriken variants
- 152: Tube (cylindrical parts)
- 195: Rectangle Medium (straight edges)
- 196: Square Full (blocky parts)
- 184: Smile Outline (mouth)
- 182: Biohazard (danger symbols)
- 187: Triangle Wide (sharp details)

COMPOSITION PRINCIPLES:
- Background first (index 0), foreground last (index 31)
- Symmetrical parts use flipped=True for mirror
- Layer order = depth order (0=back, 31=front)
- Scale 0 = full size, negative = smaller, positive = larger
- Position 0 = center, 0.5 = edge
- Colors: RGB 0-1, Alpha 0-1
- Outlined = thin stroke only
- Flipped = horizontal mirror

OUTPUT FORMAT:
Return JSON with:
{
  "concept": {
    "name": "name",
    "description": "visual description",
    "style": "style name",
    "symmetry": "bilateral|radial|asymmetric",
    "complexity": 1-5,
    "elements": ["element1", "element2"]
  },
  "layers": [
    {"index": 0, "shape_id": 192, "r":1,"g":0,"b":0,"a":1, "pos_x":0,"pos_y":0, "scale_x":0,"scale_y":0, "rotation":0, "outlined":false, "flipped":false},
    ...
  ],
  "reasoning": "explanation of design choices",
  "estimated_layers": N,
  "warnings": []
}"""

    @classmethod
    def build_prompt(cls, concept: 'EmblemConcept') -> str:
        """Build the complete prompt for the AI."""
        prompt = cls.SYSTEM_PROMPT + f"""

USER REQUEST:
Create an emblem: "{concept.name}"
Description: {concept.description}
Style: {concept.style}
Symmetry: {concept.symmetry}
Complexity: {concept.complexity}/5
Elements: {', '.join(concept.elements) if concept.elements else 'auto'}
Color scheme: {concept.color_scheme}
Notes: {concept.composition_notes}

Return the complete emblem plan as JSON."""
        return prompt


class HermesClient:
    """Client for communicating with Hermes Agent."""
    
    def __init__(self, config: HermesConfig):
        self.config = config
        self.session = None
        
    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def generate_emblem(self, concept: 'EmblemConcept') -> 'EmblemPlan':
        """Generate emblem plan via Hermes."""
        prompt = EmblemPromptBuilder.build_prompt(concept)
        
        # Prepare request based on provider
        if self.config.provider == AIProvider.LOCAL:
            return await self._call_local_hermes(prompt)
        elif self.config.provider == AIProvider.OPENAI:
            return await self._call_openai(prompt)
        elif self.config.provider == AIProvider.ANTHROPIC:
            return await self._call_anthropic(prompt)
        elif self.config.provider == AIProvider.GOOGLE:
            return await self._call_google(prompt)
        elif self.config.provider == AIProvider.OPENROUTER:
            return await self._call_openrouter(prompt)
        elif self.config.provider in (AIProvider.OLLAMA, AIProvider.LM_STUDIO, AIProvider.VLLM, AIProvider.NVIDIA):
            return await self._call_openai_compatible(prompt)
        else:
            return await self._call_custom(prompt)
    
    async def _call_local_hermes(self, prompt: str) -> 'EmblemPlan':
        """Call local Hermes Agent instance."""
        base = self.config.endpoint.rstrip('/')
        url = f"{base}/chat/completions" if base.endswith('/v1') else f"{base}/v1/chat/completions"
        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": EmblemPromptBuilder.SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "response_format": {"type": "json_object"}
        }
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
            
        async with self.session.post(url, json=payload, headers=headers) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return self._parse_response(data)
    
    async def _call_openai(self, prompt: str) -> 'EmblemPlan':
        """Call OpenAI API."""
        base = self.config.endpoint.rstrip('/')
        url = f"{base}/chat/completions" if base.endswith('/v1') else f"{base}/v1/chat/completions"
        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": EmblemPromptBuilder.SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "response_format": {"type": "json_object"}
        }
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.config.api_key}"}
        
        async with self.session.post(url, json=payload, headers=headers) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return self._parse_response(data)
    
    async def _call_anthropic(self, prompt: str) -> 'EmblemPlan':
        """Call Anthropic API."""
        base = self.config.endpoint.rstrip('/')
        url = f"{base}/messages" if base.endswith('/v1') else f"{base}/v1/messages"
        payload = {
            "model": self.config.model,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "system": EmblemPromptBuilder.SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": prompt}]
        }
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.config.api_key,
            "anthropic-version": "2023-06-01"
        }
        
        async with self.session.post(url, json=payload, headers=headers) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return self._parse_anthropic_response(data)
    
    async def _call_google(self, prompt: str) -> 'EmblemPlan':
        """Call Google Gemini API."""
        url = f"{self.config.endpoint}/v1beta/models/{self.config.model}:generateContent"
        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": prompt}]}
            ],
            "generationConfig": {
                "temperature": self.config.temperature,
                "maxOutputTokens": self.config.max_tokens,
                "responseMimeType": "application/json"
            }
        }
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            url += f"?key={self.config.api_key}"
            
        async with self.session.post(url, json=payload, headers=headers) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return self._parse_google_response(data)
    
    async def _call_openrouter(self, prompt: str) -> 'EmblemPlan':
        """Call OpenRouter API."""
        base = self.config.endpoint.rstrip('/')
        if base.endswith('/api/v1') or base.endswith('/v1'):
            url = f"{base}/chat/completions"
        else:
            url = f"{base}/api/v1/chat/completions"
        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": EmblemPromptBuilder.SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "response_format": {"type": "json_object"}
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}",
            "HTTP-Referer": "https://github.com/BO2-Emblem-Studio",
            "X-Title": "BO2 Emblem Studio"
        }
        
        async with self.session.post(url, json=payload, headers=headers) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return self._parse_response(data)
    
    async def _call_openai_compatible(self, prompt: str) -> 'EmblemPlan':
        """Call Ollama, LM Studio, or vLLM (OpenAI-compatible)."""
        base = self.config.endpoint.rstrip('/')
        url = f"{base}/chat/completions" if base.endswith('/v1') else f"{base}/v1/chat/completions"
        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": EmblemPromptBuilder.SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "response_format": {"type": "json_object"}
        }
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
            
        async with self.session.post(url, json=payload, headers=headers) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return self._parse_response(data)
    
    async def _call_custom(self, prompt: str) -> 'EmblemPlan':
        """Call custom provider with custom headers/body."""
        url = self.config.endpoint
        payload = {**self.config.custom_body, "messages": [
            {"role": "system", "content": EmblemPromptBuilder.SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]}
        headers = {"Content-Type": "application/json", **self.config.custom_headers}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
            
        async with self.session.post(url, json=payload, headers=headers) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return self._parse_response(data)
    
    def _parse_response(self, data: Dict) -> 'EmblemPlan':
        """Parse standard OpenAI-compatible response."""
        try:
            content = data["choices"][0]["message"]["content"]
            plan_data = json.loads(content)
            return self._create_plan(plan_data)
        except (KeyError, json.JSONDecodeError, IndexError) as e:
            logger.error(f"Failed to parse AI response: {e}")
            raise ValueError(f"Invalid AI response format: {e}")
    
    def _parse_anthropic_response(self, data: Dict) -> 'EmblemPlan':
        """Parse Anthropic response format."""
        try:
            content = data["content"][0]["text"]
            plan_data = json.loads(content)
            return self._create_plan(plan_data)
        except (KeyError, json.JSONDecodeError, IndexError) as e:
            logger.error(f"Failed to parse Anthropic response: {e}")
            raise ValueError(f"Invalid Anthropic response format: {e}")
    
    def _parse_google_response(self, data: Dict) -> 'EmblemPlan':
        """Parse Google Gemini response format."""
        try:
            content = data["candidates"][0]["content"]["parts"][0]["text"]
            plan_data = json.loads(content)
            return self._create_plan(plan_data)
        except (KeyError, json.JSONDecodeError, IndexError) as e:
            logger.error(f"Failed to parse Google response: {e}")
            raise ValueError(f"Invalid Google response format: {e}")
    
    def _create_plan(self, plan_data: Dict) -> 'EmblemPlan':
        """Create EmblemPlan from parsed data."""
        concept_data = plan_data.get("concept", {})
        concept = EmblemConcept(
            name=concept_data.get("name", "Untitled"),
            description=concept_data.get("description", ""),
            style=concept_data.get("style", "default"),
            symmetry=concept_data.get("symmetry", "bilateral"),
            complexity=concept_data.get("complexity", 3),
            elements=concept_data.get("elements", []),
            color_scheme=concept_data.get("color_scheme", "auto"),
            composition_notes=concept_data.get("notes", "")
        )
        
        layers = []
        for i, layer_data in enumerate(plan_data.get("layers", [])):
            layer = {
                "index": layer_data.get("index", i),
                "shape_id": layer_data.get("shape_id", 192),
                "r": layer_data.get("r", 1.0),
                "g": layer_data.get("g", 1.0),
                "b": layer_data.get("b", 1.0),
                "a": layer_data.get("a", 1.0),
                "pos_x": layer_data.get("pos_x", 0.0),
                "pos_y": layer_data.get("pos_y", 0.0),
                "scale_x": layer_data.get("scale_x", 0.0),
                "scale_y": layer_data.get("scale_y", 0.0),
                "rotation": layer_data.get("rotation", 0.0),
                "outlined": layer_data.get("outlined", False),
                "flipped": layer_data.get("flipped", False)
            }
            layers.append(layer)
        
        return EmblemPlan(
            concept=concept,
            layers=layers,
            reasoning=plan_data.get("reasoning", ""),
            estimated_layers=plan_data.get("estimated_layers", len(layers)),
            warnings=plan_data.get("warnings", [])
        )


class AIConfigManager:
    """Manages AI configuration persistence."""
    
    CONFIG_FILE = "ai_config.json"
    
    @classmethod
    def load(cls, path: str = None) -> HermesConfig:
        """Load AI configuration from file."""
        path = Path(path or cls.CONFIG_FILE)
        if path.exists():
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                return HermesConfig(**data)
            except Exception as e:
                logger.warning(f"Failed to load AI config: {e}")
        return HermesConfig()
    
    @classmethod
    def save(cls, config: HermesConfig, path: str = None) -> None:
        """Save AI configuration to file."""
        path = Path(path or cls.CONFIG_FILE)
        try:
            data = {
                "provider": config.provider.value,
                "endpoint": config.endpoint,
                "api_key": config.api_key,
                "model": config.model,
                "timeout": config.timeout,
                "temperature": config.temperature,
                "max_tokens": config.max_tokens,
                "custom_headers": config.custom_headers,
                "custom_body": config.custom_body,
            }
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save AI config: {e}")


# Convenience functions
async def generate_emblem_async(concept: EmblemConcept, config: HermesConfig = None) -> EmblemPlan:
    """Generate emblem asynchronously using Hermes."""
    config = config or AIConfigManager.load()
    async with HermesClient(config) as client:
        return await client.generate_emblem(concept)


def generate_emblem(concept: EmblemConcept, config: HermesConfig = None) -> EmblemPlan:
    """Synchronous wrapper for emblem generation."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(generate_emblem_async(concept, config))


# Export key classes
__all__ = [
    'AIProvider',
    'HermesConfig',
    'EmblemConcept',
    'EmblemPlan',
    'EmblemPromptBuilder',
    'HermesClient',
    'AIConfigManager',
    'generate_emblem',
    'generate_emblem_async',
]