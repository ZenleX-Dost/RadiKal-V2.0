"""
Database package initialization.
"""

from db.database import engine, SessionLocal, get_db, init_db, reset_db
from db.models import (
    Base, 
    Analysis, 
    Detection, 
    Explanation, 
    SystemMetrics,
    User,
    UserRole,
    Review,
    ReviewAnnotation,
    ComplianceCertificate,
    OperatorPerformance,
    CustomDefectType,
    TrainingSample,
    ModelVersion,
    TrainingDataset,
    TrainingJob,
    ActiveLearningQueue,
    # New role-based models
    ChangeRequest,
    AnalysisComment,
    ActivityLog,
    UserActivitySummary,
)

__all__ = [
    "engine",
    "SessionLocal",
    "get_db",
    "init_db",
    "reset_db",
    "Base",
    "Analysis",
    "Detection",
    "Explanation",
    "SystemMetrics",
    "User",
    "UserRole",
    "Review",
    "ReviewAnnotation",
    "ComplianceCertificate",
    "OperatorPerformance",
    "CustomDefectType",
    "TrainingSample",
    "ModelVersion",
    "TrainingDataset",
    "TrainingJob",
    "ActiveLearningQueue",
    # New role-based models
    "ChangeRequest",
    "AnalysisComment",
    "ActivityLog",
    "UserActivitySummary",
]
