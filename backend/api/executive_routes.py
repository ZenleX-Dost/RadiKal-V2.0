"""
Executive Dashboard API Routes

C-level dashboard with KPIs, trends, and business metrics
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from enum import Enum

from core.auth import get_current_user

router = APIRouter(prefix="/api/executive", tags=["executive"])


class TimeRange(str, Enum):
    """Time range for metrics"""
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"
    CUSTOM = "custom"


class MetricType(str, Enum):
    """Types of executive metrics"""
    DEFECT_RATE = "defect_rate"
    THROUGHPUT = "throughput"
    COST_SAVINGS = "cost_savings"
    EFFICIENCY = "efficiency"
    QUALITY_SCORE = "quality_score"
    COMPLIANCE = "compliance"
    ROI = "roi"


# Response Models

class KPIMetric(BaseModel):
    """Key Performance Indicator"""
    name: str
    value: float
    unit: str
    change: float  # Percentage change from previous period
    trend: str  # "up", "down", "stable"
    target: Optional[float] = None
    status: str  # "good", "warning", "critical"


class TrendData(BaseModel):
    """Time series trend data"""
    timestamp: str
    value: float
    label: str


class DefectDistribution(BaseModel):
    """Defect type distribution"""
    defect_type: str
    count: int
    percentage: float
    cost_impact: float


class SiteMetrics(BaseModel):
    """Metrics per site/facility"""
    site_id: str
    site_name: str
    total_inspections: int
    defect_rate: float
    quality_score: float
    throughput: int
    cost_savings: float


# Dashboard Endpoints

@router.get("/dashboard")
async def get_executive_dashboard(
    time_range: TimeRange = Query(TimeRange.MONTH),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get complete executive dashboard data"""
    
    # Verify user has executive access
    if current_user.get("role") not in ["manager", "project_chief"]:
        raise HTTPException(status_code=403, detail="Executive access required")
    
    tenant_id = current_user.get("tenant_id")
    
    # Calculate date range
    if time_range == TimeRange.CUSTOM and start_date and end_date:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
    else:
        end = datetime.now()
        if time_range == TimeRange.DAY:
            start = end - timedelta(days=1)
        elif time_range == TimeRange.WEEK:
            start = end - timedelta(weeks=1)
        elif time_range == TimeRange.MONTH:
            start = end - timedelta(days=30)
        elif time_range == TimeRange.QUARTER:
            start = end - timedelta(days=90)
        elif time_range == TimeRange.YEAR:
            start = end - timedelta(days=365)
        else:
            start = end - timedelta(days=30)
    
    # In production, query from database
    # For now, return mock data
    
    return {
        "period": {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "range": time_range
        },
        "kpis": {
            "defect_rate": {
                "name": "Defect Rate",
                "value": 12.5,
                "unit": "%",
                "change": -2.3,
                "trend": "down",
                "target": 10.0,
                "status": "warning"
            },
            "throughput": {
                "name": "Throughput",
                "value": 4567,
                "unit": "inspections",
                "change": 15.8,
                "trend": "up",
                "target": 5000,
                "status": "good"
            },
            "cost_savings": {
                "name": "Cost Savings",
                "value": 234567,
                "unit": "USD",
                "change": 8.5,
                "trend": "up",
                "target": 250000,
                "status": "good"
            },
            "quality_score": {
                "name": "Quality Score",
                "value": 94.8,
                "unit": "%",
                "change": 1.2,
                "trend": "up",
                "target": 95.0,
                "status": "good"
            },
            "efficiency": {
                "name": "Efficiency",
                "value": 87.3,
                "unit": "%",
                "change": 3.5,
                "trend": "up",
                "target": 90.0,
                "status": "good"
            },
            "roi": {
                "name": "ROI",
                "value": 245,
                "unit": "%",
                "change": 12.0,
                "trend": "up",
                "target": 200,
                "status": "good"
            }
        },
        "trends": {
            "defect_rate": [
                {"date": "2024-01-01", "value": 14.2},
                {"date": "2024-01-08", "value": 13.8},
                {"date": "2024-01-15", "value": 13.1},
                {"date": "2024-01-22", "value": 12.5}
            ],
            "throughput": [
                {"date": "2024-01-01", "value": 3850},
                {"date": "2024-01-08", "value": 4120},
                {"date": "2024-01-15", "value": 4350},
                {"date": "2024-01-22", "value": 4567}
            ],
            "cost_savings": [
                {"date": "2024-01-01", "value": 198000},
                {"date": "2024-01-08", "value": 215000},
                {"date": "2024-01-15", "value": 228000},
                {"date": "2024-01-22", "value": 234567}
            ]
        },
        "defect_distribution": [
            {"type": "Crack", "count": 145, "percentage": 32.5, "cost_impact": 87000},
            {"type": "Porosity", "count": 123, "percentage": 27.6, "cost_impact": 62000},
            {"type": "Lack of Fusion", "count": 98, "percentage": 22.0, "cost_impact": 98000},
            {"type": "Slag Inclusion", "count": 56, "percentage": 12.5, "cost_impact": 34000},
            {"type": "Undercut", "count": 24, "percentage": 5.4, "cost_impact": 15000}
        ],
        "site_metrics": [
            {
                "site_id": "site_001",
                "site_name": "Houston Plant",
                "total_inspections": 1234,
                "defect_rate": 11.2,
                "quality_score": 95.5,
                "throughput": 1234,
                "cost_savings": 87000
            },
            {
                "site_id": "site_002",
                "site_name": "Dallas Facility",
                "total_inspections": 1456,
                "defect_rate": 13.5,
                "quality_score": 94.2,
                "throughput": 1456,
                "cost_savings": 72000
            },
            {
                "site_id": "site_003",
                "site_name": "Austin Workshop",
                "total_inspections": 987,
                "defect_rate": 12.8,
                "quality_score": 94.8,
                "throughput": 987,
                "cost_savings": 56000
            }
        ]
    }


