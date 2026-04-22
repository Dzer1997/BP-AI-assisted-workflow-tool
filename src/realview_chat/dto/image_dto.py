from dataclasses import dataclass
from typing import List
from realview_chat.dto.pass1_dto import Pass1DTO
from realview_chat.dto.pass2_dto import Pass2DTO

@dataclass
class ImageDTO:
    filename: str
    pass1: Pass1DTO
    pass2: Pass2DTO

    condition_score: int | None
    modernity_score: int | None
    material_score: int | None
    functionality_score: int | None