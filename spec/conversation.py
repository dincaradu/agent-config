"""
Conversation Engine — LLM-driven spec elicitation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field
from spec.models import ProjectSpec


class ConversationPhase(str, Enum):
    ELICITATION = "elicitation"
    REFINEMENT = "refinement"
    CONFIRMATION = "confirmation"


class ConversationTurn(BaseModel):
    """Single turn in the conversation."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    extracted_entities: dict[str, Any] = Field(default_factory=dict)


class ConversationState(BaseModel):
    """Tracks the full conversation state."""
    turns: list[ConversationTurn] = Field(default_factory=list)
    draft_spec: Optional[ProjectSpec] = None
    confidence: dict[str, float] = Field(default_factory=dict)
    pending_questions: list[str] = Field(default_factory=list)
    phase: ConversationPhase = ConversationPhase.ELICITATION
    project_dir: Optional[Path] = None
    session_id: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def add_turn(self, role: str, content: str, entities: Optional[dict] = None) -> None:
        """Add a turn to the conversation."""
        turn = ConversationTurn(
            role=role,
            content=content,
            extracted_entities=entities or {},
        )
        self.turns.append(turn)
    
    def get_user_turns(self) -> list[ConversationTurn]:
        return [t for t in self.turns if t.role == "user"]
    
    def get_assistant_turns(self) -> list[ConversationTurn]:
        return [t for t in self.turns if t.role == "assistant"]
    
    def to_json(self) -> dict:
        """Serialize for persistence."""
        return {
            "turns": [t.model_dump(mode="json") for t in self.turns],
            "draft_spec": self.draft_spec.model_dump(mode="json") if self.draft_spec else None,
            "confidence": self.confidence,
            "pending_questions": self.pending_questions,
            "phase": self.phase.value,
            "project_dir": str(self.project_dir) if self.project_dir else None,
            "session_id": self.session_id,
        }
    
    @classmethod
    def from_json(cls, data: dict) -> "ConversationState":
        """Deserialize from persistence."""
        turns = [ConversationTurn(**t) for t in data.get("turns", [])]
        draft_spec = ProjectSpec(**data["draft_spec"]) if data.get("draft_spec") else None
        return cls(
            turns=turns,
            draft_spec=draft_spec,
            confidence=data.get("confidence", {}),
            pending_questions=data.get("pending_questions", []),
            phase=ConversationPhase(data.get("phase", "elicitation")),
            project_dir=Path(data["project_dir"]) if data.get("project_dir") else None,
            session_id=data.get("session_id"),
        )


CONVERSATION_SYSTEM_PROMPT = """You are a senior AI architect helping a developer specify an agent configuration.
Your goal: build a complete ProjectSpec through natural, unhurried conversation.

PRINCIPLES:
- Start with open-ended listening. Let them describe the project fully in their own words.
- Extract: product, tech stack, team, agent roles, conventions, pain points, 
  infrastructure preferences, memory needs, eval criteria.
- Ask ONE focused question at a time. No questionnaires. No multiple-choice unless they ask.
- Propose concrete structures: "Based on what you said, I see 3 agent roles: feature, review, test. Add research?"
- Track confidence per field. When all > 0.8, offer to generate (but wait for user confirmation).
- Never assume. Clarify ambiguity: "When you say 'local-first', do you mean Ollama + Qdrant + mem0 locally, or something else?"
- This conversation can take as long as needed — hours if that's what it takes.
- Write the spec to disk as agent-config-spec.json + README.md
- Initialize git — every refinement = commit
- Only generate when user explicitly says "build it" or "generate configs"
"""


EXTRACTION_PROMPT = """Extract a complete ProjectSpec from this conversation history.

Conversation:
{conversation}

Return JSON with:
1. "spec": the ProjectSpec fields you can confidently extract
2. "confidence": field -> 0.0-1.0 confidence scores
3. "gaps": list of fields still missing or uncertain
4. "next_questions": list of 1-3 focused follow-up questions to ask

Only include fields you're confident about. Use null for unknown.
"""


@dataclass
class ExtractionResult:
    """Result of LLM extraction."""
    spec_data: dict
    confidence: dict[str, float]
    gaps: list[str]
    next_questions: list[str]


async def extract_spec_from_conversation(
    state: ConversationState,
    ollama_client,
    model: str = "llama3.2:latest",
) -> ExtractionResult:
    """Use LLM to extract structured spec from conversation history."""
    # Format conversation for prompt
    conv_lines = []
    for turn in state.turns:
        prefix = "User" if turn.role == "user" else "Architect"
        conv_lines.append(f"{prefix}: {turn.content}")
    
    conversation_text = "\n\n".join(conv_lines)
    
    prompt = EXTRACTION_PROMPT.format(conversation=conversation_text)
    
    try:
        response = await ollama_client.chat(
            model=model,
            messages=[
                {"role": "system", "content": "You are a precise JSON extractor. Return only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            format="json",
            options={"temperature": 0.1},
        )
        
        import json
        result = json.loads(response["message"]["content"])
        
        return ExtractionResult(
            spec_data=result.get("spec", {}),
            confidence=result.get("confidence", {}),
            gaps=result.get("gaps", []),
            next_questions=result.get("next_questions", []),
        )
    except Exception as e:
        return ExtractionResult(
            spec_data={},
            confidence={},
            gaps=["extraction failed"],
            next_questions=[f"Extraction error: {e}"],
        )


def merge_spec_data(base: ProjectSpec | None, extracted: dict, confidence: dict[str, float]) -> ProjectSpec:
    """Merge extracted data into existing spec, preserving confidence."""
    if base is None:
        base = ProjectSpec(project_name="project", product_description="")
    # Update confidence
    for field_name, conf in confidence.items():
        base.update_confidence(field_name, conf)
    
    # Apply extracted data (only non-null values)
    for key, value in extracted.items():
        if value is not None and hasattr(base, key):
            # Handle nested objects
            current = getattr(base, key)
            if hasattr(current, "model_dump") and isinstance(value, dict):
                # Merge nested model
                merged = current.model_dump()
                merged.update(value)
                setattr(base, key, type(current)(**merged))
            else:
                setattr(base, key, value)
    
    return base