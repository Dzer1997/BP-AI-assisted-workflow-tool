from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Boolean, Text
from sqlalchemy.orm import relationship
from realview_chat.database.db import Base


# -------------------------
# PASS 1 (image-level classification)
# -------------------------
class pass1_results(Base):
    __tablename__ = "pass1_results"

    id = Column(Integer, primary_key=True, index=True)
    image_id = Column(Integer, ForeignKey("images.id"), unique=True)

    room_type = Column(String)
    actionable = Column(Boolean)
    pass1_confidence = Column(Float)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    image = relationship("Image", back_populates="pass1_result")


# -------------------------
# PASS 2 (image-level inspection)
# -------------------------
class pass2_results(Base):
    __tablename__ = "pass2_results"

    id = Column(Integer, primary_key=True, index=True)
    image_id = Column(Integer, ForeignKey("images.id"), unique=True)

    condition_score = Column(Integer, nullable=True)
    modernity_score = Column(Integer, nullable=True)
    material_score = Column(Integer, nullable=True)
    functionality_score = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    image = relationship("Image", back_populates="pass2_result")
    features = relationship("Feature", back_populates="pass2_result", cascade="all, delete-orphan")


# -------------------------
# PASS 2 FEATURES
# -------------------------
class Feature(Base):
    __tablename__ = "features"

    id = Column(Integer, primary_key=True)

    pass2_result_id = Column(Integer, ForeignKey("pass2_results.id"))

    feature_id = Column(String)
    severity = Column(String)
    confidence = Column(Float)
    explanation = Column(Text)

    pass2_result = relationship("pass2_results", back_populates="features")


# -------------------------
# PASS 25 (room-level aggregation)
# -------------------------
class pass25_results(Base):
    __tablename__ = "pass25_results"

    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.id"))

    room_type = Column(String)

    condition_score = Column(Integer)
    modernity_score = Column(Integer)
    material_score = Column(Integer)
    functionality_score = Column(Integer)

    confidence = Column(Float)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    case = relationship("Case", back_populates="pass25_results")


# -------------------------
# IMAGE (source entity)
# -------------------------
class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"))

    file_path = Column(String, nullable=False)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    case = relationship("Case", back_populates="images")

    pass1_result = relationship("pass1_results", back_populates="image", uselist=False)
    pass2_result = relationship("pass2_results", back_populates="image", uselist=False)


# -------------------------
# CASE (root entity)
# -------------------------
class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    folder_name = Column(String, nullable=False)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    images = relationship("Image", back_populates="case")
    pass25_results = relationship("pass25_results", back_populates="case")

class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True)

    property_id = Column(String, index=True)
    filename = Column(String, index=True)

    classification = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    scores = relationship("FeedbackScore", back_populates="feedback")
    features = relationship("FeedbackFeature", back_populates="feedback")

class FeedbackScore(Base):
    __tablename__ = "feedback_scores"

    id = Column(Integer, primary_key=True)

    feedback_id = Column(Integer, ForeignKey("feedback.id"))

    score_type = Column(String)
    value = Column(Integer)

    feedback = relationship("Feedback", back_populates="scores")

class FeedbackFeature(Base):
    __tablename__ = "feedback_features"

    id = Column(Integer, primary_key=True)

    feedback_id = Column(Integer, ForeignKey("feedback.id"))

    feature_id = Column(String)
    verdict = Column(String)

    feedback = relationship("Feedback", back_populates="features")

