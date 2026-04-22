from dataclasses import dataclass

@dataclass
class FeatureDTO:
    feature_id: str
    severity: str
    confidence: float
    explanation: str