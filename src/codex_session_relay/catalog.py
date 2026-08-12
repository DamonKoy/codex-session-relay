from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from .paths import relay_home
from .util import canonical_json, read_json, write_json


# Capability values follow DeepSeek's official Codex integration catalog.  The
# instructions are intentionally concise: project/global AGENTS.md instructions
# are still loaded by Codex and Relay does not overwrite the user's config.toml.
DEEPSEEK_V4_CATALOG: Dict[str, Any] = {
    "models": [
        {
            "slug": "deepseek-v4-flash",
            "display_name": "DeepSeek-V4-Flash",
            "description": "Latest frontier agentic coding model.",
            "base_instructions": (
                "You are Codex, an agentic coding assistant. Work with the user "
                "in the current workspace, follow developer instructions, use "
                "tools carefully, preserve unrelated changes, and verify "
                "completed work."
            ),
            "context_window": 1048576,
            "max_context_window": 1048576,
            "effective_context_window_percent": 95,
            "truncation_policy": {"mode": "tokens", "limit": 10000},
            "auto_compact_token_limit": None,
            "comp_hash": "3000",
            "default_reasoning_level": "high",
            "supported_reasoning_levels": [
                {
                    "effort": "low",
                    "description": "Fast responses with lighter reasoning",
                },
                {
                    "effort": "high",
                    "description": "Extra high reasoning depth for complex problems",
                },
                {
                    "effort": "max",
                    "description": "Maximum reasoning depth for the hardest problems",
                },
            ],
            "input_modalities": ["text"],
            "supports_parallel_tool_calls": True,
            "supports_reasoning_summaries": True,
            "reasoning_summary_format": "experimental",
            "default_reasoning_summary": "none",
            "supports_search_tool": True,
            "supports_image_detail_original": False,
            "prefer_websockets": False,
            "support_verbosity": True,
            "default_verbosity": "low",
            "apply_patch_tool_type": "freeform",
            "web_search_tool_type": "text",
            "tool_mode": None,
            "multi_agent_version": "v2",
            "use_responses_lite": False,
            "include_skills_usage_instructions": False,
            "auto_review_model_override": None,
            "shell_type": "shell_command",
            "visibility": "list",
            "minimal_client_version": "0.144.0",
            "supported_in_api": True,
            "availability_nux": None,
            "upgrade": None,
            "priority": 1,
            "experimental_supported_tools": [],
            "default_service_tier": None,
        }
    ]
}


def ensure_deepseek_v4_catalog() -> Path:
    path = relay_home() / "deepseek-v4-models.json"
    current = None
    if path.exists():
        try:
            current = read_json(path)
        except (OSError, ValueError):
            current = None
    if current is None or canonical_json(current) != canonical_json(DEEPSEEK_V4_CATALOG):
        write_json(path, DEEPSEEK_V4_CATALOG, mode=0o600)
    return path
