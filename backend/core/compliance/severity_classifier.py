"""
Severity Classification and Compliance Module

Classifies defect severity based on:
- Defect type and dimensions
- Welding standards (AWS, ASME, ISO)
- Location and criticality
- Acceptance criteria
"""

from typing import Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


class WeldingStandard(str, Enum):
    AWS_D1_1 = "AWS D1.1"
    ASME_BPVC = "ASME BPVC"
    ISO_5817_B = "ISO 5817-B"
    ISO_5817_C = "ISO 5817-C"
    ISO_5817_D = "ISO 5817-D"
    API_1104 = "API 1104"


class SeverityLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    ACCEPTABLE = "ACCEPTABLE"


class ComplianceStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class SeverityClassifier:
    """
    Classify defect severity based on welding standards.
    """
    
    # Severity rules by defect type
    DEFECT_RULES = {
        'CR': {  # Cracks
            'base_severity': SeverityLevel.CRITICAL,
            'AWS_D1_1': {
                'max_length_mm': 0,  # No cracks permitted
                'compliance': ComplianceStatus.FAIL,
            },
            'ISO_5817_B': {
                'max_length_mm': 0,
                'compliance': ComplianceStatus.FAIL,
            },
            'description': 'Cracks are linear discontinuities that compromise weld integrity',
            'action': 'REJECT - Repair required before use',
        },
        'LP': {  # Lack of Penetration
            'base_severity': SeverityLevel.CRITICAL,
            'AWS_D1_1': {
                'max_depth_mm': 1.0,
                'max_length_mm': 25,
                'compliance_threshold': 'Review required',
            },
            'ISO_5817_B': {
                'max_depth_mm': 0.5,
                'max_length_mm': 20,
            },
            'description': 'Incomplete fusion at weld root reduces joint strength',
            'action': 'REJECT - Verify penetration depth and repair if exceeded',
        },
        'PO': {  # Porosity
            'base_severity': SeverityLevel.MEDIUM,
            'AWS_D1_1': {
                'max_diameter_mm': 3.0,
                'max_density_percent': 3.0,  # Max 3% of weld area
                'max_count_per_inch': 12,
            },
            'ISO_5817_B': {
                'max_diameter_mm': 2.0,
                'max_density_percent': 2.0,
            },
            'description': 'Gas pockets in weld metal - assess size and distribution',
            'action': 'REVIEW - Accept if within tolerance, repair if excessive',
        },
        'ND': {  # No Defect
            'base_severity': SeverityLevel.ACCEPTABLE,
            'description': 'Weld meets quality standards',
            'action': 'ACCEPT - Proceed to next inspection stage',
        },
    }
    
    def __init__(self, standard: WeldingStandard = WeldingStandard.AWS_D1_1):
        """
        Initialize classifier with welding standard.
        
        Args:
            standard: Welding code to use for compliance checking
        """
        self.standard = standard
        logger.info(f"SeverityClassifier initialized with standard: {standard}")
    
    def classify_severity(
        self,
        defect_type: str,
        confidence: float,
        region_data: Optional[Dict[str, Any]] = None,
        material_thickness: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Classify defect severity based on type and measurements.
        
        Args:
            defect_type: LP, PO, CR, ND
            confidence: Model confidence (0-1)
            region_data: Defect dimensions (x, y, width, height, area)
            material_thickness: Base material thickness in mm
        
        Returns:
            Dict with severity, compliance status, and recommendations
        """
        try:
            if defect_type not in self.DEFECT_RULES:
                logger.warning(f"Unknown defect type: {defect_type}")
                return self._default_classification()
            
            rules = self.DEFECT_RULES[defect_type]
            base_severity = rules['base_severity']
            
            # Start with base severity
            final_severity = base_severity
            compliance = ComplianceStatus.PASS
            reasons = []
            
            # Adjust based on confidence
            if confidence < 0.7:
                reasons.append(f"Low confidence ({confidence*100:.1f}%) - manual review recommended")
                compliance = ComplianceStatus.REVIEW_REQUIRED
            
            # Check against standard rules
            if self.standard.value in rules:
                standard_rules = rules[self.standard.value]
                compliance_check = self._check_compliance(
                    defect_type,
                    region_data,
                    standard_rules,
                    material_thickness
                )
                
                if not compliance_check['compliant']:
                    compliance = ComplianceStatus.FAIL
                    reasons.extend(compliance_check['violations'])
                    
                    # Escalate severity if standards violated
                    if base_severity == SeverityLevel.MEDIUM:
                        final_severity = SeverityLevel.HIGH
                    elif base_severity == SeverityLevel.LOW:
                        final_severity = SeverityLevel.MEDIUM
            
            # Build response
            result = {
                'severity': final_severity,
                'compliance_status': compliance,
                'standard': self.standard.value,
                'description': rules['description'],
                'recommended_action': rules['action'],
                'reasons': reasons,
                'pass_fail': compliance == ComplianceStatus.PASS,
            }
            
            # Add repair recommendations if failed
            if compliance == ComplianceStatus.FAIL:
                result['repair_recommendation'] = self._get_repair_recommendation(defect_type)
            
            return result
            
        except Exception as e:
            logger.error(f"Severity classification failed: {e}", exc_info=True)
            return self._default_classification()
    
    def _check_compliance(
        self,
        defect_type: str,
        region_data: Optional[Dict],
        standard_rules: Dict,
        material_thickness: Optional[float],
    ) -> Dict[str, Any]:
        """Check if defect meets standard requirements."""
        violations = []
        compliant = True
        
        if not region_data:
            return {'compliant': True, 'violations': []}
        
        # Extract dimensions (assuming pixels, need calibration for mm)
        # For MVP, use relative measurements
        defect_width = region_data.get('width', 0)
        defect_height = region_data.get('height', 0)
        defect_area = region_data.get('area', defect_width * defect_height)
        
        # Check maximum dimensions
        if 'max_length_mm' in standard_rules:
            max_allowed = standard_rules['max_length_mm']
            if max_allowed == 0:
                compliant = False
                violations.append(f"{defect_type} not permitted per {self.standard.value}")
            # Note: Need calibration to convert pixels to mm
        
        if 'max_diameter_mm' in standard_rules:
            max_dia = standard_rules['max_diameter_mm']
            # Check if defect size exceeds limit
            # (simplified - needs proper measurement)
        
        if 'max_density_percent' in standard_rules:
            # Would need to calculate density across weld area
            # Placeholder for now
            pass
        
        return {
            'compliant': compliant,
            'violations': violations,
        }
    
    def _get_repair_recommendation(self, defect_type: str) -> str:
        """Get repair recommendation based on defect type."""
        recommendations = {
            'CR': 'Grind out crack completely, V-groove, and re-weld with approved procedure',
            'LP': 'Back-gouge to remove incomplete penetration, then re-weld root pass',
            'PO': 'If excessive, grind out porous area and fill with sound weld metal',
        }
        return recommendations.get(defect_type, 'Consult welding engineer for repair procedure')
    
    def _default_classification(self) -> Dict[str, Any]:
        """Return default classification when errors occur."""
        return {
            'severity': SeverityLevel.MEDIUM,
            'compliance_status': ComplianceStatus.REVIEW_REQUIRED,
            'standard': self.standard.value,
            'description': 'Unable to classify - manual review required',
            'recommended_action': 'Submit for manual inspection',
            'reasons': ['Classification error occurred'],
            'pass_fail': False,
        }
    
    def get_acceptance_criteria(self, defect_type: str) -> Dict[str, Any]:
        """
        Get acceptance criteria for a defect type under current standard.
        
        Returns human-readable criteria for operators.
        """
        if defect_type not in self.DEFECT_RULES:
            return {'error': 'Unknown defect type'}
        
        rules = self.DEFECT_RULES[defect_type]
        criteria = {
            'defect_type': defect_type,
            'standard': self.standard.value,
            'base_severity': rules['base_severity'],
            'description': rules['description'],
            'action': rules['action'],
        }
        
        if self.standard.value in rules:
            criteria['standard_limits'] = rules[self.standard.value]
        
        return criteria


class ComplianceChecker:
    """
    Check compliance against multiple welding standards.
    """
    
    def __init__(self):
        self.classifiers = {
            standard: SeverityClassifier(standard)
            for standard in WeldingStandard
        }
    
    def check_multi_standard(
        self,
        defect_type: str,
        confidence: float,
        region_data: Optional[Dict] = None,
        standards: Optional[list] = None,
    ) -> Dict[str, Any]:
        """
        Check defect against multiple standards simultaneously.
        
        Useful when work must meet multiple codes.
        """
        if standards is None:
            standards = [WeldingStandard.AWS_D1_1, WeldingStandard.ISO_5817_B]
        
        results = {}
        for standard in standards:
            classifier = self.classifiers[standard]
            results[standard.value] = classifier.classify_severity(
                defect_type,
                confidence,
                region_data
            )
        
        # Determine most restrictive result
        most_restrictive = self._get_most_restrictive(results)
        
        return {
            'individual_results': results,
            'most_restrictive_standard': most_restrictive['standard'],
            'final_compliance': most_restrictive['compliance'],
            'final_severity': most_restrictive['severity'],
        }
    
    def _get_most_restrictive(self, results: Dict) -> Dict:
        """Find the most restrictive standard result."""
        severity_order = [
            SeverityLevel.CRITICAL,
            SeverityLevel.HIGH,
            SeverityLevel.MEDIUM,
            SeverityLevel.LOW,
            SeverityLevel.ACCEPTABLE,
        ]
        
        most_restrictive = {
            'standard': None,
            'compliance': ComplianceStatus.PASS,
            'severity': SeverityLevel.ACCEPTABLE,
        }
        
        for standard, result in results.items():
            severity_idx = severity_order.index(result['severity'])
            current_idx = severity_order.index(most_restrictive['severity'])
            
            if severity_idx < current_idx:  # More severe
                most_restrictive = {
                    'standard': standard,
                    'compliance': result['compliance_status'],
                    'severity': result['severity'],
                }
        
        return most_restrictive
