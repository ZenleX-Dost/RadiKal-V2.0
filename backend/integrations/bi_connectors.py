"""
Business Intelligence Connectors for RadiKal

Integration with BI platforms:
- Tableau REST API
- Power BI REST API / Embedded
- Looker API
- Generic ODBC/JDBC connectors
- Custom data models for BI tools
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from datetime import datetime
from enum import Enum
import json
import secrets


class BIPlatform(str, Enum):
    """Supported BI platforms"""
    TABLEAU = "tableau"
    POWER_BI = "power_bi"
    LOOKER = "looker"
    QLIK = "qlik"
    METABASE = "metabase"
    GENERIC_ODBC = "generic_odbc"
    GENERIC_JDBC = "generic_jdbc"


class DataRefreshMode(str, Enum):
    """Data refresh modes"""
    REAL_TIME = "real_time"
    INCREMENTAL = "incremental"
    FULL_REFRESH = "full_refresh"
    SCHEDULED = "scheduled"


class ConnectionStatus(str, Enum):
    """Connection status"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    AUTHENTICATING = "authenticating"


# Data Models

class BIConnection(BaseModel):
    """BI platform connection"""
    connection_id: str
    platform: BIPlatform
    connection_name: str
    server_url: str
    site_id: Optional[str] = None
    project_id: Optional[str] = None
    workspace_id: Optional[str] = None
    api_key: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    status: ConnectionStatus = ConnectionStatus.DISCONNECTED
    last_sync: Optional[datetime] = None
    created_at: datetime = datetime.now()


class DataModel(BaseModel):
    """Data model for BI tools"""
    model_id: str
    model_name: str
    description: str
    tables: List[str]
    relationships: List[Dict[str, Any]]
    measures: List[Dict[str, Any]]
    dimensions: List[Dict[str, Any]]
    created_at: datetime = datetime.now()


class BIDashboard(BaseModel):
    """BI dashboard definition"""
    dashboard_id: str
    dashboard_name: str
    platform: BIPlatform
    description: str
    data_sources: List[str]
    visualizations: List[Dict[str, Any]]
    filters: List[Dict[str, Any]]
    refresh_schedule: Optional[str] = None
    public_url: Optional[str] = None


class DataExport(BaseModel):
    """Data export configuration"""
    export_id: str
    format: str  # "csv", "json", "parquet", "hyper"
    tables: List[str]
    filters: Dict[str, Any] = {}
    row_limit: Optional[int] = None
    include_metadata: bool = True


# Tableau Connector

class TableauConnector:
    """Tableau REST API connector"""
    
    def __init__(self, connection: BIConnection):
        self.connection = connection
        self.api_version = "3.19"
        
    async def authenticate(self) -> bool:
        """Authenticate with Tableau Server/Cloud"""
        # In production, use Tableau REST API
        # url = f"{self.connection.server_url}/api/{self.api_version}/auth/signin"
        # response = await httpx.post(url, json={
        #     "credentials": {
        #         "name": self.connection.username,
        #         "password": self.connection.password,
        #         "site": {"contentUrl": self.connection.site_id}
        #     }
        # })
        # self.connection.access_token = response.json()["credentials"]["token"]
        
        self.connection.status = ConnectionStatus.CONNECTED
        return True
    
    async def publish_datasource(
        self,
        datasource_name: str,
        data_export: DataExport
    ) -> Dict[str, Any]:
        """Publish data source to Tableau"""
        # In production, create .hyper file and publish via REST API
        # 1. Create Hyper extract
        # from tableauhyperapi import HyperProcess, Connection, TableDefinition
        # 2. Publish to Tableau Server
        # POST /api/{api_version}/sites/{site_id}/datasources
        
        return {
            "success": True,
            "datasource_id": f"ds_{secrets.token_hex(8)}",
            "datasource_name": datasource_name,
            "project_id": self.connection.project_id,
            "published_at": datetime.now().isoformat()
        }
    
    async def create_dashboard(
        self,
        dashboard_def: BIDashboard
    ) -> Dict[str, Any]:
        """Create dashboard in Tableau"""
        # In production, use Tableau REST API or Tableau Document API
        # POST /api/{api_version}/sites/{site_id}/workbooks
        
        return {
            "success": True,
            "dashboard_id": dashboard_def.dashboard_id,
            "dashboard_url": f"{self.connection.server_url}/views/{dashboard_def.dashboard_name}",
            "embed_code": f'<tableau-viz src="{self.connection.server_url}/views/{dashboard_def.dashboard_name}"></tableau-viz>'
        }
    
    async def refresh_datasource(self, datasource_id: str) -> bool:
        """Trigger datasource refresh"""
        # POST /api/{api_version}/sites/{site_id}/datasources/{datasource_id}/refresh
        return True
    
    async def get_dashboard_url(self, dashboard_id: str) -> str:
        """Get dashboard embed URL"""
        return f"{self.connection.server_url}/trusted/{self.connection.access_token}/views/{dashboard_id}"


