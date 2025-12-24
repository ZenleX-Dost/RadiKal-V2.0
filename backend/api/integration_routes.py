"""
ERP/MES Integration API Routes

Configure and manage enterprise system integrations
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from integrations.erp_mes_connectors import (
    integration_manager,
    ERPSystem,
    MESSystem,
    WorkOrder,
    QualityResult
)
from core.auth import get_current_user

router = APIRouter(prefix="/api/integrations", tags=["integrations"])


# Request Models

class IntegrationConfig(BaseModel):
    """Integration configuration"""
    system_type: str  # ERPSystem or MESSystem
    system_name: str
    base_url: str
    authentication_type: str  # "api_key", "oauth", "basic", "certificate"
    api_key: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    certificate_path: Optional[str] = None
    enabled: bool = True
    sync_interval_minutes: int = 15
    auto_sync: bool = True


class WorkOrderFilter(BaseModel):
    """Filters for pulling work orders"""
    status: Optional[List[str]] = None
    priority: Optional[List[str]] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    part_number: Optional[str] = None


# Configuration Endpoints

@router.post("/config")
async def configure_integration(
    config: IntegrationConfig,
    current_user: dict = Depends(get_current_user)
):
    """Configure ERP/MES integration for tenant (admin only)"""
    
    if current_user.get("role") != "manager":
        raise HTTPException(status_code=403, detail="Only managers can configure integrations")
    
    tenant_id = current_user.get("tenant_id")
    
    try:
        # Register connector
        connector = integration_manager.register_connector(
            tenant_id=tenant_id,
            system_type=config.system_type,
            config=config.dict()
        )
        
        # Test connection
        connection_ok = await connector.test_connection()
        
        if not connection_ok:
            raise HTTPException(status_code=400, detail="Failed to connect to ERP/MES system")
        
        return {
            "success": True,
            "message": f"Integration with {config.system_name} configured successfully",
            "system_type": config.system_type,
            "enabled": config.enabled,
            "auto_sync": config.auto_sync
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Configuration failed: {str(e)}")


@router.get("/config")
async def get_integration_config(
    current_user: dict = Depends(get_current_user)
):
    """Get current integration configuration"""
    
    tenant_id = current_user.get("tenant_id")
    connector = integration_manager.get_connector(tenant_id)
    
    if not connector:
        return {
            "configured": False,
            "system_type": None
        }
    
    return {
        "configured": True,
        "system_name": connector.system_name,
        "base_url": connector.base_url,
        "enabled": True
    }


@router.post("/test-connection")
async def test_integration_connection(
    current_user: dict = Depends(get_current_user)
):
    """Test connection to configured ERP/MES system"""
    
    tenant_id = current_user.get("tenant_id")
    connector = integration_manager.get_connector(tenant_id)
    
    if not connector:
        raise HTTPException(status_code=404, detail="No integration configured")
    
    try:
        connection_ok = await connector.test_connection()
        
        return {
            "success": connection_ok,
            "message": "Connection successful" if connection_ok else "Connection failed",
            "system": connector.system_name,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            "success": False,
            "message": f"Connection test failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }


# Work Order Endpoints

@router.post("/work-orders/sync")
async def sync_work_orders(
    filters: Optional[WorkOrderFilter] = None,
    background_tasks: BackgroundTasks = None,
    current_user: dict = Depends(get_current_user)
):
    """Manually trigger work order synchronization"""
    
    tenant_id = current_user.get("tenant_id")
    
    # Run sync in background
    if background_tasks:
        background_tasks.add_task(integration_manager.sync_work_orders, tenant_id)
        
        return {
            "success": True,
            "message": "Work order sync initiated",
            "status": "processing",
            "timestamp": datetime.now().isoformat()
        }
    
    # Run sync immediately
    result = await integration_manager.sync_work_orders(tenant_id)
    return result


@router.get("/work-orders")
async def get_work_orders(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """Get synchronized work orders from ERP/MES"""
    
    tenant_id = current_user.get("tenant_id")
    connector = integration_manager.get_connector(tenant_id)
    
    if not connector:
        raise HTTPException(status_code=404, detail="No integration configured")
    
    try:
        filters = {}
        if status:
            filters["status"] = status
        if priority:
            filters["priority"] = priority
        
        work_orders = await connector.pull_work_orders(filters)
        
        # Limit results
        work_orders = work_orders[:limit]
        
        return {
            "success": True,
            "count": len(work_orders),
            "work_orders": [wo.dict() for wo in work_orders]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch work orders: {str(e)}")


@router.get("/work-orders/{order_id}")
async def get_work_order_details(
    order_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get detailed information for specific work order"""
    
    tenant_id = current_user.get("tenant_id")
    connector = integration_manager.get_connector(tenant_id)
    
    if not connector:
        raise HTTPException(status_code=404, detail="No integration configured")
    
    # In production, query from database where work orders are cached
    # For now, pull all and filter
    work_orders = await connector.pull_work_orders()
    
    for wo in work_orders:
        if wo.order_id == order_id:
            return {
                "success": True,
                "work_order": wo.dict()
            }
    
    raise HTTPException(status_code=404, detail="Work order not found")


