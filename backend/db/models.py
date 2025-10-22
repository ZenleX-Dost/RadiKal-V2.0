"""
Database models for RadiKal XAI Quality Control system.

This module defines SQLAlchemy models for persisting analysis history,
detection results, and XAI explanations.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Analysis(Base):
    """
    Main analysis record - one per uploaded image.
    """
    __tablename__ = "analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    image_id = Column(String, unique=True, index=True, nullable=False)
    filename = Column(String, nullable=False)
    upload_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Image metadata
    image_width = Column(Integer)
    image_height = Column(Integer)
    image_size_bytes = Column(Integer)
    
    # Analysis results summary
    num_detections = Column(Integer, default=0)
    has_defects = Column(Boolean, default=False)
    highest_severity = Column(String)  # critical, high, medium, low
    mean_confidence = Column(Float)
    mean_uncertainty = Column(Float, default=0.0)
    
    # Processing info
    inference_time_ms = Column(Float)
    model_version = Column(String)
    status = Column(String, default="completed")  # completed, failed, processing
    
    # Relationships
    detections = relationship("Detection", back_populates="analysis", cascade="all, delete-orphan")
    explanations = relationship("Explanation", back_populates="analysis", cascade="all, delete-orphan")


class Detection(Base):
    """
    Individual detection/bounding box from YOLOv8.
    """
    __tablename__ = "detections"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False)
    
    # Bounding box coordinates
    x1 = Column(Float, nullable=False)
    y1 = Column(Float, nullable=False)
    x2 = Column(Float, nullable=False)
    y2 = Column(Float, nullable=False)
    
    # Detection metadata
    confidence = Column(Float, nullable=False)
    label = Column(Integer, nullable=False)  # Class index
    class_name = Column(String, nullable=False)  # Human-readable class name
    severity = Column(String)  # critical, high, medium, low
    
    # Relationship
    analysis = relationship("Analysis", back_populates="detections")


class Explanation(Base):
    """
    XAI explanation heatmap for an analysis.
    """
    __tablename__ = "explanations"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False)
    
    # XAI method info
    method = Column(String, nullable=False)  # gradcam, lime, shap, integrated_gradients
    confidence_score = Column(Float)
    
    # Heatmap stored as base64 (could also store file path)
    heatmap_base64 = Column(String)  # Base64 encoded PNG
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    analysis = relationship("Analysis", back_populates="explanations")


class SystemMetrics(Base):
    """
    System-wide metrics snapshots over time.
    """
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Business metrics
    true_positives = Column(Integer, default=0)
    true_negatives = Column(Integer, default=0)
    false_positives = Column(Integer, default=0)
    false_negatives = Column(Integer, default=0)
    
    # Detection metrics
    precision = Column(Float)
    recall = Column(Float)
    f1_score = Column(Float)
    map50 = Column(Float)
    auroc = Column(Float)
    
    # Segmentation metrics
    mean_iou = Column(Float)
    mean_dice = Column(Float)
    pixel_accuracy = Column(Float)
    
    # Summary
    total_analyses = Column(Integer, default=0)
    period_start = Column(DateTime)
    period_end = Column(DateTime)
