"""Blackbox Teller agent evaluation (utterance → /api/chat → golden asserts)."""

from .assert_engine import AssertResult, evaluate_case

__all__ = ["AssertResult", "evaluate_case"]
