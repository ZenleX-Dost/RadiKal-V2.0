"""
Role-Based Access Control API Routes

Provides endpoints for:
- RadikalUser: View other users' results, perform analyses
- Chief: Supervise users, create change requests, add comments, view activity
- Manager: View history, change requests list, activity charts

Author: RadiKal Team
"""

from datetime import datetime, timedelta
from typing import List, Optional
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc

from db import (
    get_db, 
    User, 
    UserRole, 
    Analysis, 
    ChangeRequest, 
    AnalysisComment, 
    ActivityLog,
    UserActivitySummary,
    Review
)
from api.schemas import (
    ChangeRequestCreate,
    ChangeRequestUpdate,
    ChangeRequestResponse,
    ChangeRequestListResponse,
    CommentCreate,
    CommentResponse,
    ActivityLogResponse,
    UserActivitySummaryResponse,
    UserActivityChartData,
    RadikalUserStats,
    ChiefDashboardStats,
    ManagerDashboardStats,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/roles", tags=["Role-Based Access"])


# ============================================================================
# Helper Functions
# ============================================================================

def get_user_by_session(session_token: str, db: Session) -> Optional[User]:
    """Get user from session token. In production, use proper JWT validation."""
    from api.user_routes import active_sessions
    if session_token in active_sessions:
        user_id = active_sessions[session_token]["user_id"]
        return db.query(User).filter(User.id == user_id, User.is_active == True).first()
    return None


def require_role(allowed_roles: List[str]):
    """Decorator-like dependency to check user role."""
    def check_role(session_token: str, db: Session = Depends(get_db)):
        user = get_user_by_session(session_token, db)
        if not user:
            raise HTTPException(status_code=401, detail="Not authenticated")
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=403, 
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}"
            )
        return user
    return check_role


def log_activity(
    db: Session,
    user_id: int,
    action_type: str,
    description: str = None,
    analysis_id: int = None,
    related_entity_type: str = None,
    related_entity_id: int = None,
    extra_data: dict = None
):
    """Log user activity."""
    log = ActivityLog(
        user_id=user_id,
        action_type=action_type,
        action_description=description,
        analysis_id=analysis_id,
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id,
        extra_data=extra_data
    )
    db.add(log)
    db.commit()


# ============================================================================
# RadikalUser Endpoints
# ============================================================================

