# Hermes AI Integration for BO2 Emblem Studio

## Overview
The BO2 Emblem Studio includes a full Hermes Agent integration (`ai_hermes.py`) for AI-powered emblem generation. This allows users to describe an emblem in natural language and have an LLM generate the 32-layer BO2 emblem structure.

## Architecture

### Core Classes
- **AIProvider** (Enum): `LOCAL`, `OPENAI`, `ANTHROPIC`, `GOOGLE`, `NVIDIA`, `OPENROUTER`, `OLLAMA`, `LM_STUDIO`, `VLLM`, `CUSTOM`
- **HermesConfig**: Connection config (provider, endpoint, api_key, model, timeout, temperature, max_tokens, custom headers/body)
- **EmblemConcept**: Structured prompt (name, description, style, symmetry, complexity, elements, color_scheme, notes)
- **EmblemPlan**: AI response (concept, layers[], reasoning, estimated_layers, warnings)
- **EmblemPromptBuilder**: Builds the BO2-specific system prompt + user prompt
- **HermesClient**: Async client with provider-specific call methods
- **AIConfigManager**: Persists config to `ai_config.json`

### Provider-Specific Handlers
| Provider | Method | Request Format | Response Parser |
|----------|--------|----------------|-----------------|
| Local / OpenAI / OpenRouter / Ollama / LM Studio / vLLM / Custom | `_call_openai_compatible` | OpenAI Chat Completions | `_parse_response` |
| Anthropic | `_call_anthropic` | Messages API | `_parse_anthropic_response` |
| Google | `_call_google` | Gemini API | `_parse_google_response` |

## System Prompt (BO2-Specific)
The prompt encodes the full BO2 emblem specification:
- 32 layers max (index 0-31, lower = back)
- Shape IDs 0-260 across 5 categories
- Coordinate system: center=(0,0), +Y=DOWN, pos 0.5 = edge
- Scale: true_scale = 2^scale_value
- Rotation: degrees clockwise
- Key shape IDs documented (192=Full Circle, 137=Half Circle, 185=Heart, etc.)
- Composition principles (background→foreground, symmetry via flip, layer order = depth)

## GUI Integration (editor.py: AI Studio Tab)
- Provider dropdown (10 options)
- Endpoint / Model / API Key fields
- Test Connection button (threaded HTTP test)
- Prompt text area with examples
- Style / Symmetry / Complexity / Max Layers controls
- Generate / Refine / Recreate / Improve buttons
- Live PreviewWidget (256px)
- Log console with timestamps

## Usage in Editor
```python
# From GUI - async generation in background thread
from bo2_emblem.ai_hermes import (
    EmblemConcept, HermesConfig, AIProvider, generate_emblem_async
)

concept = EmblemConcept(
    name="AI Generated",
    description="Realistic skull with glowing blue eyes, zombie style",
    style="realistic",
    symmetry="bilateral",
    complexity=4,
    elements=["skull", "glowing eyes", "zombie"],
    color_scheme="dark_blue_white"
)

config = HermesConfig(
    provider=AIProvider.LOCAL,
    endpoint="http://localhost:8080/v1",
    model="nemotron-3-ultra",
    temperature=0.7,
    max_tokens=4096
)

plan = await generate_emblem_async(concept, config)
# plan.layers -> list of layer dicts -> convert to EmblemLayer objects
```

## Running Hermes Agent Locally
```bash
# Start Hermes API server (OpenAI-compatible)
hermes serve --host 0.0.0.0 --port 8080

# Test
curl http://localhost:8080/v1/models
# Should return model list including nemotron-3-ultra
```

## Configuration File (`ai_config.json`)
```json
{
  "provider": "local",
  "endpoint": "http://localhost:8080/v1",
  "api_key": "",
  "model": "nemotron-3-ultra",
  "timeout": 60,
  "temperature": 0.7,
  "max_tokens": 4096,
  "custom_headers": {},
  "custom_body": {}
}
```

## Common Issues & Fixes
| Issue | Fix |
|-------|-----|
| Connection refused | Ensure `hermes serve` is running on correct port |
| "Invalid response format" | Check model supports JSON mode; adjust prompt |
| Generation hangs | Runs in background thread; UI updates via `QMetaObject.invokeMethod` |
| Empty layers returned | Model didn't follow JSON schema; increase temperature or simplify prompt |
| 401 Unauthorized | Verify API key for cloud providers; leave empty for local |
| Model not found | Check model name matches `hermes serve` output or provider catalog |