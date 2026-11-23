"""
Shared provider configuration for Grok Flutter App Builder.

Supports:
  - xAI (official)
  - OpenRouter
  - Together AI
  - Fireworks AI
  - Generic OpenAI-compatible endpoint (BASE_URL + API_KEY)
"""

from __future__ import annotations

import os
from typing import Tuple

from openai import OpenAI


PROVIDERS = {
    "xai": {
        "env_key": "XAI_API_KEY",
        "base_url": "https://api.x.ai/v1",
        "default_model": "grok-4.7",
        "model_prefix": "",  # models are just "grok-4.7"
    },
    "openrouter": {
        "env_key": "OPENROUTER_API_KEY",
        "base_url": "https://openrouter.ai/api/v1",
        "default_model": "x-ai/grok-4.7",
        "model_prefix": "x-ai/",
        "extra_headers": {
            "HTTP-Referer": "https://github.com/xbustcodex/grok-flutter-app-builder",
            "X-Title": "Grok Flutter App Builder",
        },
    },
    "together": {
        "env_key": "TOGETHER_API_KEY",
        "base_url": "https://api.together.xyz/v1",
        "default_model": "xai/grok-4.7",  # adjust if Together naming differs
        "model_prefix": "",
    },
    "fireworks": {
        "env_key": "FIREWORKS_API_KEY",
        "base_url": "https://api.fireworks.ai/inference/v1",
        "default_model": "accounts/xai/models/grok-4.7",  # placeholder – update when exact ID known
        "model_prefix": "",
    },
    "generic": {
        "env_key": "API_KEY",          # or OPENAI_API_KEY
        "base_url_env": "BASE_URL",    # required for generic
        "default_model": "grok-4.7",
        "model_prefix": "",
    },
}


def resolve_provider(requested: str | None = None) -> str:
    requested = (requested or os.environ.get("GROK_PROVIDER") or "auto").lower().strip()

    if requested != "auto":
        if requested not in PROVIDERS and requested != "generic":
            raise ValueError(f"Unknown provider: {requested}. Choose from: {list(PROVIDERS) + ['auto']}")
        return requested

    # auto preference order
    for name in ("openrouter", "xai", "together", "fireworks"):
        conf = PROVIDERS[name]
        if os.environ.get(conf["env_key"]):
            return name

    # generic if both BASE_URL and a key are present
    if os.environ.get("BASE_URL") and (os.environ.get("API_KEY") or os.environ.get("OPENAI_API_KEY")):
        return "generic"

    raise ValueError(
        "No API key found. Set one of:\n"
        "  XAI_API_KEY, OPENROUTER_API_KEY, TOGETHER_API_KEY, FIREWORKS_API_KEY\n"
        "  or BASE_URL + API_KEY (generic OpenAI-compatible endpoint)\n"
        "Optional: GROK_PROVIDER=xai|openrouter|together|fireworks|generic"
    )


def get_client(provider: str | None = None) -> Tuple[OpenAI, str, str]:
    """
    Returns (client, resolved_provider_name, default_model)
    """
    name = resolve_provider(provider)
    conf = PROVIDERS[name]

    if name == "generic":
        base_url = os.environ.get("BASE_URL")
        if not base_url:
            raise ValueError("Generic provider requires BASE_URL environment variable")
        api_key = os.environ.get("API_KEY") or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("Generic provider requires API_KEY (or OPENAI_API_KEY)")
        client = OpenAI(api_key=api_key, base_url=base_url.rstrip("/"))
        return client, name, conf["default_model"]

    api_key = os.environ.get(conf["env_key"])
    if not api_key:
        # also accept GROK_API_KEY as alias for xai
        if name == "xai":
            api_key = os.environ.get("GROK_API_KEY")
        if not api_key:
            raise ValueError(f"{conf['env_key']} is not set for provider '{name}'")

    headers = conf.get("extra_headers") or {}
    client = OpenAI(
        api_key=api_key,
        base_url=conf["base_url"],
        default_headers=headers if headers else None,
    )
    return client, name, conf["default_model"]


def resolve_model(model: str | None, provider: str) -> str:
    """Normalize model name for the chosen provider."""
    conf = PROVIDERS.get(provider, PROVIDERS["xai"])
    if not model:
        return conf["default_model"]

    prefix = conf.get("model_prefix", "")
    if prefix and not model.startswith(prefix) and model.startswith("grok"):
        return prefix + model
    return model
