"""
Unit tests for the Dual LLM Provider Strategy (capabl_core/llm).

Validates:
1. Ollama provider default resolution (ChatOllama -> Qwen 3 8B).
2. Groq provider construction with mock credentials (ChatGroq -> configured hosted model).
3. Invalid provider handling (raises LLMConfigError).
4. Missing Groq credentials/model handling (raises LLMConfigError).
5. Strict non-fallback invariant (no silent fallback between providers).
6. Provider independence (downstream consumers receive BaseChatModel).
"""

import os
import unittest
from unittest.mock import patch

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq

from capabl_core.llm.provider import (
    LLMProvider,
    LLMConfig,
    LLMConfigError,
)
from capabl_core.llm.factory import create_llm


class TestLLMProvider(unittest.TestCase):
    """Test suite for LLM provider abstraction and factory."""

    def test_ollama_provider_default(self):
        """Verify LLM_PROVIDER=ollama instantiates ChatOllama with qwen3:8b by default."""
        with patch.dict(os.environ, {"LLM_PROVIDER": "ollama", "OLLAMA_MODEL": "qwen3:8b"}, clear=False):
            llm = create_llm()
            self.assertIsInstance(llm, ChatOllama)
            self.assertIsInstance(llm, BaseChatModel)
            self.assertEqual(llm.model, "qwen3:8b")
            self.assertEqual(llm.base_url, "http://localhost:11434")

    def test_ollama_provider_custom_parameters(self):
        """Verify explicit arguments override defaults for ChatOllama."""
        llm = create_llm(
            provider="ollama",
            model="qwen3:8b",
            base_url="http://custom-host:11434",
            temperature=0.3,
        )
        self.assertIsInstance(llm, ChatOllama)
        self.assertEqual(llm.model, "qwen3:8b")
        self.assertEqual(llm.base_url, "http://custom-host:11434")
        self.assertEqual(llm.temperature, 0.3)

    def test_groq_provider_with_mock_credentials(self):
        """Verify LLM_PROVIDER=groq instantiates ChatGroq with configured hosted model."""
        mock_env = {
            "LLM_PROVIDER": "groq",
            "GROQ_API_KEY": "gsk_mock_test_key_for_unit_tests_only",
            "GROQ_MODEL": "llama-3.3-70b-versatile",
            "GROQ_TEMPERATURE": "0.1",
        }
        with patch.dict(os.environ, mock_env, clear=False):
            llm = create_llm()
            self.assertIsInstance(llm, ChatGroq)
            self.assertIsInstance(llm, BaseChatModel)
            self.assertEqual(llm.model_name, "llama-3.3-70b-versatile")
            self.assertEqual(llm.temperature, 0.1)

    def test_invalid_provider_raises_error(self):
        """Verify unsupported LLM_PROVIDER raises an explicit LLMConfigError."""
        with patch.dict(os.environ, {"LLM_PROVIDER": "unknown_provider"}, clear=False):
            with self.assertRaises(LLMConfigError) as ctx:
                create_llm()
            self.assertIn("Unsupported LLM_PROVIDER", str(ctx.exception))
            self.assertIn("unknown_provider", str(ctx.exception))

    def test_missing_groq_api_key_raises_error(self):
        """Verify LLM_PROVIDER=groq without GROQ_API_KEY raises LLMConfigError without silent fallback."""
        mock_env = {
            "LLM_PROVIDER": "groq",
            "GROQ_API_KEY": "",
            "GROQ_MODEL": "llama-3.3-70b-versatile",
        }
        with patch.dict(os.environ, mock_env, clear=False):
            with self.assertRaises(LLMConfigError) as ctx:
                create_llm()
            self.assertIn("GROQ_API_KEY is missing or empty", str(ctx.exception))
            self.assertIn("Silent fallback to Ollama is strictly disallowed", str(ctx.exception))

    def test_missing_groq_model_raises_error(self):
        """Verify LLM_PROVIDER=groq without GROQ_MODEL raises LLMConfigError."""
        mock_env = {
            "LLM_PROVIDER": "groq",
            "GROQ_API_KEY": "gsk_mock_test_key",
            "GROQ_MODEL": "",
        }
        with patch.dict(os.environ, mock_env, clear=False):
            with self.assertRaises(LLMConfigError) as ctx:
                create_llm()
            self.assertIn("GROQ_MODEL is missing or empty", str(ctx.exception))
            self.assertIn("Hard-coding a default Groq model is disallowed", str(ctx.exception))

    def test_no_silent_fallback_from_groq_to_ollama(self):
        """Verify that Groq configuration errors do NOT silently fall back to Ollama."""
        with patch.dict(os.environ, {"LLM_PROVIDER": "groq", "GROQ_API_KEY": ""}, clear=False):
            with self.assertRaises(LLMConfigError):
                llm = create_llm()
                # Should never execute:
                self.assertNotIsInstance(llm, ChatOllama)

    def test_provider_independence_contract(self):
        """Verify downstream functions can consume the factory output as generic BaseChatModel."""
        llm = create_llm(provider="ollama", model="qwen3:8b")
        self.assertTrue(issubclass(type(llm), BaseChatModel))

        mock_groq_llm = create_llm(
            provider="groq",
            api_key="gsk_mock_key",
            model="mixtral-8x7b-32768",
        )
        self.assertTrue(issubclass(type(mock_groq_llm), BaseChatModel))


if __name__ == "__main__":
    unittest.main()