# Power BI Connector

class PowerBIConnector:
    """Power BI REST API connector"""
    
    def __init__(self, connection: BIConnection):
        self.connection = connection
        self.api_url = "https://api.powerbi.com/v1.0/myorg"
        
    async def authenticate(self) -> bool:
        """Authenticate with Power BI using OAuth 2.0"""
        # In production, use Microsoft Identity Platform OAuth
        # from msal import ConfidentialClientApplication
        # app = ConfidentialClientApplication(
        #     client_id=client_id,
        #     client_credential=client_secret,
        #     authority=f"https://login.microsoftonline.com/{tenant_id}"
        # )
        # result = app.acquire_token_for_client(scopes=["https://analysis.windows.net/powerbi/api/.default"])
        # self.connection.access_token = result["access_token"]
        
        self.connection.status = ConnectionStatus.CONNECTED
        return True
    
    async def push_dataset(
        self,
        dataset_name: str,
        tables: List[Dict[str, Any]],
        mode: DataRefreshMode = DataRefreshMode.INCREMENTAL
    ) -> Dict[str, Any]:
        """Push dataset to Power BI"""
        # In production, use Power BI Push Datasets API
        # POST https://api.powerbi.com/v1.0/myorg/datasets
        
        dataset_def = {
            "name": dataset_name,
            "tables": tables,
            "defaultMode": mode.value
        }
        
        return {
            "success": True,
            "dataset_id": f"ds_{secrets.token_hex(8)}",
            "dataset_name": dataset_name,
            "web_url": f"https://app.powerbi.com/groups/{self.connection.workspace_id}/datasets"
        }
    
    async def create_report(
        self,
        report_name: str,
        dataset_id: str
    ) -> Dict[str, Any]:
        """Create Power BI report"""
        # POST https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/reports
        
        return {
            "success": True,
            "report_id": f"rpt_{secrets.token_hex(8)}",
            "report_name": report_name,
            "embed_url": f"https://app.powerbi.com/reportEmbed?reportId={report_name}",
            "web_url": f"https://app.powerbi.com/groups/{self.connection.workspace_id}/reports/{report_name}"
        }
    
    async def get_embed_token(self, report_id: str) -> Dict[str, str]:
        """Generate embed token for report"""
        # POST https://api.powerbi.com/v1.0/myorg/reports/{report_id}/GenerateToken
        
        return {
            "token": secrets.token_urlsafe(64),
            "token_id": secrets.token_hex(16),
            "expiration": (datetime.now() + timedelta(hours=1)).isoformat()
        }
    
    async def refresh_dataset(self, dataset_id: str) -> bool:
        """Trigger dataset refresh"""
        # POST https://api.powerbi.com/v1.0/myorg/datasets/{dataset_id}/refreshes
        return True


# Looker Connector

