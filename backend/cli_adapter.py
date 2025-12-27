"""CLI adapter for making LLM requests via local command-line tools."""

import asyncio
from typing import List, Dict, Any, Optional

from . import cli_config


def get_cli_configs() -> Dict[str, Dict[str, Any]]:
    """
    Load CLI configurations from cli_config.py.
    Returns a dict mapping CLI id to {command, args}.
    """
    config = cli_config.load_config()
    return {
        cli["id"]: {"command": cli["command"], "args": cli["args"]}
        for cli in config["clis"]
    }


def format_messages_as_prompt(messages: List[Dict[str, str]]) -> str:
    """
    Convert a list of chat messages into a single prompt string.

    CLIs typically don't support multi-turn conversations, so we
    concatenate the conversation history into a single prompt.
    """
    parts = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "system":
            parts.append(f"System: {content}")
        elif role == "user":
            parts.append(f"User: {content}")
        elif role == "assistant":
            parts.append(f"Assistant: {content}")

    # If there's only one user message, just return it directly
    if len(messages) == 1 and messages[0].get("role") == "user":
        return messages[0].get("content", "")

    return "\n\n".join(parts)


async def query_model(
    model: str,
    messages: List[Dict[str, str]],
    timeout: float = 120.0
) -> Optional[Dict[str, Any]]:
    """
    Query a single model via its CLI.

    Args:
        model: Model identifier (e.g., "gemini", "claude", "codex", "amp")
        messages: List of message dicts with 'role' and 'content'
        timeout: Request timeout in seconds

    Returns:
        Response dict with 'content' and optional 'reasoning_details', or None if failed
    """
    cli_configs = get_cli_configs()

    if model not in cli_configs:
        print(f"Unknown model: {model}. Available: {list(cli_configs.keys())}")
        return None

    config = cli_configs[model]
    prompt = format_messages_as_prompt(messages)

    # Build command
    cmd = [config["command"]] + config["args"] + [prompt]

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            print(f"Timeout querying model {model}")
            return None

        if process.returncode != 0:
            print(f"Error from {model} CLI (exit {process.returncode}): {stderr.decode()}")
            return None

        content = stdout.decode().strip()

        # For codex, try to filter out thinking if present
        if model == "codex":
            content = filter_codex_thinking(content)

        return {
            'content': content,
            'reasoning_details': None
        }

    except FileNotFoundError:
        print(f"CLI not found: {config['command']}. Is it installed and in PATH?")
        return None
    except Exception as e:
        print(f"Error querying model {model}: {e}")
        return None


def filter_codex_thinking(content: str) -> str:
    """
    Filter codex output to extract just the response content.

    Codex output format:
    - Header (version, workdir, model, etc.)
    - "user" section with prompt
    - "thinking" section with reasoning
    - "codex" section with the actual response
    - "tokens used" section
    """
    import re

    # Try to extract content between "codex" line and "tokens used" line
    lines = content.split('\n')
    in_codex_section = False
    codex_content = []

    for line in lines:
        stripped = line.strip()
        if stripped == 'codex':
            in_codex_section = True
            continue
        if stripped.startswith('tokens used'):
            break
        if in_codex_section:
            codex_content.append(line)

    if codex_content:
        return '\n'.join(codex_content).strip()

    # Fallback: try to remove common header patterns
    # Remove everything before "thinking" or "codex" sections
    if '\ncodex\n' in content:
        parts = content.split('\ncodex\n', 1)
        if len(parts) > 1:
            # Remove "tokens used" section
            result = parts[1].split('\ntokens used')[0]
            return result.strip()

    return content.strip()


async def query_models_parallel(
    models: List[str],
    messages: List[Dict[str, str]]
) -> Dict[str, Optional[Dict[str, Any]]]:
    """
    Query multiple models in parallel.

    Args:
        models: List of model identifiers
        messages: List of message dicts to send to each model

    Returns:
        Dict mapping model identifier to response dict (or None if failed)
    """
    # Create tasks for all models
    tasks = [query_model(model, messages) for model in models]

    # Wait for all to complete
    responses = await asyncio.gather(*tasks)

    # Map models to their responses
    return {model: response for model, response in zip(models, responses)}
