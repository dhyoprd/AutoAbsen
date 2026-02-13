from dataclasses import dataclass
from typing import ClassVar

@dataclass
class Report:
    """
    Domain Entity representing a daily report.
    Follows SRP: Wraps the data structure for a report.
    """
    activity: str
    learning: str
    obstacles: str
    MIN_FIELD_LENGTH: ClassVar[int] = 150
    MAX_FIELD_LENGTH: ClassVar[int] = 300
    
    def validate(self) -> bool:
        """Basic validation to ensure content is sufficient."""
        return (
            len(self.activity) >= self.MIN_FIELD_LENGTH and
            len(self.learning) >= self.MIN_FIELD_LENGTH and
            len(self.obstacles) >= self.MIN_FIELD_LENGTH
        )
