from __future__ import annotations
from enum import Enum

class ProcessStateEnum(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in progress"
    COMPLETED = "completed"
    FAILED = "failed"

    def __str__(self):
        return self.value

    def __repr__(self) -> str:
        return self.value

    @staticmethod
    def from_string(status_str: str) -> ProcessStateEnum:
        try:
            return ProcessStateEnum(status_str)
        except ValueError:
            raise ValueError(f"Invalid ProcessStatus string: {status_str}")

    @staticmethod
    def to_string(status: ProcessStateEnum) -> str:
        return status.value