@router.get("/radikal-user/other-results", response_model=List[dict])
async def get_other_radikal_users_results(
    session_token: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    [RadikalUser] View results from other RadikalUsers.
    
    RadikalUsers can see what other RadikalUsers have analyzed.
    """
    user = get_user_by_session(session_token, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if user.role != UserRole.RADIKAL_USER:
        raise HTTPException(status_code=403, detail="Only RadikalUsers can access this endpoint")
    
    # Get analyses from other RadikalUsers
    offset = (page - 1) * page_size
    
    other_analyses = db.query(Analysis).join(
        User, Analysis.performed_by == User.id
    ).filter(
        User.role == UserRole.RADIKAL_USER,
        User.id != user.id
    ).order_by(
        Analysis.upload_timestamp.desc()
    ).offset(offset).limit(page_size).all()
    
    results = []
    for analysis in other_analyses:
        performer = db.query(User).filter(User.id == analysis.performed_by).first()
        results.append({
            "analysis_id": analysis.id,
            "image_id": analysis.image_id,
            "filename": analysis.filename,
            "performed_by": performer.full_name if performer else "Unknown",
            "performed_by_id": analysis.performed_by,
            "upload_timestamp": analysis.upload_timestamp,
            "has_defects": analysis.has_defects,
            "highest_severity": analysis.highest_severity,
            "num_detections": analysis.num_detections,
            "mean_confidence": analysis.mean_confidence,
            "status": analysis.status,
        })
    
    return results


@router.get("/radikal-user/my-analyses", response_model=List[dict])
async def get_my_analyses(
    session_token: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    [RadikalUser] View my own analysis history.
    """
    user = get_user_by_session(session_token, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if user.role != UserRole.RADIKAL_USER:
        raise HTTPException(status_code=403, detail="Only RadikalUsers can access this endpoint")
    
    offset = (page - 1) * page_size
    
    my_analyses = db.query(Analysis).filter(
        Analysis.performed_by == user.id
    ).order_by(
        Analysis.upload_timestamp.desc()
    ).offset(offset).limit(page_size).all()
    
    return [{
        "analysis_id": a.id,
        "image_id": a.image_id,
        "filename": a.filename,
        "upload_timestamp": a.upload_timestamp,
        "has_defects": a.has_defects,
        "highest_severity": a.highest_severity,
        "num_detections": a.num_detections,
        "mean_confidence": a.mean_confidence,
        "status": a.status,
    } for a in my_analyses]


@router.get("/radikal-user/pending-changes", response_model=List[ChangeRequestResponse])
async def get_my_pending_change_requests(
    session_token: str,
    db: Session = Depends(get_db),
):
    """
    [RadikalUser] View change requests assigned to me.
    """
    user = get_user_by_session(session_token, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if user.role != UserRole.RADIKAL_USER:
        raise HTTPException(status_code=403, detail="Only RadikalUsers can access this endpoint")
    
    change_requests = db.query(ChangeRequest).filter(
        ChangeRequest.assigned_to_id == user.id,
        ChangeRequest.status.in_(["pending", "in_progress"])
    ).order_by(
        ChangeRequest.created_at.desc()
    ).all()
    
    results = []
    for cr in change_requests:
        requester = db.query(User).filter(User.id == cr.requested_by_id).first()
        results.append(ChangeRequestResponse(
            id=cr.id,
            analysis_id=cr.analysis_id,
            requested_by_id=cr.requested_by_id,
            requested_by_name=requester.full_name if requester else None,
            assigned_to_id=cr.assigned_to_id,
            assigned_to_name=user.full_name,
            title=cr.title,
            description=cr.description,
            reason=cr.reason,
            priority=cr.priority,
            status=cr.status,
            resolution_notes=cr.resolution_notes,
            resolved_analysis_id=cr.resolved_analysis_id,
            created_at=cr.created_at,
            updated_at=cr.updated_at,
            due_date=cr.due_date,
            completed_at=cr.completed_at,
        ))
    
    return results


@router.patch("/radikal-user/change-request/{request_id}/complete")
async def complete_change_request(
    request_id: int,
    update_data: ChangeRequestUpdate,
    session_token: str,
    db: Session = Depends(get_db),
):
    """
    [RadikalUser] Mark a change request as completed.
    """
    user = get_user_by_session(session_token, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if user.role != UserRole.RADIKAL_USER:
        raise HTTPException(status_code=403, detail="Only RadikalUsers can access this endpoint")
    
    change_request = db.query(ChangeRequest).filter(
        ChangeRequest.id == request_id,
        ChangeRequest.assigned_to_id == user.id
    ).first()
    
    if not change_request:
        raise HTTPException(status_code=404, detail="Change request not found or not assigned to you")
    
    if update_data.status:
        change_request.status = update_data.status.value
    if update_data.resolution_notes:
        change_request.resolution_notes = update_data.resolution_notes
    if update_data.resolved_analysis_id:
        change_request.resolved_analysis_id = update_data.resolved_analysis_id
    
    if update_data.status and update_data.status.value == "completed":
        change_request.completed_at = datetime.utcnow()
    
    db.commit()
    
    log_activity(
        db, user.id, "change_request_completed",
        f"Completed change request #{request_id}",
        related_entity_type="change_request",
        related_entity_id=request_id
    )
    
    return {"success": True, "message": "Change request updated"}


# ============================================================================
# Chief Endpoints
# ============================================================================

@router.get("/chief/supervised-users", response_model=List[RadikalUserStats])
async def get_supervised_users_stats(
    session_token: str,
    db: Session = Depends(get_db),
):
    """
    [Chief] Get statistics for all supervised RadikalUsers.
    """
    user = get_user_by_session(session_token, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if user.role != UserRole.CHIEF:
        raise HTTPException(status_code=403, detail="Only Chiefs can access this endpoint")
    
    # Get all RadikalUsers supervised by this Chief
    supervised = db.query(User).filter(
        User.supervisor_id == user.id,
        User.is_active == True
    ).all()
    
    stats = []
    for radikal_user in supervised:
        # Count analyses
        total_analyses = db.query(Analysis).filter(
            Analysis.performed_by == radikal_user.id
        ).count()
        
        week_ago = datetime.utcnow() - timedelta(days=7)
        month_ago = datetime.utcnow() - timedelta(days=30)
        
        analyses_this_week = db.query(Analysis).filter(
            Analysis.performed_by == radikal_user.id,
            Analysis.upload_timestamp >= week_ago
        ).count()
        
        analyses_this_month = db.query(Analysis).filter(
            Analysis.performed_by == radikal_user.id,
            Analysis.upload_timestamp >= month_ago
        ).count()
        
        # Count change requests
        pending_crs = db.query(ChangeRequest).filter(
            ChangeRequest.assigned_to_id == radikal_user.id,
            ChangeRequest.status.in_(["pending", "in_progress"])
        ).count()
        
        completed_crs = db.query(ChangeRequest).filter(
            ChangeRequest.assigned_to_id == radikal_user.id,
            ChangeRequest.status == "completed"
        ).count()
        
        # Calculate average confidence
        avg_conf = db.query(func.avg(Analysis.mean_confidence)).filter(
            Analysis.performed_by == radikal_user.id
        ).scalar() or 0.0
        
        # Count defects
        defects = db.query(Analysis).filter(
            Analysis.performed_by == radikal_user.id,
            Analysis.has_defects == True
        ).count()
        
        # Last activity
        last_activity = db.query(ActivityLog).filter(
            ActivityLog.user_id == radikal_user.id
        ).order_by(ActivityLog.created_at.desc()).first()
        
        stats.append(RadikalUserStats(
            user_id=radikal_user.id,
            user_name=radikal_user.full_name,
            total_analyses=total_analyses,
            analyses_this_week=analyses_this_week,
            analyses_this_month=analyses_this_month,
            pending_change_requests=pending_crs,
            completed_change_requests=completed_crs,
            average_confidence=round(avg_conf, 3),
            defects_found=defects,
            last_activity=last_activity.created_at if last_activity else None
        ))
    
    return stats


@router.get("/chief/user/{user_id}/history", response_model=List[dict])
async def get_user_analysis_history(
    user_id: int,
    session_token: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    [Chief] View a RadikalUser's analysis history.
    """
    user = get_user_by_session(session_token, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if user.role != UserRole.CHIEF:
        raise HTTPException(status_code=403, detail="Only Chiefs can access this endpoint")
    
    # Verify the user is supervised by this chief
    target_user = db.query(User).filter(
        User.id == user_id,
        User.supervisor_id == user.id
    ).first()
    
    if not target_user:
        raise HTTPException(
            status_code=404, 
            detail="User not found or not supervised by you"
        )
    
    offset = (page - 1) * page_size
    
    analyses = db.query(Analysis).filter(
        Analysis.performed_by == user_id
    ).order_by(
        Analysis.upload_timestamp.desc()
    ).offset(offset).limit(page_size).all()
    
    return [{
        "analysis_id": a.id,
        "image_id": a.image_id,
        "filename": a.filename,
        "upload_timestamp": a.upload_timestamp,
        "has_defects": a.has_defects,
        "highest_severity": a.highest_severity,
        "num_detections": a.num_detections,
        "mean_confidence": a.mean_confidence,
        "status": a.status,
    } for a in analyses]


@router.post("/chief/change-request", response_model=ChangeRequestResponse)
async def create_change_request(
    request_data: ChangeRequestCreate,
    session_token: str,
    db: Session = Depends(get_db),
):
    """
    [Chief] Create a change request for a RadikalUser.
    """
    user = get_user_by_session(session_token, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if user.role != UserRole.CHIEF:
        raise HTTPException(status_code=403, detail="Only Chiefs can create change requests")
    
    # Verify analysis exists
    analysis = db.query(Analysis).filter(Analysis.id == request_data.analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    # Verify assigned user is a RadikalUser supervised by this chief
    assigned_user = db.query(User).filter(
        User.id == request_data.assigned_to_id,
        User.role == UserRole.RADIKAL_USER,
        User.supervisor_id == user.id
    ).first()
    
    if not assigned_user:
        raise HTTPException(
            status_code=400, 
            detail="Assigned user must be a RadikalUser supervised by you"
        )
    
    change_request = ChangeRequest(
        analysis_id=request_data.analysis_id,
        requested_by_id=user.id,
        assigned_to_id=request_data.assigned_to_id,
        title=request_data.title,
        description=request_data.description,
        reason=request_data.reason,
        priority=request_data.priority.value,
        due_date=request_data.due_date,
        status="pending"
    )
    
    db.add(change_request)
    db.commit()
    db.refresh(change_request)
    
    log_activity(
        db, user.id, "change_request_created",
        f"Created change request for analysis #{request_data.analysis_id}",
        analysis_id=request_data.analysis_id,
        related_entity_type="change_request",
        related_entity_id=change_request.id
    )
    
    return ChangeRequestResponse(
        id=change_request.id,
        analysis_id=change_request.analysis_id,
        requested_by_id=change_request.requested_by_id,
        requested_by_name=user.full_name,
        assigned_to_id=change_request.assigned_to_id,
        assigned_to_name=assigned_user.full_name,
        title=change_request.title,
        description=change_request.description,
        reason=change_request.reason,
        priority=change_request.priority,
        status=change_request.status,
        resolution_notes=change_request.resolution_notes,
        resolved_analysis_id=change_request.resolved_analysis_id,
        created_at=change_request.created_at,
        updated_at=change_request.updated_at,
        due_date=change_request.due_date,
        completed_at=change_request.completed_at,
    )


@router.post("/chief/comment", response_model=CommentResponse)
async def add_comment(
    comment_data: CommentCreate,
    session_token: str,
    db: Session = Depends(get_db),
):
    """
    [Chief] Add a comment to an analysis.
    """
    user = get_user_by_session(session_token, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if user.role != UserRole.CHIEF:
        raise HTTPException(status_code=403, detail="Only Chiefs can add comments")
    
    # Verify analysis exists
    analysis = db.query(Analysis).filter(Analysis.id == comment_data.analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    comment = AnalysisComment(
        analysis_id=comment_data.analysis_id,
        author_id=user.id,
        content=comment_data.content,
        comment_type=comment_data.comment_type.value,
        region_x=comment_data.region_x,
        region_y=comment_data.region_y,
        region_width=comment_data.region_width,
        region_height=comment_data.region_height,
        is_internal=comment_data.is_internal
    )
    
    db.add(comment)
    db.commit()
    db.refresh(comment)
    
    log_activity(
        db, user.id, "comment_added",
        f"Added comment to analysis #{comment_data.analysis_id}",
        analysis_id=comment_data.analysis_id
    )
    
    return CommentResponse(
        id=comment.id,
        analysis_id=comment.analysis_id,
        author_id=comment.author_id,
        author_name=user.full_name,
        content=comment.content,
        comment_type=comment.comment_type,
        region_x=comment.region_x,
        region_y=comment.region_y,
        region_width=comment.region_width,
        region_height=comment.region_height,
        is_internal=comment.is_internal,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
    )


@router.get("/chief/analysis/{analysis_id}/comments", response_model=List[CommentResponse])
async def get_analysis_comments(
    analysis_id: int,
    session_token: str,
    db: Session = Depends(get_db),
):
    """
    [Chief] Get all comments on an analysis.
    """
    user = get_user_by_session(session_token, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if user.role not in [UserRole.CHIEF, UserRole.MANAGER]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    comments = db.query(AnalysisComment).filter(
        AnalysisComment.analysis_id == analysis_id
    ).order_by(AnalysisComment.created_at.desc()).all()
    
    results = []
    for c in comments:
        author = db.query(User).filter(User.id == c.author_id).first()
        results.append(CommentResponse(
            id=c.id,
            analysis_id=c.analysis_id,
            author_id=c.author_id,
            author_name=author.full_name if author else None,
            content=c.content,
            comment_type=c.comment_type,
            region_x=c.region_x,
            region_y=c.region_y,
            region_width=c.region_width,
            region_height=c.region_height,
            is_internal=c.is_internal,
            created_at=c.created_at,
            updated_at=c.updated_at,
        ))
    
    return results


@router.get("/chief/user/{user_id}/activity-chart", response_model=UserActivityChartData)
async def get_user_activity_chart(
    user_id: int,
    session_token: str,
    days: int = Query(30, ge=7, le=90),
    db: Session = Depends(get_db),
):
    """
    [Chief] Get activity chart data for a RadikalUser.
    """
    user = get_user_by_session(session_token, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if user.role != UserRole.CHIEF:
        raise HTTPException(status_code=403, detail="Only Chiefs can access this endpoint")
    
    # Verify the user is supervised by this chief
    target_user = db.query(User).filter(
        User.id == user_id,
        User.supervisor_id == user.id
    ).first()
    
    if not target_user:
        raise HTTPException(
            status_code=404, 
            detail="User not found or not supervised by you"
        )
    
    # Generate chart data for the last N days
    labels = []
    analyses_data = []
    defects_data = []
    
    for i in range(days - 1, -1, -1):
        date = datetime.utcnow() - timedelta(days=i)
        date_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        date_end = date_start + timedelta(days=1)
        
        labels.append(date_start.strftime("%Y-%m-%d"))
        
        analyses_count = db.query(Analysis).filter(
            Analysis.performed_by == user_id,
            Analysis.upload_timestamp >= date_start,
            Analysis.upload_timestamp < date_end
        ).count()
        
        defects_count = db.query(Analysis).filter(
            Analysis.performed_by == user_id,
            Analysis.upload_timestamp >= date_start,
            Analysis.upload_timestamp < date_end,
            Analysis.has_defects == True
        ).count()
        
        analyses_data.append(analyses_count)
        defects_data.append(defects_count)
    
    return UserActivityChartData(
        labels=labels,
        datasets=[
            {
                "label": "Analyses Performed",
                "data": analyses_data,
                "borderColor": "#3b82f6",
                "backgroundColor": "rgba(59, 130, 246, 0.2)",
            },
            {
                "label": "Defects Found",
                "data": defects_data,
                "borderColor": "#ef4444",
                "backgroundColor": "rgba(239, 68, 68, 0.2)",
            }
        ]
    )


@router.get("/chief/dashboard", response_model=ChiefDashboardStats)
async def get_chief_dashboard(
    session_token: str,
    db: Session = Depends(get_db),
):
    """
    [Chief] Get dashboard statistics.
    """
    user = get_user_by_session(session_token, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if user.role != UserRole.CHIEF:
        raise HTTPException(status_code=403, detail="Only Chiefs can access this endpoint")
    
    # Count supervised users
    supervised_count = db.query(User).filter(
        User.supervisor_id == user.id,
        User.is_active == True
    ).count()
    
    # Get IDs of supervised users
    supervised_ids = [u.id for u in db.query(User).filter(
        User.supervisor_id == user.id
    ).all()]
    
    # Total analyses by team
    total_analyses = db.query(Analysis).filter(
        Analysis.performed_by.in_(supervised_ids)
    ).count() if supervised_ids else 0
    
    # Pending reviews (analyses not yet reviewed)
    pending_reviews = db.query(Analysis).filter(
        Analysis.performed_by.in_(supervised_ids),
        ~Analysis.id.in_(
            db.query(Review.analysis_id).filter(Review.status == "approved")
        )
    ).count() if supervised_ids else 0
    
    # Change requests
    change_requests_sent = db.query(ChangeRequest).filter(
        ChangeRequest.requested_by_id == user.id
    ).count()
    
    change_requests_completed = db.query(ChangeRequest).filter(
        ChangeRequest.requested_by_id == user.id,
        ChangeRequest.status == "completed"
    ).count()
    
    # Recent activity
    recent_logs = db.query(ActivityLog).filter(
        ActivityLog.user_id.in_(supervised_ids + [user.id])
    ).order_by(
        ActivityLog.created_at.desc()
    ).limit(10).all()
    
    recent_activity = []
    for log in recent_logs:
        log_user = db.query(User).filter(User.id == log.user_id).first()
        recent_activity.append(ActivityLogResponse(
            id=log.id,
            user_id=log.user_id,
            user_name=log_user.full_name if log_user else None,
            action_type=log.action_type,
            action_description=log.action_description,
            analysis_id=log.analysis_id,
            related_entity_type=log.related_entity_type,
            related_entity_id=log.related_entity_id,
            created_at=log.created_at,
        ))
    
    return ChiefDashboardStats(
        supervised_users_count=supervised_count,
        total_analyses_by_team=total_analyses,
        pending_reviews=pending_reviews,
        change_requests_sent=change_requests_sent,
        change_requests_completed=change_requests_completed,
        recent_activity=recent_activity
    )


# ============================================================================
# Manager Endpoints
# ============================================================================

@router.get("/manager/dashboard", response_model=ManagerDashboardStats)
async def get_manager_dashboard(
    session_token: str,
    db: Session = Depends(get_db),
):
    """
    [Manager] Get comprehensive dashboard statistics.
    """
    user = get_user_by_session(session_token, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if user.role != UserRole.MANAGER:
        raise HTTPException(status_code=403, detail="Only Managers can access this endpoint")
    
    # User counts
    total_users = db.query(User).filter(User.is_active == True).count()
    total_radikal_users = db.query(User).filter(
        User.role == UserRole.RADIKAL_USER,
        User.is_active == True
    ).count()
    total_chiefs = db.query(User).filter(
        User.role == UserRole.CHIEF,
        User.is_active == True
    ).count()
    
    # Analysis counts
    total_analyses = db.query(Analysis).count()
    
    week_ago = datetime.utcnow() - timedelta(days=7)
    month_ago = datetime.utcnow() - timedelta(days=30)
    
    analyses_this_week = db.query(Analysis).filter(
        Analysis.upload_timestamp >= week_ago
    ).count()
    
    analyses_this_month = db.query(Analysis).filter(
        Analysis.upload_timestamp >= month_ago
    ).count()
    
    # Change requests
    pending_crs = db.query(ChangeRequest).filter(
        ChangeRequest.status.in_(["pending", "in_progress"])
    ).count()
    
    completed_crs = db.query(ChangeRequest).filter(
        ChangeRequest.status == "completed"
    ).count()
    
    # Top performers
    radikal_users = db.query(User).filter(
        User.role == UserRole.RADIKAL_USER,
        User.is_active == True
    ).all()
    
    top_performers = []
    for ru in radikal_users:
        analyses_count = db.query(Analysis).filter(
            Analysis.performed_by == ru.id,
            Analysis.upload_timestamp >= month_ago
        ).count()
        
        avg_conf = db.query(func.avg(Analysis.mean_confidence)).filter(
            Analysis.performed_by == ru.id
        ).scalar() or 0.0
        
        top_performers.append({
            "user_id": ru.id,
            "user_name": ru.full_name,
            "analyses_this_month": analyses_count,
            "average_confidence": avg_conf
        })
    
    # Sort by analyses count and get top 5
    top_performers.sort(key=lambda x: x["analyses_this_month"], reverse=True)
    top_performers = top_performers[:5]
    
    # Convert to RadikalUserStats
    top_stats = []
    for tp in top_performers:
        user_data = db.query(User).filter(User.id == tp["user_id"]).first()
        total_analyses_user = db.query(Analysis).filter(
            Analysis.performed_by == tp["user_id"]
        ).count()
        
        analyses_week = db.query(Analysis).filter(
            Analysis.performed_by == tp["user_id"],
            Analysis.upload_timestamp >= week_ago
        ).count()
        
        pending = db.query(ChangeRequest).filter(
            ChangeRequest.assigned_to_id == tp["user_id"],
            ChangeRequest.status.in_(["pending", "in_progress"])
        ).count()
        
        completed = db.query(ChangeRequest).filter(
            ChangeRequest.assigned_to_id == tp["user_id"],
            ChangeRequest.status == "completed"
        ).count()
        
        defects = db.query(Analysis).filter(
            Analysis.performed_by == tp["user_id"],
            Analysis.has_defects == True
        ).count()
        
        last_act = db.query(ActivityLog).filter(
            ActivityLog.user_id == tp["user_id"]
        ).order_by(ActivityLog.created_at.desc()).first()
        
        top_stats.append(RadikalUserStats(
            user_id=tp["user_id"],
            user_name=tp["user_name"],
            total_analyses=total_analyses_user,
            analyses_this_week=analyses_week,
            analyses_this_month=tp["analyses_this_month"],
            pending_change_requests=pending,
            completed_change_requests=completed,
            average_confidence=round(tp["average_confidence"], 3),
            defects_found=defects,
            last_activity=last_act.created_at if last_act else None
        ))
    
    return ManagerDashboardStats(
        total_users=total_users,
        total_radikal_users=total_radikal_users,
        total_chiefs=total_chiefs,
        total_analyses=total_analyses,
        pending_change_requests=pending_crs,
        completed_change_requests=completed_crs,
        analyses_this_week=analyses_this_week,
        analyses_this_month=analyses_this_month,
        top_performers=top_stats
    )


@router.get("/manager/change-requests", response_model=ChangeRequestListResponse)
async def get_all_change_requests(
    session_token: str,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    [Manager] Get list of all change requests.
    """
    user = get_user_by_session(session_token, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if user.role != UserRole.MANAGER:
        raise HTTPException(status_code=403, detail="Only Managers can access this endpoint")
    
    query = db.query(ChangeRequest)
    
    if status:
        query = query.filter(ChangeRequest.status == status)
    
    total = query.count()
    
    offset = (page - 1) * page_size
    change_requests = query.order_by(
        ChangeRequest.created_at.desc()
    ).offset(offset).limit(page_size).all()
    
    items = []
    for cr in change_requests:
        requester = db.query(User).filter(User.id == cr.requested_by_id).first()
        assigned = db.query(User).filter(User.id == cr.assigned_to_id).first()
        
        items.append(ChangeRequestResponse(
            id=cr.id,
            analysis_id=cr.analysis_id,
            requested_by_id=cr.requested_by_id,
            requested_by_name=requester.full_name if requester else None,
            assigned_to_id=cr.assigned_to_id,
            assigned_to_name=assigned.full_name if assigned else None,
            title=cr.title,
            description=cr.description,
            reason=cr.reason,
            priority=cr.priority,
            status=cr.status,
            resolution_notes=cr.resolution_notes,
            resolved_analysis_id=cr.resolved_analysis_id,
            created_at=cr.created_at,
            updated_at=cr.updated_at,
            due_date=cr.due_date,
            completed_at=cr.completed_at,
        ))
    
    return ChangeRequestListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/manager/all-analyses", response_model=List[dict])
async def get_all_analyses(
    session_token: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
):
    """
    [Manager] Get all analysis results (read-only view).
    """
    user = get_user_by_session(session_token, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if user.role != UserRole.MANAGER:
        raise HTTPException(status_code=403, detail="Only Managers can access this endpoint")
    
    query = db.query(Analysis)
    
    if start_date:
        query = query.filter(Analysis.upload_timestamp >= start_date)
    if end_date:
        query = query.filter(Analysis.upload_timestamp <= end_date)
    
    offset = (page - 1) * page_size
    analyses = query.order_by(
        Analysis.upload_timestamp.desc()
    ).offset(offset).limit(page_size).all()
    
    results = []
    for a in analyses:
        performer = db.query(User).filter(User.id == a.performed_by).first()
        results.append({
            "analysis_id": a.id,
            "image_id": a.image_id,
            "filename": a.filename,
            "performed_by": performer.full_name if performer else "Unknown",
            "performed_by_id": a.performed_by,
            "upload_timestamp": a.upload_timestamp,
            "has_defects": a.has_defects,
            "highest_severity": a.highest_severity,
            "num_detections": a.num_detections,
            "mean_confidence": a.mean_confidence,
            "status": a.status,
        })
    
    return results


@router.get("/manager/user-activity-overview", response_model=List[UserActivitySummaryResponse])
async def get_all_users_activity_overview(
    session_token: str,
    period: str = Query("weekly", description="daily, weekly, monthly"),
    db: Session = Depends(get_db),
):
    """
    [Manager] Get activity overview for all RadikalUsers.
    """
    user = get_user_by_session(session_token, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if user.role != UserRole.MANAGER:
        raise HTTPException(status_code=403, detail="Only Managers can access this endpoint")
    
    # Calculate period
    now = datetime.utcnow()
    if period == "daily":
        period_start = now - timedelta(days=1)
    elif period == "weekly":
        period_start = now - timedelta(weeks=1)
    else:  # monthly
        period_start = now - timedelta(days=30)
    
    radikal_users = db.query(User).filter(
        User.role == UserRole.RADIKAL_USER,
        User.is_active == True
    ).all()
    
    summaries = []
    for ru in radikal_users:
        analyses = db.query(Analysis).filter(
            Analysis.performed_by == ru.id,
            Analysis.upload_timestamp >= period_start
        ).count()
        
        defects = db.query(Analysis).filter(
            Analysis.performed_by == ru.id,
            Analysis.upload_timestamp >= period_start,
            Analysis.has_defects == True
        ).count()
        
        avg_conf = db.query(func.avg(Analysis.mean_confidence)).filter(
            Analysis.performed_by == ru.id,
            Analysis.upload_timestamp >= period_start
        ).scalar() or 0.0
        
        avg_time = db.query(func.avg(Analysis.inference_time_ms)).filter(
            Analysis.performed_by == ru.id,
            Analysis.upload_timestamp >= period_start
        ).scalar() or 0.0
        
        crs_received = db.query(ChangeRequest).filter(
            ChangeRequest.assigned_to_id == ru.id,
            ChangeRequest.created_at >= period_start
        ).count()
        
        crs_completed = db.query(ChangeRequest).filter(
            ChangeRequest.assigned_to_id == ru.id,
            ChangeRequest.status == "completed",
            ChangeRequest.completed_at >= period_start
        ).count()
        
        logins = db.query(ActivityLog).filter(
            ActivityLog.user_id == ru.id,
            ActivityLog.action_type == "login",
            ActivityLog.created_at >= period_start
        ).count()
        
        summaries.append(UserActivitySummaryResponse(
            user_id=ru.id,
            user_name=ru.full_name,
            period_type=period,
            period_start=period_start,
            period_end=now,
            analyses_performed=analyses,
            analyses_reviewed=0,  # RadikalUsers don't review
            change_requests_received=crs_received,
            change_requests_completed=crs_completed,
            comments_made=0,  # RadikalUsers don't comment
            login_count=logins,
            defects_found=defects,
            average_confidence=round(avg_conf, 3),
            average_processing_time_ms=round(avg_time, 2)
        ))
    
    return summaries


# ============================================================================
# Common Endpoints
# ============================================================================

@router.get("/permissions")
async def get_my_permissions(
    session_token: str,
    db: Session = Depends(get_db),
):
    """
    Get current user's role-based permissions.
    """
    user = get_user_by_session(session_token, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    return {
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
        "permissions": {
            "can_use_models": UserRole.can_use_models(user.role),
            "can_review": UserRole.can_review(user.role),
            "can_request_changes": UserRole.can_request_changes(user.role),
            "can_add_comments": UserRole.can_add_comments(user.role),
            "can_view_all_users": UserRole.can_view_all_users(user.role),
            "can_view_change_requests": UserRole.can_view_change_requests(user.role),
        }
    }