@router.get("/kpis")
async def get_kpis(
    time_range: TimeRange = Query(TimeRange.MONTH),
    metric_type: Optional[MetricType] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get Key Performance Indicators"""
    
    if current_user.get("role") not in ["manager", "project_chief"]:
        raise HTTPException(status_code=403, detail="Executive access required")
    
    kpis = {
        "defect_rate": {
            "name": "Defect Rate",
            "value": 12.5,
            "unit": "%",
            "change": -2.3,
            "trend": "down",
            "target": 10.0,
            "status": "warning",
            "description": "Percentage of inspections with detected defects"
        },
        "throughput": {
            "name": "Throughput",
            "value": 4567,
            "unit": "inspections",
            "change": 15.8,
            "trend": "up",
            "target": 5000,
            "status": "good",
            "description": "Total inspections completed in period"
        },
        "cost_savings": {
            "name": "Cost Savings",
            "value": 234567,
            "unit": "USD",
            "change": 8.5,
            "trend": "up",
            "target": 250000,
            "status": "good",
            "description": "Estimated cost savings from early defect detection"
        },
        "quality_score": {
            "name": "Quality Score",
            "value": 94.8,
            "unit": "%",
            "change": 1.2,
            "trend": "up",
            "target": 95.0,
            "status": "good",
            "description": "Overall quality assurance score"
        },
        "efficiency": {
            "name": "Efficiency",
            "value": 87.3,
            "unit": "%",
            "change": 3.5,
            "trend": "up",
            "target": 90.0,
            "status": "good",
            "description": "Inspection efficiency vs manual process"
        },
        "roi": {
            "name": "ROI",
            "value": 245,
            "unit": "%",
            "change": 12.0,
            "trend": "up",
            "target": 200,
            "status": "good",
            "description": "Return on investment for RadiKal system"
        }
    }
    
    if metric_type:
        return kpis.get(metric_type.value, {})
    
    return kpis


@router.get("/trends/{metric_type}")
async def get_trend_data(
    metric_type: MetricType,
    time_range: TimeRange = Query(TimeRange.MONTH),
    granularity: str = Query("day", regex="^(hour|day|week|month)$"),
    current_user: dict = Depends(get_current_user)
):
    """Get trend data for specific metric"""
    
    if current_user.get("role") not in ["manager", "project_chief"]:
        raise HTTPException(status_code=403, detail="Executive access required")
    
    # Generate mock trend data
    # In production, query from time-series database
    
    trends = {
        "defect_rate": [
            {"timestamp": "2024-01-01T00:00:00Z", "value": 14.2, "label": "Week 1"},
            {"timestamp": "2024-01-08T00:00:00Z", "value": 13.8, "label": "Week 2"},
            {"timestamp": "2024-01-15T00:00:00Z", "value": 13.1, "label": "Week 3"},
            {"timestamp": "2024-01-22T00:00:00Z", "value": 12.5, "label": "Week 4"}
        ],
        "throughput": [
            {"timestamp": "2024-01-01T00:00:00Z", "value": 3850, "label": "Week 1"},
            {"timestamp": "2024-01-08T00:00:00Z", "value": 4120, "label": "Week 2"},
            {"timestamp": "2024-01-15T00:00:00Z", "value": 4350, "label": "Week 3"},
            {"timestamp": "2024-01-22T00:00:00Z", "value": 4567, "label": "Week 4"}
        ],
        "cost_savings": [
            {"timestamp": "2024-01-01T00:00:00Z", "value": 198000, "label": "Week 1"},
            {"timestamp": "2024-01-08T00:00:00Z", "value": 215000, "label": "Week 2"},
            {"timestamp": "2024-01-15T00:00:00Z", "value": 228000, "label": "Week 3"},
            {"timestamp": "2024-01-22T00:00:00Z", "value": 234567, "label": "Week 4"}
        ]
    }
    
    return {
        "metric_type": metric_type,
        "time_range": time_range,
        "granularity": granularity,
        "data": trends.get(metric_type.value, [])
    }


@router.get("/defect-distribution")
async def get_defect_distribution(
    time_range: TimeRange = Query(TimeRange.MONTH),
    current_user: dict = Depends(get_current_user)
):
    """Get defect type distribution analysis"""
    
    if current_user.get("role") not in ["manager", "project_chief"]:
        raise HTTPException(status_code=403, detail="Executive access required")
    
    return {
        "total_defects": 446,
        "distribution": [
            {
                "defect_type": "Crack",
                "count": 145,
                "percentage": 32.5,
                "cost_impact": 87000,
                "severity": "critical",
                "trend": "decreasing"
            },
            {
                "defect_type": "Porosity",
                "count": 123,
                "percentage": 27.6,
                "cost_impact": 62000,
                "severity": "major",
                "trend": "stable"
            },
            {
                "defect_type": "Lack of Fusion",
                "count": 98,
                "percentage": 22.0,
                "cost_impact": 98000,
                "severity": "critical",
                "trend": "increasing"
            },
            {
                "defect_type": "Slag Inclusion",
                "count": 56,
                "percentage": 12.5,
                "cost_impact": 34000,
                "severity": "moderate",
                "trend": "stable"
            },
            {
                "defect_type": "Undercut",
                "count": 24,
                "percentage": 5.4,
                "cost_impact": 15000,
                "severity": "minor",
                "trend": "decreasing"
            }
        ]
    }


@router.get("/site-comparison")
async def get_site_comparison(
    time_range: TimeRange = Query(TimeRange.MONTH),
    current_user: dict = Depends(get_current_user)
):
    """Get comparative metrics across sites"""
    
    if current_user.get("role") not in ["manager", "project_chief"]:
        raise HTTPException(status_code=403, detail="Executive access required")
    
    return {
        "sites": [
            {
                "site_id": "site_001",
                "site_name": "Houston Plant",
                "location": "Houston, TX",
                "total_inspections": 1234,
                "defect_rate": 11.2,
                "quality_score": 95.5,
                "throughput": 1234,
                "cost_savings": 87000,
                "efficiency": 89.5,
                "rank": 1
            },
            {
                "site_id": "site_002",
                "site_name": "Dallas Facility",
                "location": "Dallas, TX",
                "total_inspections": 1456,
                "defect_rate": 13.5,
                "quality_score": 94.2,
                "throughput": 1456,
                "cost_savings": 72000,
                "efficiency": 86.2,
                "rank": 2
            },
            {
                "site_id": "site_003",
                "site_name": "Austin Workshop",
                "location": "Austin, TX",
                "total_inspections": 987,
                "defect_rate": 12.8,
                "quality_score": 94.8,
                "throughput": 987,
                "cost_savings": 56000,
                "efficiency": 88.1,
                "rank": 3
            }
        ],
        "summary": {
            "total_sites": 3,
            "best_performer": "Houston Plant",
            "highest_quality": "Houston Plant",
            "highest_throughput": "Dallas Facility"
        }
    }


@router.get("/financial-impact")
async def get_financial_impact(
    time_range: TimeRange = Query(TimeRange.YEAR),
    current_user: dict = Depends(get_current_user)
):
    """Get financial impact analysis"""
    
    if current_user.get("role") not in ["manager", "project_chief"]:
        raise HTTPException(status_code=403, detail="Executive access required")
    
    return {
        "period": time_range,
        "total_cost_savings": 987654,
        "roi": 245,
        "payback_period_months": 8.5,
        "breakdown": {
            "prevented_rework": 456000,
            "reduced_scrap": 234000,
            "labor_savings": 198000,
            "compliance_savings": 99654
        },
        "projection": {
            "next_quarter": 312000,
            "next_year": 1245000
        },
        "vs_manual_inspection": {
            "cost_reduction": 67.5,
            "time_savings": 82.3,
            "accuracy_improvement": 94.8
        }
    }


@router.get("/compliance-status")
async def get_compliance_status(
    current_user: dict = Depends(get_current_user)
):
    """Get compliance certification status"""
    
    if current_user.get("role") not in ["manager", "project_chief"]:
        raise HTTPException(status_code=403, detail="Executive access required")
    
    return {
        "overall_score": 94.5,
        "certifications": [
            {
                "name": "ISO 9001",
                "status": "certified",
                "expiry": "2025-12-31",
                "compliance_score": 98.5,
                "last_audit": "2024-01-15"
            },
            {
                "name": "AWS D1.1",
                "status": "certified",
                "expiry": "2025-06-30",
                "compliance_score": 96.2,
                "last_audit": "2023-12-01"
            },
            {
                "name": "ASME Section V",
                "status": "in_progress",
                "expiry": None,
                "compliance_score": 87.5,
                "last_audit": "2024-01-20"
            }
        ],
        "audit_trail": {
            "total_records": 15678,
            "last_7_days": 234,
            "compliance_rate": 99.8
        }
    }


@router.get("/export/presentation")
async def export_executive_presentation(
    time_range: TimeRange = Query(TimeRange.MONTH),
    format: str = Query("pdf", regex="^(pdf|pptx)$"),
    current_user: dict = Depends(get_current_user)
):
    """Export executive dashboard to PDF or PowerPoint"""
    
    if current_user.get("role") not in ["manager", "project_chief"]:
        raise HTTPException(status_code=403, detail="Executive access required")
    
    # In production, generate PDF or PPTX with reportlab or python-pptx
    
    return {
        "success": True,
        "format": format,
        "download_url": f"/api/executive/download/executive_report_{datetime.now().strftime('%Y%m%d')}.{format}",
        "generated_at": datetime.now().isoformat()
    }
