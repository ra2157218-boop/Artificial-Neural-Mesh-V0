# ============================================================
#  ANM V0-OpenSource — Unified Type Definitions
#  High-Quality Type System
# ============================================================

"""
ANM Type Definitions

Provides unified types used across all ANM modules.
"""

from __future__ import annotations
from typing import (
    Dict, Any, List, Optional, Union, Callable, TypeVar, Generic,
    Protocol, runtime_checkable, Tuple, Set, FrozenSet, Sequence,
    Mapping, Iterator, Iterable, Awaitable, TYPE_CHECKING
)
from dataclasses import dataclass, field
from enum import Enum, auto
from abc import ABC, abstractmethod
import time

__all__ = [
    # Version
    "ANM_VERSION",
    "ANM_CODENAME",
    
    # Base Types
    "Domain",
    "QueryType",
    "ResponseQuality",
    "ProcessingPhase",
    
    # Result Types
    "ANMResult",
    "QueryResult",
    "ReasoningStep",
    "DomainResult",
    
    # Protocol Types
    "Specialist",
    "MemoryStore",
    "Verifiable",
    
    # Utility Types
    "Timestamp",
    "Score",
    "Confidence",
]

# ============================================================
#  VERSION
# ============================================================

ANM_VERSION = "0.1.0-opensource"
ANM_CODENAME = "Aurora"

# ============================================================
#  ENUMS
# ============================================================

class Domain(Enum):
    """All supported reasoning domains."""
    GENERAL = "general"
    MATH = "math"
    PHYSICS = "physics"
    CODE = "code"
    CHEMISTRY = "chemistry"
    BIOLOGY = "biology"
    MEMORY = "memory"
    RESEARCH = "research"
    FACTS = "facts"
    SIMULATION = "simulation"
    IMAGE = "image"
    SOUND = "sound"


class QueryType(Enum):
    """Types of user queries."""
    QUESTION = auto()
    COMMAND = auto()
    ANALYSIS = auto()
    CREATIVE = auto()
    CALCULATION = auto()
    CODE_TASK = auto()
    MEMORY_RECALL = auto()
    SIMULATION = auto()
    MULTI_STEP = auto()
    UNKNOWN = auto()


class ResponseQuality(Enum):
    """Quality levels for responses."""
    EXCELLENT = auto()    # 0.9-1.0
    GOOD = auto()         # 0.7-0.9
    ACCEPTABLE = auto()   # 0.5-0.7
    POOR = auto()         # 0.3-0.5
    FAILED = auto()       # 0.0-0.3
    
    @classmethod
    def from_score(cls, score: float) -> "ResponseQuality":
        """Convert numeric score to quality level."""
        if score >= 0.9:
            return cls.EXCELLENT
        elif score >= 0.7:
            return cls.GOOD
        elif score >= 0.5:
            return cls.ACCEPTABLE
        elif score >= 0.3:
            return cls.POOR
        return cls.FAILED


class ProcessingPhase(Enum):
    """Phases of query processing."""
    RECEIVED = auto()
    PARSING = auto()
    ROUTING = auto()
    REASONING = auto()
    VERIFYING = auto()
    REFINING = auto()
    COMPLETE = auto()
    ERROR = auto()


# ============================================================
#  TYPE ALIASES
# ============================================================

Timestamp = float  # Unix timestamp
Score = float      # 0.0 to 1.0
Confidence = float # 0.0 to 1.0

T = TypeVar('T')
R = TypeVar('R')

# ============================================================
#  DATA CLASSES
# ============================================================

@dataclass(frozen=True, slots=True)
class ReasoningStep:
    """A single step in the reasoning chain."""
    step_id: int
    domain: Domain
    input_text: str
    output_text: str
    confidence: Confidence
    duration_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class DomainResult:
    """Result from a single domain specialist."""
    domain: Domain
    output: str
    confidence: Confidence
    reasoning_steps: List[ReasoningStep] = field(default_factory=list)
    wot_request: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class QueryResult:
    """Complete result from query processing."""
    query: str
    query_type: QueryType
    primary_domain: Domain
    answer: str
    confidence: Confidence
    quality: ResponseQuality
    domain_results: Dict[str, DomainResult] = field(default_factory=dict)
    reasoning_trace: List[ReasoningStep] = field(default_factory=list)
    total_steps: int = 0
    duration_ms: float = 0.0
    verified: bool = False
    refined: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ANMResult:
    """Top-level ANM query result."""
    success: bool
    result: str
    confidence: Confidence
    quality: ResponseQuality
    query_result: Optional[QueryResult] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def success_result(
        cls,
        result: str,
        confidence: float = 0.8,
        query_result: Optional[QueryResult] = None,
    ) -> "ANMResult":
        """Create a successful result."""
        return cls(
            success=True,
            result=result,
            confidence=confidence,
            quality=ResponseQuality.from_score(confidence),
            query_result=query_result,
        )
    
    @classmethod
    def error_result(cls, error: str) -> "ANMResult":
        """Create an error result."""
        return cls(
            success=False,
            result="",
            confidence=0.0,
            quality=ResponseQuality.FAILED,
            errors=[error],
        )


# ============================================================
#  PROTOCOLS
# ============================================================

@runtime_checkable
class Specialist(Protocol):
    """Protocol for domain specialists."""
    
    def run(self, packet: str) -> str:
        """Process a query packet and return output."""
        ...
    
    @property
    def domain(self) -> Domain:
        """Return the specialist's domain."""
        ...


@runtime_checkable
class MemoryStore(Protocol):
    """Protocol for memory storage."""
    
    def store(self, key: str, value: Any, metadata: Optional[Dict] = None) -> bool:
        """Store a value."""
        ...
    
    def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve a value."""
        ...
    
    def search(self, query: str, limit: int = 10) -> List[Any]:
        """Search for relevant entries."""
        ...


@runtime_checkable  
class Verifiable(Protocol):
    """Protocol for verifiable outputs."""
    
    def verify(self) -> Tuple[bool, List[str]]:
        """Verify the output. Returns (passed, issues)."""
        ...


# ============================================================
#  BASE CLASSES
# ============================================================

class ANMComponent(ABC):
    """Base class for all ANM components."""
    
    _version: str = ANM_VERSION
    _component_name: str = "ANMComponent"
    
    @property
    def version(self) -> str:
        return self._version
    
    @property
    def component_name(self) -> str:
        return self._component_name
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the component."""
        ...
    
    def shutdown(self) -> None:
        """Clean shutdown of the component."""
        pass


class TimedOperation:
    """Context manager for timing operations."""
    
    __slots__ = ('start_time', 'duration_ms', 'name')
    
    def __init__(self, name: str = "operation"):
        self.name = name
        self.start_time: float = 0
        self.duration_ms: float = 0
    
    def __enter__(self) -> "TimedOperation":
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, *args) -> None:
        self.duration_ms = (time.perf_counter() - self.start_time) * 1000
