#!/usr/bin/env python3
"""
Central separator specification and validation
Ensures consistency across generators and validators
"""

import re
from enum import Enum
from typing import Dict, List, Tuple


class RoleType(Enum):
    FAMILY_TUTOR = "family_tutor"
    PHILOSOPHICAL_GUIDE = "philosophical_guide"
    GENERAL_ASSISTANT = "general_assistant"
    EDUCATIONAL_EXPERT = "educational_expert"


class SeparatorSpec:
    """Central specification for role-based separators"""

    SPEC_VERSION = "1.0.0"

    ROLE_SEPARATORS: Dict[RoleType, List[str]] = {
        RoleType.FAMILY_TUTOR: [
            "[FAMILY_CONTEXT]",
            "[LEARNING_OBJECTIVE]",
            "[RESPONSE]",
        ],
        RoleType.PHILOSOPHICAL_GUIDE: [
            "[PHILOSOPHICAL_CONTEXT]",
            "[REFLECTION_PROMPT]",
            "[GUIDANCE]",
        ],
        RoleType.GENERAL_ASSISTANT: ["[CONTEXT]", "[TASK]", "[RESPONSE]"],
        RoleType.EDUCATIONAL_EXPERT: [
            "[LEARNING_CONTEXT]",
            "[EXPLANATION_GOAL]",
            "[TEACHING_RESPONSE]",
        ],
    }

    # All possible separators (for collision detection)
    ALL_SEPARATORS = set()
    for separators in ROLE_SEPARATORS.values():
        ALL_SEPARATORS.update(separators)

    # Patterns that should NOT appear inside content segments
    FORBIDDEN_BRACKET_PATTERNS = [
        r"\[(?:FAMILY_|PHILOSOPHICAL_|LEARNING_|EXPLANATION_|REFLECTION_|TEACHING_)[A-Z_]+\]",
        r"\[(?:CONTEXT|TASK|RESPONSE|GUIDANCE|PROMPT|OBJECTIVE)\]",
    ]

    @classmethod
    def get_separators(cls, role: str) -> List[str]:
        """Get separators for a role string"""
        try:
            role_enum = RoleType(role)
            return cls.ROLE_SEPARATORS[role_enum]
        except ValueError:
            raise ValueError(f"Unknown role: {role}")

    @classmethod
    def validate_no_stray_brackets(cls, content: str) -> Tuple[bool, List[str]]:
        """Check for stray separator brackets in content"""
        violations = []

        for pattern in cls.FORBIDDEN_BRACKET_PATTERNS:
            matches = re.findall(pattern, content)
            if matches:
                violations.extend(matches)

        return len(violations) == 0, violations

    @classmethod
    def extract_segments(cls, instruction: str, role: str) -> Dict[str, str]:
        """Extract content segments based on role separators"""
        separators = cls.get_separators(role)
        segments = {}

        # Split by separators and extract content
        parts = instruction.split("\n\n")
        current_segment = None
        current_content = []

        for part in parts:
            part = part.strip()

            # Check if this part is a separator
            if part in separators:
                # Save previous segment
                if current_segment:
                    segments[current_segment] = "\n".join(current_content).strip()

                # Start new segment
                current_segment = part
                current_content = []
            elif current_segment:
                # Add to current segment
                current_content.append(part)

        # Save final segment
        if current_segment and current_content:
            segments[current_segment] = "\n".join(current_content).strip()

        return segments