class LookerConnector:
    """Looker API connector"""
    
    def __init__(self, connection: BIConnection):
        self.connection = connection
        self.api_version = "4.0"
        
    async def authenticate(self) -> bool:
        """Authenticate with Looker API"""
        # In production, use Looker API authentication
        # POST {base_url}/login
        # response = await httpx.post(
        #     f"{self.connection.server_url}/api/{self.api_version}/login",
        #     data={
        #         "client_id": client_id,
        #         "client_secret": client_secret
        #     }
        # )
        # self.connection.access_token = response.json()["access_token"]
        
        self.connection.status = ConnectionStatus.CONNECTED
        return True
    
    async def create_connection(
        self,
        connection_name: str,
        database_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create database connection in Looker"""
        # POST /api/{api_version}/connections
        
        return {
            "success": True,
            "connection_name": connection_name,
            "dialect": database_config.get("dialect", "postgresql")
        }
    
    async def create_lookml_model(
        self,
        model_name: str,
        data_model: DataModel
    ) -> Dict[str, Any]:
        """Create LookML model"""
        # LookML is Looker's modeling language
        # In production, generate LookML files and push to git repo
        
        lookml = self._generate_lookml(model_name, data_model)
        
        return {
            "success": True,
            "model_name": model_name,
            "lookml": lookml
        }
    
    def _generate_lookml(self, model_name: str, data_model: DataModel) -> str:
        """Generate LookML code"""
        lookml = f"""connection: "radikal_db"

include: "*.view"

explore: inspections {{
  label: "Inspections"
  
  join: defects {{
    sql_on: ${{inspections.inspection_id}} = ${{defects.inspection_id}} ;;
    relationship: one_to_many
  }}
  
  join: users {{
    sql_on: ${{inspections.user_id}} = ${{users.user_id}} ;;
    relationship: many_to_one
  }}
}}
"""
        return lookml
    
    async def create_dashboard(
        self,
        dashboard_def: BIDashboard
    ) -> Dict[str, Any]:
        """Create Looker dashboard"""
        # POST /api/{api_version}/dashboards
        
        return {
            "success": True,
            "dashboard_id": dashboard_def.dashboard_id,
            "dashboard_url": f"{self.connection.server_url}/dashboards/{dashboard_def.dashboard_id}"
        }
    
    async def run_query(self, query: str) -> List[Dict[str, Any]]:
        """Run SQL query via Looker"""
        # POST /api/{api_version}/queries
        # POST /api/{api_version}/queries/{query_id}/run/json
        
        return []  # Mock result


# ODBC/JDBC Connector

class GenericDatabaseConnector:
    """Generic ODBC/JDBC connector for BI tools"""
    
    def __init__(self, connection: BIConnection):
        self.connection = connection
        self.connection_string = ""
        
    def get_odbc_connection_string(self) -> str:
        """Generate ODBC connection string"""
        # For PostgreSQL (Supabase)
        conn_str = (
            f"Driver={{PostgreSQL Unicode}};"
            f"Server={self.connection.server_url};"
            f"Port=5432;"
            f"Database=radikal_db;"
            f"Uid={self.connection.username};"
            f"Pwd={self.connection.password};"
            f"SSLmode=require;"
        )
        return conn_str
    
    def get_jdbc_connection_string(self) -> str:
        """Generate JDBC connection string"""
        # For PostgreSQL (Supabase)
        jdbc_str = (
            f"jdbc:postgresql://{self.connection.server_url}:5432/radikal_db"
            f"?user={self.connection.username}"
            f"&password={self.connection.password}"
            f"&ssl=true"
        )
        return jdbc_str
    
    def get_connection_parameters(self) -> Dict[str, Any]:
        """Get connection parameters for BI tools"""
        return {
            "host": self.connection.server_url,
            "port": 5432,
            "database": "radikal_db",
            "username": self.connection.username,
            "password": self.connection.password,
            "ssl_mode": "require",
            "driver": "postgresql",
            "odbc_string": self.get_odbc_connection_string(),
            "jdbc_string": self.get_jdbc_connection_string()
        }


# BI Data Model Generator

class BIDataModelGenerator:
    """Generate optimized data models for BI tools"""
    
    @staticmethod
    def generate_star_schema() -> DataModel:
        """Generate star schema for BI"""
        return DataModel(
            model_id=f"model_{secrets.token_hex(8)}",
            model_name="RadiKal Star Schema",
            description="Optimized star schema for BI analytics",
            tables=[
                "fact_inspections",
                "dim_users",
                "dim_defects",
                "dim_time",
                "dim_sites"
            ],
            relationships=[
                {
                    "from_table": "fact_inspections",
                    "from_column": "user_id",
                    "to_table": "dim_users",
                    "to_column": "user_id",
                    "type": "many_to_one"
                },
                {
                    "from_table": "fact_inspections",
                    "from_column": "defect_id",
                    "to_table": "dim_defects",
                    "to_column": "defect_id",
                    "type": "many_to_one"
                }
            ],
            measures=[
                {
                    "name": "total_inspections",
                    "expression": "COUNT(inspection_id)",
                    "format": "number"
                },
                {
                    "name": "defect_rate",
                    "expression": "SUM(has_defect) / COUNT(*) * 100",
                    "format": "percentage"
                },
                {
                    "name": "avg_confidence",
                    "expression": "AVG(xai_confidence)",
                    "format": "percentage"
                }
            ],
            dimensions=[
                {"name": "inspection_date", "type": "date"},
                {"name": "user_name", "type": "string"},
                {"name": "defect_type", "type": "string"},
                {"name": "site_name", "type": "string"}
            ]
        )
    
    @staticmethod
    def generate_tableau_extract_definition() -> Dict[str, Any]:
        """Generate Tableau extract definition"""
        return {
            "tables": [
                {
                    "name": "inspections",
                    "columns": [
                        {"name": "inspection_id", "type": "string"},
                        {"name": "image_path", "type": "string"},
                        {"name": "user_id", "type": "string"},
                        {"name": "prediction", "type": "string"},
                        {"name": "xai_confidence", "type": "real"},
                        {"name": "created_at", "type": "datetime"}
                    ]
                }
            ]
        }
    
    @staticmethod
    def generate_powerbi_schema() -> Dict[str, Any]:
        """Generate Power BI schema"""
        return {
            "name": "RadiKal Dataset",
            "tables": [
                {
                    "name": "Inspections",
                    "columns": [
                        {"name": "InspectionID", "dataType": "string"},
                        {"name": "ImagePath", "dataType": "string"},
                        {"name": "Prediction", "dataType": "string"},
                        {"name": "Confidence", "dataType": "double"},
                        {"name": "CreatedAt", "dataType": "dateTime"}
                    ]
                }
            ],
            "relationships": []
        }


# BI Dashboard Templates

class BIDashboardTemplates:
    """Pre-built dashboard templates for BI platforms"""
    
    @staticmethod
    def get_executive_dashboard_template(platform: BIPlatform) -> BIDashboard:
        """Get executive dashboard template"""
        return BIDashboard(
            dashboard_id=f"exec_dash_{secrets.token_hex(4)}",
            dashboard_name="RadiKal Executive Dashboard",
            platform=platform,
            description="C-level dashboard with KPIs and trends",
            data_sources=["fact_inspections", "dim_defects", "dim_time"],
            visualizations=[
                {
                    "type": "kpi_card",
                    "title": "Defect Rate",
                    "metric": "defect_rate",
                    "format": "percentage"
                },
                {
                    "type": "line_chart",
                    "title": "Defect Trend",
                    "x_axis": "date",
                    "y_axis": "defect_rate"
                },
                {
                    "type": "bar_chart",
                    "title": "Defects by Type",
                    "x_axis": "defect_type",
                    "y_axis": "count"
                }
            ],
            filters=[
                {"field": "date_range", "type": "date"},
                {"field": "site", "type": "multi_select"}
            ],
            refresh_schedule="0 */6 * * *"  # Every 6 hours
        )


# Global connector factory

class BIConnectorFactory:
    """Factory for creating BI connectors"""
    
    @staticmethod
    def create_connector(connection: BIConnection):
        """Create appropriate connector for platform"""
        if connection.platform == BIPlatform.TABLEAU:
            return TableauConnector(connection)
        elif connection.platform == BIPlatform.POWER_BI:
            return PowerBIConnector(connection)
        elif connection.platform == BIPlatform.LOOKER:
            return LookerConnector(connection)
        elif connection.platform in [BIPlatform.GENERIC_ODBC, BIPlatform.GENERIC_JDBC]:
            return GenericDatabaseConnector(connection)
        else:
            raise ValueError(f"Unsupported platform: {connection.platform}")


# Global instances

bi_connector_factory = BIConnectorFactory()
bi_model_generator = BIDataModelGenerator()
bi_templates = BIDashboardTemplates()
