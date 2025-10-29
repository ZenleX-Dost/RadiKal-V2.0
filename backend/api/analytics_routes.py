"""
Analytics and Historical Trends API Routes

Provides endpoints for:
- Historical defect trends analysis
- Comparative statistics
- Performance metrics over time
- Operator/project analytics
"""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import logging

from api.schemas import (
    TrendAnalysisResponse,
    DefectTrendData,
    ComparativeAnalysis,
    OperatorPerformance,
    ProjectQualityScore,
)
from db import get_db, Analysis, Detection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/xai-qc/analytics", tags=["Analytics"])


@router.get("/trends", response_model=TrendAnalysisResponse)
async def get_defect_trends(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    group_by: str = Query("day", description="Grouping: day, week, month"),
    defect_type: Optional[str] = Query(None, description="Filter by defect type"),
    db: Session = Depends(get_db),
):
    """
    Get historical defect trends over time.
    
    Returns time-series data showing:
    - Defect counts by type
    - Defect rates
    - Average confidence scores
    - Severity distribution
    """
    try:
        # Parse dates or use defaults (last 30 days)
        if start_date:
            start = datetime.fromisoformat(start_date)
        else:
            start = datetime.now() - timedelta(days=30)
        
        if end_date:
            end = datetime.fromisoformat(end_date)
        else:
            end = datetime.now()
        
        # Query analyses in date range
        query = db.query(Analysis).filter(
            and_(
                Analysis.upload_timestamp >= start,
                Analysis.upload_timestamp <= end,
                Analysis.status == "completed"
            )
        )
        
        analyses = query.all()
        
        # Group data by time period
        trends = _aggregate_by_period(analyses, group_by, start, end)
        
        # Calculate statistics
        total_inspections = len(analyses)
        defect_count = sum(1 for a in analyses if a.has_defects)
        defect_rate = (defect_count / total_inspections * 100) if total_inspections > 0 else 0
        
        # Get defect type distribution
        defect_types = {}
        for analysis in analyses:
            if analysis.detections:
                for det in analysis.detections:
                    class_name = det.class_name
                    if class_name not in ['ND', 'No Defect']:
                        defect_types[class_name] = defect_types.get(class_name, 0) + 1
        
        return TrendAnalysisResponse(
            start_date=start,
            end_date=end,
            total_inspections=total_inspections,
            defect_rate=defect_rate,
            trends=trends,
            defect_type_distribution=defect_types,
            group_by=group_by,
        )
        
    except Exception as e:
        logger.error(f"Failed to get trends: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Trend analysis failed: {str(e)}")


