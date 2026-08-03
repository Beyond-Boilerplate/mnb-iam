"""Spoken pronunciation rewrites for Meridian / IAM acronyms.

Edge neural TTS often collapses dotted forms like ``I.A.M.`` into a mushy
word (sounds like "AAM"). Expand selective hard terms to letter-spaced speech
before synthesis so students hear the industry pronunciation.
"""

from __future__ import annotations

import re
from collections.abc import Callable

Repl = str | Callable[[re.Match[str]], str]

# Boundary: letters/digits on either side — NOT \\b after a trailing "."
# (Python \\b fails between "." and space/punctuation.)
_B = r"(?<![A-Za-z0-9])"
_E = r"(?![A-Za-z0-9])"

# Longest / most specific patterns first.
_RULES: list[tuple[re.Pattern[str], Repl]] = [
    # Product / platform
    (re.compile(rf"{_B}IdentityIQ{_E}"), "Identity I Q"),
    (re.compile(rf"{_B}I\.I\.Q\.'s{_E}"), "I I Q's"),
    (re.compile(rf"{_B}I\.I\.Q\.{_E}"), "I I Q"),
    (re.compile(rf"{_B}IIQ{_E}"), "I I Q"),
    # IAM family — never "aam" / word-like mush
    (re.compile(rf"{_B}I\.A\.M\.{_E}"), "I A M"),
    (re.compile(rf"{_B}IAM{_E}"), "I A M"),
    (re.compile(rf"{_B}I\.G\.A\.{_E}"), "I G A"),
    (re.compile(rf"{_B}IGA{_E}"), "I G A"),
    # Bank / lab shorthand
    (re.compile(rf"{_B}MNB-H\.R\.{_E}"), "M N B H R"),
    (
        re.compile(rf"{_B}MNB-([A-Za-z]+(?:-[A-Za-z0-9]+)*){_E}"),
        lambda m: "M N B " + m.group(1).replace("-", " "),
    ),
    (re.compile(rf"{_B}MNB{_E}"), "M N B"),
    # Common IAM / IT acronyms that TTS mangles when left as words
    (re.compile(rf"{_B}SoD{_E}"), "S O D"),
    (re.compile(rf"{_B}SOD{_E}"), "S O D"),
    (re.compile(rf"{_B}H\.R\.{_E}"), "H R"),
    (re.compile(rf"{_B}HR{_E}"), "H R"),
    (re.compile(rf"{_B}U\.I\.{_E}"), "U I"),
    (re.compile(rf"{_B}UI{_E}"), "U I"),
    (re.compile(rf"{_B}U\.R\.L\.{_E}"), "U R L"),
    (re.compile(rf"{_B}URL{_E}"), "U R L"),
    (re.compile(rf"{_B}I\.D\.{_E}"), "I D"),
    (re.compile(rf"{_B}XML{_E}"), "X M L"),
    (re.compile(rf"{_B}SAP{_E}"), "S A P"),
    (re.compile(rf"{_B}AWS{_E}"), "A W S"),
    (re.compile(rf"{_B}API{_E}"), "A P I"),
    (re.compile(rf"{_B}SSO{_E}"), "S S O"),
    (re.compile(rf"{_B}RBAC{_E}"), "R B A C"),
    (re.compile(rf"{_B}SCIM{_E}"), "skim"),
    (re.compile(rf"{_B}JDBC{_E}"), "J D B C"),
    (re.compile(rf"{_B}LDAP{_E}"), "L dap"),
    (re.compile(rf"{_B}OAuth{_E}", re.I), "oauth"),
    (re.compile(rf"{_B}OIDC{_E}"), "O I D C"),
    (re.compile(rf"{_B}SLA{_E}"), "S L A"),
    (re.compile(rf"{_B}RPO{_E}"), "R P O"),
    (re.compile(rf"{_B}CSV{_E}"), "C S V"),
    # Entitlement codes
    (re.compile(rf"{_B}WIRE_INIT{_E}"), "wire init"),
    (re.compile(rf"{_B}WIRE_APPR{_E}"), "wire approve"),
]


def apply_pronunciation(text: str) -> str:
    """Rewrite selective technical terms for natural letter-correct speech."""
    out = text
    for pattern, repl in _RULES:
        out = pattern.sub(repl, out)
    out = re.sub(r"[ \t]{2,}", " ", out)
    return out
