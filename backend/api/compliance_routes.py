"""
Compliance Module - API Routes

Endpoints for regulatory compliance and certification.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import logging
import uuid

from db import get_db
from db.models import ComplianceCheck, Analysis
from core.compliance.severity_classifier import (
    SeverityClassifier,
    ComplianceChecker,
    WeldingStandard,
    ComplianceStatus,
)
from core.compliance.certificate_generator import ComplianceCertificateGenerator
# from api.middleware import get_current_user  # TODO: Enable authentication

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/xai-qc/compliance", tags=["Compliance"])


class ComplianceCheckRequest(BaseModel):
    defect_type: str
    confidence: float = 1.0
    region_data: Optional[dict] = None
    length_mm: Optional[float] = None
    width_mm: Optional[float] = None
    depth_mm: Optional[float] = None
    density_percent: Optional[float] = None
    location: Optional[str] = None
    material_type: Optional[str] = None
    material_thickness: Optional[float] = None
    standard: WeldingStandard = WeldingStandard.AWS_D1_1
    analysis_id: Optional[int] = None
    inspector_name: Optional[str] = None


class CertificateGenerationRequest(BaseModel):
    compliance_check_id: int
    inspector_name: Optional[str] = None


class ComplianceReportRequest(BaseModel):
    analysis_id: str
    standard: WeldingStandard
    inspector_signature: Optional[str] = None
    inspector_name: Optional[str] = None
    notes: Optional[str] = None


class ComplianceCertificate(BaseModel):
    certificate_id: str
    analysis_id: str
    standard: str
    compliance_status: str
    inspector_name: str
    inspector_signature: Optional[str]
    issue_date: datetime
    expiry_date: Optional[datetime]
    notes: Optional[str]


@router.post("/check")
async def check_compliance(
    request: ComplianceCheckRequest,
    db: Session = Depends(get_db),
):
    """
    Check if a defect meets compliance standards and store the result.
    
    Returns severity classification and acceptance criteria.
    """
    try:
        classifier = SeverityClassifier(request.standard)
        
        # Build region_data from individual measurements if not provided
        if not request.region_data and (request.length_mm or request.width_mm or request.depth_mm):
            request.region_data = {
                "length_mm": request.length_mm,
                "width_mm": request.width_mm,
                "depth_mm": request.depth_mm,
                "density_percent": request.density_percent,
                "location": request.location,
            }
        
        result = classifier.classify_severity(
            defect_type=request.defect_type,
            confidence=request.confidence,
            region_data=request.region_data,
            material_thickness=request.material_thickness,
        )
        
        # Store compliance check in database
        compliance_check = ComplianceCheck(
            analysis_id=request.analysis_id,
            inspector_name=request.inspector_name,
            defect_type=request.defect_type,
            length_mm=request.length_mm,
            width_mm=request.width_mm,
            depth_mm=request.depth_mm,
            density_percent=request.density_percent,
            location=request.location,
            material_type=request.material_type,
            material_thickness=request.material_thickness,
            standard_code=request.standard.value,
            standard_name=f"{request.standard.value} Standard",
            severity=result.get("severity", "unknown"),
            compliance_status=result.get("compliance_status", "unknown"),
            pass_fail=result.get("pass_fail", False),
            recommended_action=result.get("recommended_action", ""),
            reasons=result.get("reasons", []),
        )
        
        db.add(compliance_check)
        db.commit()
        db.refresh(compliance_check)
        
        # Add check_id to result
        result["check_id"] = compliance_check.id
        
        logger.info(f"Compliance check completed and stored: ID {compliance_check.id}")
        
        return result
        
    except Exception as e:
        logger.error(f"Compliance check failed: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check-multi")
async def check_multiple_standards(
    defect_type: str,
    confidence: float,
    region_data: Optional[dict] = None,
    standards: Optional[List[WeldingStandard]] = None,
):
    """
    Check compliance against multiple welding standards simultaneously.
    
    Returns most restrictive result.
    """
    try:
        checker = ComplianceChecker()
        
        result = checker.check_multi_standard(
            defect_type=defect_type,
            confidence=confidence,
            region_data=region_data,
            standards=standards,
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Multi-standard check failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/standards")
async def list_standards():
    """
    List all available welding standards.
    
    Returns standards library with descriptions.
    """
    return {
        "standards": [
            {
                "code": "AWS D1.1",
                "name": "AWS D1.1 - Structural Welding Code - Steel",
                "organization": "American Welding Society",
                "year": "2020",
                "application": "Structural steel welding",
            },
            {
                "code": "ASME BPVC",
                "name": "ASME Boiler and Pressure Vessel Code",
                "organization": "American Society of Mechanical Engineers",
                "year": "2021",
                "application": "Pressure vessels and boilers",
            },
            {
                "code": "ISO 5817-B",
                "name": "ISO 5817 Quality Level B",
                "organization": "International Organization for Standardization",
                "year": "2014",
                "application": "High quality welds",
            },
            {
                "code": "ISO 5817-C",
                "name": "ISO 5817 Quality Level C",
                "organization": "International Organization for Standardization",
                "year": "2014",
                "application": "Standard quality welds",
            },
            {
                "code": "ISO 5817-D",
                "name": "ISO 5817 Quality Level D",
                "organization": "International Organization for Standardization",
                "year": "2014",
                "application": "Moderate quality welds",
            },
            {
                "code": "API 1104",
                "name": "API 1104 - Welding of Pipelines and Related Facilities",
                "organization": "American Petroleum Institute",
                "year": "2021",
                "application": "Pipeline welding",
            },
        ]
    }


@router.get("/acceptance-criteria/{defect_type}")
async def get_acceptance_criteria(
    defect_type: str,
    standard: WeldingStandard = WeldingStandard.AWS_D1_1,
):
    """
    Get detailed acceptance criteria for a defect type.
    
    Returns human-readable limits and requirements.
    """
    try:
        classifier = SeverityClassifier(standard)
        criteria = classifier.get_acceptance_criteria(defect_type)
        
        return criteria
        
    except Exception as e:
        logger.error(f"Failed to get criteria: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-certificate")
async def generate_compliance_certificate(
    request: CertificateGenerationRequest,
    db: Session = Depends(get_db),
):
    """
    Generate PDF compliance certificate for a completed compliance check.
    
    Creates ISO 9001 compliant documentation.
    """
    try:
        # Fetch the compliance check
        check = db.query(ComplianceCheck).filter(
            ComplianceCheck.id == request.compliance_check_id
        ).first()
        
        if not check:
            raise HTTPException(status_code=404, detail="Compliance check not found")
        
        # Generate unique certificate ID
        certificate_id = f"CERT-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        
        # Initialize certificate generator
        generator = ComplianceCertificateGenerator()
        
        # Prepare defect measurements
        defect_measurements = {
            "length_mm": check.length_mm,
            "width_mm": check.width_mm,
            "depth_mm": check.depth_mm,
            "density_percent": check.density_percent,
            "location": check.location,
        }
        
        # Generate PDF
        pdf_path = generator.generate_certificate(
            certificate_id=certificate_id,
            analysis_id=str(check.analysis_id) if check.analysis_id else None,
            defect_type=check.defect_type,
            defect_measurements=defect_measurements,
            material_type=check.material_type,
            material_thickness=check.material_thickness,
            standard_code=check.standard_code,
            standard_name=check.standard_name or f"{check.standard_code} Standard",
            compliance_status=check.compliance_status,
            severity=check.severity,
            pass_fail=check.pass_fail,
            recommended_action=check.recommended_action or "No action specified",
            reasons=check.reasons or [],
            inspector_name=request.inspector_name or check.inspector_name or "Unknown Inspector",
        )
        
        # Update check with certificate info
        check.certificate_id = certificate_id
        check.certificate_path = pdf_path
        db.commit()
        
        logger.info(f"Generated compliance certificate: {certificate_id}")
        
        return {
            "certificate_id": certificate_id,
            "check_id": check.id,
            "pdf_path": pdf_path,
            "download_url": f"/api/xai-qc/compliance/download-certificate/{certificate_id}",
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Certificate generation failed: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download-certificate/{certificate_id}")
async def download_certificate(
    certificate_id: str,
    db: Session = Depends(get_db),
):
    """
    Download a generated compliance certificate PDF.
    """
    try:
        # Find the compliance check with this certificate
        check = db.query(ComplianceCheck).filter(
            ComplianceCheck.certificate_id == certificate_id
        ).first()
        
        if not check or not check.certificate_path:
            raise HTTPException(status_code=404, detail="Certificate not found")
        
        # Return PDF file
        return FileResponse(
            path=check.certificate_path,
            media_type="application/pdf",
            filename=f"{certificate_id}.pdf",
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Certificate download failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_compliance_history(
    limit: int = 50,
    skip: int = 0,
    db: Session = Depends(get_db),
):
    """
    Get compliance check history (audit trail).
    
    Returns recent compliance checks with pagination.
    """
    try:
        total = db.query(ComplianceCheck).count()
        
        checks = db.query(ComplianceCheck).order_by(
            ComplianceCheck.created_at.desc()
        ).offset(skip).limit(limit).all()
        
        return {
            "total": total,
            "checks": [
                {
                    "id": check.id,
                    "analysis_id": check.analysis_id,
                    "inspector_name": check.inspector_name,
                    "defect_type": check.defect_type,
                    "material_type": check.material_type,
                    "material_thickness": check.material_thickness,
                    "standard_code": check.standard_code,
                    "severity": check.severity,
                    "compliance_status": check.compliance_status,
                    "pass_fail": check.pass_fail,
                    "certificate_id": check.certificate_id,
                    "created_at": check.created_at.isoformat(),
                }
                for check in checks
            ],
        }
        
    except Exception as e:
        logger.error(f"Failed to get compliance history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
