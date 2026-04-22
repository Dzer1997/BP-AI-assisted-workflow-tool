from dataclasses import dataclass
from typing import List
from realview_chat.dto.feature_dto import FeatureDTO

@dataclass
class Pass2DTO:
    condition_score: int | None
    modernity_score: int | None
    material_score: int | None
    functionality_score: int | None
    features: List[FeatureDTO]