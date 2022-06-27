__version__ = "0.0.0"

from ._code_demo import (
    CodeDemo,
    ParametersBox,
    CodeChecker
)
from ._code_visualizer import (
    CodeVisualizer,
    PyplotOutput,
    ClearedOutput,
    AnimationOutput
)
from ._answer import (
    Answer,
    AnswerRegistry,
    TextareaAnswer
)

__all__ = [
    "CodeDemo",
    "ParametersBox",
    "CodeChecker",
    "CodeVisualizer",
    "PyplotOutput",
    "ClearedOutput",
    "AnimationOutput",
    "Answer",
    "AnswerRegistry"
    "TextareaAnswer",
]
