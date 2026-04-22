from dataclasses import dataclass

@dataclass
class Pass25DTO:
    room_type: str
    condition_score: int
    modernity_score: int
    material_score: int
    functionality_score: int
    confidence: float | None = None