from dataclasses import dataclass
from typing import List
from realview_chat.dto.image_dto import ImageDTO
from realview_chat.dto.pass25_dto import Pass25DTO

@dataclass
class CaseDTO:
    property_id: str
    created_at: str
    images: List[ImageDTO]
    rooms: List[Pass25DTO]