@router.patch("/work-orders/{order_id}/status")
async def update_work_order_status(
    order_id: str,
    status: str,
    current_user: dict = Depends(get_current_user)
):
    """Update work order status in ERP/MES"""
    
    tenant_id = current_user.get("tenant_id")
    connector = integration_manager.get_connector(tenant_id)
    
    if not connector:
        raise HTTPException(status_code=404, detail="No integration configured")
    
    try:
        success = await connector.update_work_order_status(order_id, status)
        
        return {
            "success": success,
            "message": f"Work order {order_id} status updated to {status}",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update status: {str(e)}")


# Quality Results Push

@router.post("/quality-results/push")
async def push_quality_results(
    inspection_ids: List[str],
    background_tasks: BackgroundTasks = None,
    current_user: dict = Depends(get_current_user)
):
    """Push quality inspection results to ERP/MES"""
    
    tenant_id = current_user.get("tenant_id")
    
    # In production, fetch inspection results from database
    # Mock data for now
    results = []
    for insp_id in inspection_ids:
        result = QualityResult(
            inspection_id=insp_id,
            work_order_id="WO001",
            part_number="WELD-PIPE-100",
            inspection_date=datetime.now(),
            inspector=current_user.get("email"),
            result="pass",
            defects_found=[],
            images=[],
            xai_confidence=0.98,
            xai_method="gradcam",
            compliance=True
        )
        results.append(result)
    
    # Push to ERP/MES
    if background_tasks:
        background_tasks.add_task(integration_manager.push_results, tenant_id, results)
        
        return {
            "success": True,
            "message": "Quality results push initiated",
            "count": len(results),
            "status": "processing"
        }
    
    response = await integration_manager.push_results(tenant_id, results)
    return response


@router.post("/quality-results/auto-push")
async def configure_auto_push(
    enabled: bool,
    push_on_complete: bool = True,
    push_on_defect: bool = True,
    current_user: dict = Depends(get_current_user)
):
    """Configure automatic push of quality results to ERP/MES"""
    
    if current_user.get("role") != "manager":
        raise HTTPException(status_code=403, detail="Only managers can configure auto-push")
    
    # Store configuration in database
    # In production, save tenant-specific settings
    
    return {
        "success": True,
        "message": "Auto-push configuration updated",
        "enabled": enabled,
        "push_on_complete": push_on_complete,
        "push_on_defect": push_on_defect
    }


# Material Tracking

@router.get("/materials/{material_id}")
async def get_material_tracking(
    material_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get material tracking information from ERP/MES"""
    
    tenant_id = current_user.get("tenant_id")
    connector = integration_manager.get_connector(tenant_id)
    
    if not connector:
        raise HTTPException(status_code=404, detail="No integration configured")
    
    try:
        material = await connector.get_material_info(material_id)
        
        if not material:
            raise HTTPException(status_code=404, detail="Material not found")
        
        return {
            "success": True,
            "material": material.dict()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch material: {str(e)}")


# Webhooks

@router.post("/webhooks/erp-event")
async def handle_erp_webhook(
    event: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """Handle incoming webhook from ERP/MES system"""
    
    # Process different event types
    event_type = event.get("type")
    
    if event_type == "work_order_created":
        # Handle new work order
        pass
    elif event_type == "work_order_updated":
        # Handle work order update
        pass
    elif event_type == "material_received":
        # Handle material receipt
        pass
    
    return {
        "success": True,
        "message": "Webhook processed",
        "event_type": event_type
    }


# Sync Status and History

@router.get("/sync-status")
async def get_sync_status(
    current_user: dict = Depends(get_current_user)
):
    """Get status of last synchronization"""
    
    # In production, query from sync_history table
    
    return {
        "last_sync": datetime.now().isoformat(),
        "status": "success",
        "work_orders_synced": 45,
        "quality_results_pushed": 23,
        "next_sync": datetime.now().isoformat(),
        "auto_sync_enabled": True
    }


@router.get("/sync-history")
async def get_sync_history(
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """Get synchronization history"""
    
    # In production, query from sync_history table
    
    return {
        "history": [
            {
                "timestamp": datetime.now().isoformat(),
                "type": "work_orders",
                "direction": "inbound",
                "status": "success",
                "records": 45
            },
            {
                "timestamp": datetime.now().isoformat(),
                "type": "quality_results",
                "direction": "outbound",
                "status": "success",
                "records": 23
            }
        ]
    }


# System Support

@router.get("/supported-systems")
async def get_supported_systems():
    """Get list of supported ERP/MES systems"""
    
    return {
        "erp_systems": [
            {"id": "sap_ecc", "name": "SAP ECC", "version": "6.0+", "status": "supported"},
            {"id": "sap_s4hana", "name": "SAP S/4HANA", "version": "1809+", "status": "supported"},
            {"id": "oracle_ebs", "name": "Oracle E-Business Suite", "version": "R12+", "status": "supported"},
            {"id": "oracle_cloud", "name": "Oracle Cloud ERP", "version": "Latest", "status": "supported"},
            {"id": "microsoft_dynamics", "name": "Microsoft Dynamics 365", "version": "Latest", "status": "beta"},
            {"id": "infor_ln", "name": "Infor LN", "version": "10.x+", "status": "beta"},
            {"id": "epicor", "name": "Epicor ERP", "version": "10.x+", "status": "planned"}
        ],
        "mes_systems": [
            {"id": "siemens_opcenter", "name": "Siemens Opcenter", "version": "Latest", "status": "supported"},
            {"id": "rockwell_factorytalk", "name": "Rockwell FactoryTalk", "version": "11.x+", "status": "supported"},
            {"id": "ge_proficy", "name": "GE Proficy", "version": "Latest", "status": "beta"},
            {"id": "dassault_apriso", "name": "Dassault APRISO", "version": "Latest", "status": "planned"},
            {"id": "aveva_mes", "name": "AVEVA MES", "version": "Latest", "status": "planned"}
        ]
    }
