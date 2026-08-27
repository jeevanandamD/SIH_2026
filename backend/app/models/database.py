from sqlalchemy import create_engine, Column, String, Float, Integer, Text, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from ..config import DB_PATH

Base = declarative_base()
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
SessionLocal = sessionmaker(bind=engine)


class Survey(Base):
    __tablename__ = "surveys"

    survey_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    vessel_id = Column(String, nullable=True)
    start_time = Column(String, nullable=True)
    end_time = Column(String, nullable=True)
    area_name = Column(String, nullable=True)
    sonar_type = Column(String, nullable=True)
    status = Column(String, default="uploaded")

    images = relationship("SonarImage", back_populates="survey")


class SonarImage(Base):
    __tablename__ = "sonar_images"

    image_id = Column(String, primary_key=True)
    survey_id = Column(String, ForeignKey("surveys.survey_id"), nullable=False)
    image_path = Column(String, nullable=False)
    timestamp = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    depth = Column(Float, nullable=True)

    survey = relationship("Survey", back_populates="images")
    detections = relationship("Detection", back_populates="image")


class Detection(Base):
    __tablename__ = "detections"

    detection_id = Column(String, primary_key=True)
    image_id = Column(String, ForeignKey("sonar_images.image_id"), nullable=False)
    target_id = Column(String, nullable=False)
    object_class = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    bbox_x1 = Column(Float, nullable=False)
    bbox_y1 = Column(Float, nullable=False)
    bbox_x2 = Column(Float, nullable=False)
    bbox_y2 = Column(Float, nullable=False)
    segmentation_mask_path = Column(String, nullable=True)

    image = relationship("SonarImage", back_populates="detections")
    anomaly = relationship("Anomaly", back_populates="detection", uselist=False)
    acoustic_features = relationship("AcousticFeatures", back_populates="detection", uselist=False)
    risk_assessment = relationship("RiskAssessment", back_populates="detection", uselist=False)
    feedback = relationship("ExpertFeedback", back_populates="detection", uselist=False)


class Anomaly(Base):
    __tablename__ = "anomalies"

    anomaly_id = Column(String, primary_key=True)
    detection_id = Column(String, ForeignKey("detections.detection_id"), nullable=False)
    anomaly_score = Column(Float, nullable=False)
    uncertainty = Column(Float, nullable=False)

    detection = relationship("Detection", back_populates="anomaly")


class AcousticFeatures(Base):
    __tablename__ = "acoustic_features"

    detection_id = Column(String, ForeignKey("detections.detection_id"), primary_key=True)
    target_intensity = Column(Float, nullable=False)
    target_area = Column(Float, nullable=False)
    shadow_area = Column(Float, nullable=False)
    shadow_length = Column(Float, nullable=False)
    target_shadow_ratio = Column(Float, nullable=False)
    seabed_texture = Column(Float, nullable=False)
    seabed_contrast = Column(Float, nullable=False)

    detection = relationship("Detection", back_populates="acoustic_features")


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    detection_id = Column(String, ForeignKey("detections.detection_id"), primary_key=True)
    evidence_score = Column(Float, nullable=False)
    risk_score = Column(Float, nullable=False)
    risk_level = Column(String, nullable=False)
    priority = Column(Integer, nullable=False)

    detection = relationship("Detection", back_populates="risk_assessment")


class ExpertFeedback(Base):
    __tablename__ = "expert_feedback"

    feedback_id = Column(String, primary_key=True)
    detection_id = Column(String, ForeignKey("detections.detection_id"), nullable=False)
    expert_label = Column(String, nullable=False)
    correction = Column(Text, nullable=True)
    comments = Column(Text, nullable=True)
    verified = Column(Integer, default=0)

    detection = relationship("Detection", back_populates="feedback")


def init_db():
    Base.metadata.create_all(engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
