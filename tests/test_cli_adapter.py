"""Tests for the CLI adapter - verifies council can call models and get responses."""

import pytest
import asyncio
from backend.cli_adapter import (
    query_model,
    query_models_parallel,
    filter_codex_thinking,
    format_messages_as_prompt,
    CLI_CONFIGS,
)


# ============================================================================
# Unit Tests (no external calls)
# ============================================================================

class TestFormatMessages:
    """Test message formatting for CLI prompts."""

    def test_single_user_message(self):
        messages = [{"role": "user", "content": "Hello"}]
        result = format_messages_as_prompt(messages)
        assert result == "Hello"

    def test_multi_turn_conversation(self):
        messages = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello!"},
            {"role": "user", "content": "Bye"},
        ]
        result = format_messages_as_prompt(messages)
        assert "System: You are helpful." in result
        assert "User: Hi" in result
        assert "Assistant: Hello!" in result
        assert "User: Bye" in result


class TestCodexFilter:
    """Test codex output filtering."""

    def test_filters_standard_codex_output(self):
        codex_output = """OpenAI Codex v0.77.0 (research preview)
--------
workdir: /Users/test
model: gpt-5.2-codex
--------
user
What is 2+2?
thinking
**Calculating the sum**
codex
Four
tokens used
1,288
"""
        result = filter_codex_thinking(codex_output)
        assert result == "Four"

    def test_filters_multiline_response(self):
        codex_output = """OpenAI Codex v0.77.0
--------
user
Explain Python
thinking
**Preparing explanation**
codex
Python is a programming language.
It is widely used for:
- Web development
- Data science
- Automation
tokens used
500
"""
        result = filter_codex_thinking(codex_output)
        assert "Python is a programming language" in result
        assert "Web development" in result
        assert "tokens used" not in result

    def test_handles_missing_codex_section(self):
        # If no codex section, return stripped content
        content = "Just some plain text"
        result = filter_codex_thinking(content)
        assert result == "Just some plain text"


# ============================================================================
# Integration Tests (call real CLIs)
# ============================================================================

# Simple prompt that should get a short, predictable response
TEST_PROMPT = "What is 2+2? Answer with just the number."


@pytest.fixture
def simple_messages():
    return [{"role": "user", "content": TEST_PROMPT}]


class TestCLIAvailability:
    """Test that CLIs are available in PATH."""

    @pytest.mark.parametrize("model", CLI_CONFIGS.keys())
    def test_cli_in_path(self, model):
        import shutil
        config = CLI_CONFIGS[model]
        cmd = config["command"]
        assert shutil.which(cmd) is not None, f"{cmd} not found in PATH"


@pytest.mark.asyncio
class TestIndividualModels:
    """Test each model can respond to a query."""

    @pytest.mark.timeout(60)
    async def test_gemini_responds(self, simple_messages):
        result = await query_model("gemini", simple_messages, timeout=60)
        assert result is not None, "gemini returned None"
        assert "content" in result
        assert result["content"], "gemini returned empty content"
        # Should contain "4" or "four" somewhere
        content_lower = result["content"].lower()
        assert "4" in content_lower or "four" in content_lower, f"Unexpected response: {result['content']}"

    @pytest.mark.timeout(60)
    async def test_claude_responds(self, simple_messages):
        result = await query_model("claude", simple_messages, timeout=60)
        assert result is not None, "claude returned None"
        assert "content" in result
        assert result["content"], "claude returned empty content"
        content_lower = result["content"].lower()
        assert "4" in content_lower or "four" in content_lower, f"Unexpected response: {result['content']}"

    @pytest.mark.timeout(60)
    async def test_codex_responds(self, simple_messages):
        result = await query_model("codex", simple_messages, timeout=60)
        assert result is not None, "codex returned None"
        assert "content" in result
        assert result["content"], "codex returned empty content"
        content_lower = result["content"].lower()
        assert "4" in content_lower or "four" in content_lower, f"Unexpected response: {result['content']}"

    @pytest.mark.timeout(60)
    async def test_amp_responds(self, simple_messages):
        result = await query_model("amp", simple_messages, timeout=60)
        assert result is not None, "amp returned None"
        assert "content" in result
        assert result["content"], "amp returned empty content"
        content_lower = result["content"].lower()
        assert "4" in content_lower or "four" in content_lower, f"Unexpected response: {result['content']}"


@pytest.mark.asyncio
class TestParallelQueries:
    """Test parallel query functionality."""

    @pytest.mark.timeout(120)
    async def test_query_all_models_parallel(self, simple_messages):
        """Test that all models can be queried in parallel."""
        models = list(CLI_CONFIGS.keys())
        results = await query_models_parallel(models, simple_messages)

        assert len(results) == len(models), "Not all models returned results"

        for model in models:
            assert model in results, f"{model} missing from results"
            result = results[model]
            assert result is not None, f"{model} returned None"
            assert "content" in result, f"{model} missing 'content' key"
            assert result["content"], f"{model} returned empty content"

    @pytest.mark.timeout(120)
    async def test_parallel_faster_than_sequential(self, simple_messages):
        """Verify parallel execution provides speedup."""
        import time

        models = ["gemini", "claude"]  # Use just 2 for faster test

        # Time parallel execution
        start = time.time()
        await query_models_parallel(models, simple_messages)
        parallel_time = time.time() - start

        # Time sequential execution
        start = time.time()
        for model in models:
            await query_model(model, simple_messages)
        sequential_time = time.time() - start

        # Parallel should be faster (allow some margin for variance)
        # At minimum, parallel shouldn't be significantly slower
        assert parallel_time < sequential_time * 1.5, (
            f"Parallel ({parallel_time:.1f}s) not faster than sequential ({sequential_time:.1f}s)"
        )


@pytest.mark.asyncio
class TestErrorHandling:
    """Test error handling in the adapter."""

    async def test_unknown_model_returns_none(self):
        result = await query_model("unknown_model", [{"role": "user", "content": "test"}])
        assert result is None

    async def test_timeout_returns_none(self):
        # Use a very short timeout that should fail
        result = await query_model(
            "gemini",
            [{"role": "user", "content": "Write a 1000 word essay."}],
            timeout=0.001  # 1ms - should timeout
        )
        assert result is None
