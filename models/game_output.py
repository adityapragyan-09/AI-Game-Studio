"""
Pydantic models for structured AI output.

These models define the expected output format for each agent in the pipeline,
enabling structured output validation instead of fragile regex parsing.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class GameDesign(BaseModel):
    """Structured output for the Game Designer agent."""
    game_title: str = Field(..., description="Creative title for the game")
    core_mechanics: str = Field(..., description="Core gameplay loop and mechanics")
    controls: str = Field(..., description="Keyboard controls (arrow keys, space, etc.)")
    scoring_system: str = Field(..., description="How scoring works with increasing difficulty")
    enemy_types: List[str] = Field(..., description="List of enemy types and behaviors")
    progression_system: str = Field(..., description="How difficulty scales over time")
    visual_style: str = Field(..., description="Visual style using pygame.draw primitives only")
    constraints: List[str] = Field(default_factory=list, description="Technical constraints for developers")

    @field_validator('enemy_types')
    @classmethod
    def validate_enemy_types(cls, v):
        if not v:
            raise ValueError("At least one enemy type must be specified")
        return v


class GameCode(BaseModel):
    """Structured output for Developer/Optimizer/QA agents."""
    code: str = Field(..., description="Complete executable Python game code")
    game_title: str = Field(..., description="Title of the game")
    description: str = Field(..., description="Brief description of the game")
    requirements_met: bool = Field(default=True, description="Whether all requirements were met")
    known_issues: List[str] = Field(default_factory=list, description="Any known issues or limitations")

    @field_validator('code')
    @classmethod
    def validate_code_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Code cannot be empty")
        if not v.strip().startswith(('import ', 'from ', '#!')):
            raise ValueError("Code must start with import statement or shebang")
        return v


class DesignTaskOutput(BaseModel):
    """Output format for design task."""
    design: GameDesign


class DevelopmentTaskOutput(BaseModel):
    """Output format for development task."""
    game: GameCode


class OptimizationTaskOutput(BaseModel):
    """Output format for optimization task."""
    game: GameCode
    optimizations_applied: List[str] = Field(default_factory=list)


class QATaskOutput(BaseModel):
    """Output format for QA task."""
    game: GameCode
    bugs_fixed: List[str] = Field(default_factory=list)
    validation_passed: bool = True


# Schema exports for CrewAI structured output
GAME_DESIGN_SCHEMA = GameDesign.model_json_schema()
GAME_CODE_SCHEMA = GameCode.model_json_schema()