@router.get("/compare", response_model=ComparativeAnalysis)
async def compare_periods(
    period1_start: str = Query(..., description="Period 1 start (YYYY-MM-DD)"),
    period1_end: str = Query(..., description="Period 1 end (YYYY-MM-DD)"),
    period2_start: str = Query(..., description="Period 2 start (YYYY-MM-DD)"),
    period2_end: str = Query(..., description="Period 2 end (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """
    Compare quality metrics between two time periods.
    
    Useful for:
    - Before/after process changes
    - Month-over-month comparisons
    - Operator training effectiveness
    """
    try:
        p1_start = datetime.fromisoformat(period1_start)
        p1_end = datetime.fromisoformat(period1_end)
        p2_start = datetime.fromisoformat(period2_start)
        p2_end = datetime.fromisoformat(period2_end)
        
        # Get data for both periods
        period1_data = _get_period_metrics(db, p1_start, p1_end)
        period2_data = _get_period_metrics(db, p2_start, p2_end)
        
        # Calculate changes
        defect_rate_change = period2_data['defect_rate'] - period1_data['defect_rate']
        quality_improvement = -defect_rate_change  # Negative change = improvement
        
        return ComparativeAnalysis(
            period1=period1_data,
            period2=period2_data,
            defect_rate_change=defect_rate_change,
            quality_improvement_percent=quality_improvement,
            significant_changes=_identify_significant_changes(period1_data, period2_data),
        )
        
    except Exception as e:
        logger.error(f"Comparison failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")


@router.get("/operators", response_model=List[OperatorPerformance])
async def get_operator_performance(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Get performance metrics by operator/user.
    
    Shows:
    - Inspections per operator
    - Defect detection rates
    - Average confidence scores
    - Quality scores
    """
    try:
        # Note: Requires operator_id field in Analysis table
        # For now, return mock data structure
        logger.warning("Operator tracking not yet implemented - returning placeholder")
        
        return [
            OperatorPerformance(
                operator_id="OP001",
                operator_name="System",
                total_inspections=0,
                defects_found=0,
                defect_rate=0.0,
                avg_confidence=0.0,
                quality_score=0.0,
            )
        ]
        
    except Exception as e:
        logger.error(f"Operator analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def _aggregate_by_period(analyses, group_by, start, end):
    """Aggregate analyses by time period."""
    from collections import defaultdict
    
    trends = []
    
    # Create time buckets
    if group_by == "day":
        delta = timedelta(days=1)
    elif group_by == "week":
        delta = timedelta(weeks=1)
    elif group_by == "month":
        delta = timedelta(days=30)
    else:
        delta = timedelta(days=1)
    
    current = start
    while current <= end:
        next_period = current + delta
        
        # Count analyses in this period
        period_analyses = [
            a for a in analyses
            if current <= a.upload_timestamp < next_period
        ]
        
        if period_analyses:
            defect_count = sum(1 for a in period_analyses if a.has_defects)
            total = len(period_analyses)
            
            trends.append(DefectTrendData(
                date=current,
                total_inspections=total,
                defect_count=defect_count,
                defect_rate=(defect_count / total * 100) if total > 0 else 0,
                avg_confidence=sum(a.mean_confidence or 0 for a in period_analyses) / total if total > 0 else 0,
            ))
        
        current = next_period
    
    return trends


def _get_period_metrics(db: Session, start: datetime, end: datetime):
    """Calculate metrics for a time period."""
    analyses = db.query(Analysis).filter(
        and_(
            Analysis.upload_timestamp >= start,
            Analysis.upload_timestamp <= end,
            Analysis.status == "completed"
        )
    ).all()
    
    total = len(analyses)
    defects = sum(1 for a in analyses if a.has_defects)
    
    # Defect type counts
    defect_types = {}
    for analysis in analyses:
        if analysis.detections:
            for det in analysis.detections:
                class_name = det.class_name
                if class_name not in ['ND', 'No Defect']:
                    defect_types[class_name] = defect_types.get(class_name, 0) + 1
    
    return {
        'start_date': start,
        'end_date': end,
        'total_inspections': total,
        'defect_count': defects,
        'defect_rate': (defects / total * 100) if total > 0 else 0,
        'defect_types': defect_types,
        'avg_confidence': sum(a.mean_confidence or 0 for a in analyses) / total if total > 0 else 0,
    }


def _identify_significant_changes(period1, period2):
    """Identify statistically significant changes between periods."""
    changes = []
    
    # Check defect rate change
    rate_change = abs(period2['defect_rate'] - period1['defect_rate'])
    if rate_change > 5:  # More than 5% change
        direction = "increased" if period2['defect_rate'] > period1['defect_rate'] else "decreased"
        changes.append(f"Defect rate {direction} by {rate_change:.1f}%")
    
    # Check new defect types
    new_types = set(period2['defect_types'].keys()) - set(period1['defect_types'].keys())
    if new_types:
        changes.append(f"New defect types detected: {', '.join(new_types)}")
    
    # Check defect type changes
    for defect_type in period1['defect_types']:
        if defect_type in period2['defect_types']:
            p1_count = period1['defect_types'][defect_type]
            p2_count = period2['defect_types'][defect_type]
            if abs(p2_count - p1_count) > 3:
                direction = "increase" if p2_count > p1_count else "decrease"
                changes.append(f"{defect_type}: {direction} of {abs(p2_count - p1_count)} detections")
    
    return changes
