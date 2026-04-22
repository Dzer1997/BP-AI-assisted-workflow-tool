from dataclasses import dataclass

@dataclass
class Pass1DTO:
    room_type: str
    actionable: bool
    confidence: float