from dataclasses import dataclass
from typing import Optional

@dataclass
class Report:
    """
    Domain Entity representing a daily report.
    Follows SRP: Wraps the data structure for a report.
    """
    activity: str
    learning: str
    obstacles: str
    
    def validate(self) -> bool:
        """Basic validation to ensure content is sufficient."""
        return (
            len(self.activity) >= 50 and 
            len(self.learning) >= 50 and 
            len(self.obstacles) >= 50
        )
