"""
BI Connectors API Routes

Endpoints for:
- BI platform integration
- Data export
- Dashboard creation
- Report generation
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

from integrations.bi_connectors import (
    bi_connector_factory,
    bi_model_generator,
    bi_templates,
    BIPlatform,
    DataRefreshMode
)


router = APIRouter(prefix="/api/bi", tags=["bi-connectors"])


# Request/Response Models

class TableauConfigRequest(BaseModel):
    server_url: str
    site_id: str
    username: str
    password: str
    project_name: str = "RadiKal XAI"


class PowerBIConfigRequest(BaseModel):
    workspace_id: str
    client_id: str
    client_secret: str
    tenant_id: str
    dataset_name: str = "RadiKal Quality Control"


class LookerConfigRequest(BaseModel):
    base_url: str
    client_id: str
    client_secret: str
    connection_name: str = "radikal_db"


class DashboardRequest(BaseModel):
    platform: str
    dashboard_name: str
    data_model_id: str
    template: Optional[str] = None  # "executive", "quality", "defects"


class DataExportRequest(BaseModel):
    format: str  # "csv", "json", "parquet", "hyper"
    start_date: datetime
    end_date: datetime
    filters: Optional[Dict[str, Any]] = None


# Tableau Endpoints

@router.post("/tableau/configure")
async def configure_tableau(request: TableauConfigRequest):
    """Configure Tableau connection"""
    try:
        connector = bi_connector_factory.get_connector(BIPlatform.TABLEAU)
        
        # Authenticate
        token = connector.authenticate(
            server_url=request.server_url,
            site_id=request.site_id,
            username=request.username,
            password=request.password
        )
        
        return {
            "status": "success",
            "message": "Tableau configured successfully",
            "expires_at": token.get("expires_at")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tableau/publish-datasource")
async def publish_tableau_datasource(
    datasource_name: str,
    project_name: str = "RadiKal XAI"
):
    """Publish datasource to Tableau"""
    try:
        connector = bi_connector_factory.get_connector(BIPlatform.TABLEAU)
        
        # Generate star schema
        star_schema = bi_model_generator.generate_star_schema()
        
        # Publish
        datasource_id = connector.publish_datasource(
            datasource_name=datasource_name,
            project_name=project_name,
            data=star_schema
        )
        
        return {
            "status": "success",
            "datasource_id": datasource_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tableau/create-dashboard")
async def create_tableau_dashboard(request: DashboardRequest):
    """Create Tableau dashboard"""
    try:
        connector = bi_connector_factory.get_connector(BIPlatform.TABLEAU)
        
        # Get template if specified
        dashboard_config = None
        if request.template == "executive":
            dashboard_config = bi_templates.get_executive_dashboard_template()
        
        # Create dashboard
        dashboard_id = connector.create_dashboard(
            dashboard_name=request.dashboard_name,
            datasource_id=request.data_model_id,
            dashboard_config=dashboard_config
        )
        
        # Get embed URL
        embed_url = connector.get_dashboard_url(dashboard_id, embed=True)
        
        return {
            "status": "success",
            "dashboard_id": dashboard_id,
            "embed_url": embed_url
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Power BI Endpoints

@router.post("/powerbi/configure")
async def configure_powerbi(request: PowerBIConfigRequest):
    """Configure Power BI connection"""
    try:
        connector = bi_connector_factory.get_connector(BIPlatform.POWER_BI)
        
        # Authenticate
        token = connector.authenticate(
            client_id=request.client_id,
            client_secret=request.client_secret,
            tenant_id=request.tenant_id
        )
        
        return {
            "status": "success",
            "message": "Power BI configured successfully",
            "access_token": token.get("access_token")[:20] + "..."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/powerbi/push-dataset")
async def push_powerbi_dataset(
    workspace_id: str,
    dataset_name: str
):
    """Push dataset to Power BI"""
    try:
        connector = bi_connector_factory.get_connector(BIPlatform.POWER_BI)
        
        # Generate star schema
        star_schema = bi_model_generator.generate_star_schema()
        
        # Push dataset
        dataset_id = connector.push_dataset(
            workspace_id=workspace_id,
            dataset_name=dataset_name,
            data=star_schema
        )
        
        return {
            "status": "success",
            "dataset_id": dataset_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/powerbi/create-report")
async def create_powerbi_report(
    workspace_id: str,
    report_name: str,
    dataset_id: str
):
    """Create Power BI report"""
    try:
        connector = bi_connector_factory.get_connector(BIPlatform.POWER_BI)
        
        # Get template
        dashboard_config = bi_templates.get_executive_dashboard_template()
        
        # Create report
        report_id = connector.create_report(
            workspace_id=workspace_id,
            report_name=report_name,
            dataset_id=dataset_id,
            report_config=dashboard_config
        )
        
        # Get embed token
        embed_token = connector.get_embed_token(workspace_id, report_id)
        
        return {
            "status": "success",
            "report_id": report_id,
            "embed_token": embed_token
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Looker Endpoints

@router.post("/looker/configure")
async def configure_looker(request: LookerConfigRequest):
    """Configure Looker connection"""
    try:
        connector = bi_connector_factory.get_connector(BIPlatform.LOOKER)
        
        # Authenticate
        token = connector.authenticate(
            base_url=request.base_url,
            client_id=request.client_id,
            client_secret=request.client_secret
        )
        
        return {
            "status": "success",
            "message": "Looker configured successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/looker/create-connection")
async def create_looker_connection(
    connection_name: str,
    database: str,
    host: str,
    port: int,
    username: str,
    password: str
):
    """Create Looker database connection"""
    try:
        connector = bi_connector_factory.get_connector(BIPlatform.LOOKER)
        
        connection_id = connector.create_connection(
            connection_name=connection_name,
            database=database,
            host=host,
            port=port,
            username=username,
            password=password
        )
        
        return {
            "status": "success",
            "connection_id": connection_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/looker/create-model")
async def create_looker_model(
    project_name: str,
    model_name: str,
    connection_name: str
):
    """Create Looker LookML model"""
    try:
        connector = bi_connector_factory.get_connector(BIPlatform.LOOKER)
        
        # Generate star schema
        star_schema = bi_model_generator.generate_star_schema()
        
        model_id = connector.create_lookml_model(
            project_name=project_name,
            model_name=model_name,
            connection_name=connection_name,
            schema=star_schema
        )
        
        return {
            "status": "success",
            "model_id": model_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/looker/create-dashboard")
async def create_looker_dashboard(
    dashboard_title: str,
    model_name: str
):
    """Create Looker dashboard"""
    try:
        connector = bi_connector_factory.get_connector(BIPlatform.LOOKER)
        
        # Get template
        dashboard_config = bi_templates.get_executive_dashboard_template()
        
        dashboard_id = connector.create_dashboard(
            dashboard_title=dashboard_title,
            model_name=model_name,
            dashboard_config=dashboard_config
        )
        
        return {
            "status": "success",
            "dashboard_id": dashboard_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Generic Endpoints

@router.post("/export")
async def export_data(request: DataExportRequest):
    """Export data in various formats"""
    try:
        # Generate star schema
        star_schema = bi_model_generator.generate_star_schema()
        
        # Apply filters
        # In production, query database with filters
        
        return {
            "status": "success",
            "format": request.format,
            "records": len(star_schema.get("fact_table", [])),
            "export_url": f"/downloads/export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{request.format}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/star-schema")
async def get_star_schema():
    """Get star schema data model"""
    try:
        schema = bi_model_generator.generate_star_schema()
        
        return {
            "status": "success",
            "schema": schema
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/executive-dashboard")
async def get_executive_dashboard_template():
    """Get executive dashboard template"""
    try:
        template = bi_templates.get_executive_dashboard_template()
        
        return {
            "status": "success",
            "template": template
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
