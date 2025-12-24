"""
Enterprise SSO/SAML API Routes

Endpoints for SSO authentication flows
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import jwt
import secrets

from core.sso_auth import (
    sso_manager,
    SSOProvider,
    SSOConfiguration,
    MFAMethod
)
from core.auth import get_current_user, create_access_token

# Try to import settings, fallback if not configured
try:
    from core.config import settings
except:
    settings = None

router = APIRouter(prefix="/api/sso", tags=["sso"])


# Request/Response Models

class SSOProviderConfig(BaseModel):
    provider: SSOProvider
    enabled: bool = True
    saml_entity_id: Optional[str] = None
    saml_sso_url: Optional[str] = None
    saml_certificate: Optional[str] = None
    oauth_client_id: Optional[str] = None
    oauth_redirect_uri: Optional[str] = None
    oauth_authorization_endpoint: Optional[str] = None
    oauth_token_endpoint: Optional[str] = None
    ldap_server: Optional[str] = None
    ldap_port: Optional[int] = 389
    ldap_base_dn: Optional[str] = None
    auto_provision_users: bool = True
    default_role: str = "technician"


class SAMLLoginRequest(BaseModel):
    relay_state: Optional[str] = None


class SAMLCallbackRequest(BaseModel):
    saml_response: str
    relay_state: Optional[str] = None


class OAuthLoginRequest(BaseModel):
    state: Optional[str] = None


class OAuthCallbackRequest(BaseModel):
    code: str
    state: str


class LDAPLoginRequest(BaseModel):
    username: str
    password: str


class MFAEnableRequest(BaseModel):
    method: MFAMethod


class MFAVerifyRequest(BaseModel):
    code: str


# Configuration Endpoints

@router.post("/config")
async def configure_sso(
    config: SSOProviderConfig,
    current_user: dict = Depends(get_current_user)
):
    """Configure SSO provider for tenant (admin only)"""
    
    if current_user.get("role") != "manager":
        raise HTTPException(status_code=403, detail="Only managers can configure SSO")
    
    tenant_id = current_user.get("tenant_id")
    
    sso_config = SSOConfiguration(**config.dict())
    sso_manager.add_provider(tenant_id, sso_config)
    
    return {
        "success": True,
        "message": f"SSO provider {config.provider} configured successfully",
        "provider": config.provider,
        "enabled": config.enabled
    }


@router.get("/config")
async def get_sso_config(
    current_user: dict = Depends(get_current_user)
):
    """Get SSO configuration for tenant"""
    
    tenant_id = current_user.get("tenant_id")
    config = sso_manager.configurations.get(tenant_id)
    
    if not config:
        return {
            "configured": False,
            "provider": None
        }
    
    return {
        "configured": True,
        "provider": config.provider,
        "enabled": config.enabled,
        "auto_provision_users": config.auto_provision_users,
        "default_role": config.default_role
    }


@router.get("/providers")
async def list_providers():
    """List available SSO providers"""
    
    return {
        "providers": [
            {
                "id": "saml_okta",
                "name": "Okta (SAML)",
                "type": "saml",
                "description": "Enterprise SSO with Okta"
            },
            {
                "id": "saml_azure_ad",
                "name": "Azure AD (SAML)",
                "type": "saml",
                "description": "Microsoft Azure Active Directory"
            },
            {
                "id": "saml_onelogin",
                "name": "OneLogin (SAML)",
                "type": "saml",
                "description": "Enterprise SSO with OneLogin"
            },
            {
                "id": "oauth_google",
                "name": "Google (OAuth)",
                "type": "oauth",
                "description": "Sign in with Google"
            },
            {
                "id": "oauth_microsoft",
                "name": "Microsoft (OAuth)",
                "type": "oauth",
                "description": "Sign in with Microsoft"
            },
            {
                "id": "oauth_github",
                "name": "GitHub (OAuth)",
                "type": "oauth",
                "description": "Sign in with GitHub"
            },
            {
                "id": "ldap",
                "name": "LDAP",
                "type": "ldap",
                "description": "LDAP directory authentication"
            },
            {
                "id": "active_directory",
                "name": "Active Directory",
                "type": "ldap",
                "description": "Microsoft Active Directory"
            }
        ]
    }


# SAML Endpoints

@router.post("/saml/login")
async def saml_login(
    request: SAMLLoginRequest,
    tenant_id: str
):
    """Initiate SAML SSO login"""
    
    try:
        authenticator = sso_manager.get_authenticator(tenant_id, SSOProvider.SAML_OKTA)
        sso_data = await authenticator.initiate_sso(request.relay_state)
        
        return {
            "sso_url": sso_data["sso_url"],
            "saml_request": sso_data["saml_request"],
            "relay_state": sso_data["relay_state"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SAML login failed: {str(e)}")


@router.post("/saml/callback")
async def saml_callback(
    request: SAMLCallbackRequest,
    tenant_id: str
):
    """Handle SAML SSO callback"""
    
    try:
        authenticator = sso_manager.get_authenticator(tenant_id, SSOProvider.SAML_OKTA)
        sso_user = await authenticator.validate_assertion(request.saml_response)
        
        # Auto-provision user if enabled
        user = await sso_manager.provision_user(sso_user, tenant_id)
        
        # Create JWT token
        access_token = create_access_token(
            data={
                "sub": user["user_id"],
                "email": user["email"],
                "role": user["roles"][0],
                "tenant_id": tenant_id,
                "sso_provider": sso_user.provider
            }
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"SAML authentication failed: {str(e)}")


# OAuth Endpoints

@router.post("/oauth/login")
async def oauth_login(
    request: OAuthLoginRequest,
    provider: SSOProvider,
    tenant_id: str
):
    """Initiate OAuth login"""
    
    if not provider.startswith("oauth_"):
        raise HTTPException(status_code=400, detail="Invalid OAuth provider")
    
    try:
        authenticator = sso_manager.get_authenticator(tenant_id, provider)
        auth_data = await authenticator.get_authorization_url(request.state)
        
        return {
            "authorization_url": auth_data["authorization_url"],
            "state": auth_data["state"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OAuth login failed: {str(e)}")


@router.post("/oauth/callback")
async def oauth_callback(
    request: OAuthCallbackRequest,
    provider: SSOProvider,
    tenant_id: str
):
    """Handle OAuth callback"""
    
    try:
        authenticator = sso_manager.get_authenticator(tenant_id, provider)
        
        # Exchange code for token
        token_data = await authenticator.exchange_code_for_token(request.code)
        
        # Get user info
        sso_user = await authenticator.get_user_info(token_data["access_token"])
        
        # Auto-provision user
        user = await sso_manager.provision_user(sso_user, tenant_id)
        
        # Create JWT token
        access_token = create_access_token(
            data={
                "sub": user["user_id"],
                "email": user["email"],
                "role": user["roles"][0],
                "tenant_id": tenant_id,
                "sso_provider": sso_user.provider
            }
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"OAuth authentication failed: {str(e)}")


# LDAP Endpoints

@router.post("/ldap/login")
async def ldap_login(
    request: LDAPLoginRequest,
    tenant_id: str
):
    """Authenticate with LDAP"""
    
    try:
        authenticator = sso_manager.get_authenticator(tenant_id, SSOProvider.LDAP)
        sso_user = await authenticator.authenticate(request.username, request.password)
        
        if not sso_user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Auto-provision user
        user = await sso_manager.provision_user(sso_user, tenant_id)
        
        # Create JWT token
        access_token = create_access_token(
            data={
                "sub": user["user_id"],
                "email": user["email"],
                "role": user["roles"][0],
                "tenant_id": tenant_id,
                "sso_provider": "ldap"
            }
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"LDAP authentication failed: {str(e)}")


# MFA Endpoints

@router.post("/mfa/enable")
async def enable_mfa(
    request: MFAEnableRequest,
    current_user: dict = Depends(get_current_user)
):
    """Enable MFA for user"""
    
    user_id = current_user.get("user_id")
    
    if request.method == MFAMethod.TOTP:
        mfa_data = await sso_manager.mfa_manager.enable_totp(user_id)
        return {
            "success": True,
            "method": "totp",
            "secret": mfa_data["secret"],
            "qr_code_url": mfa_data["qr_code_url"]
        }
    
    elif request.method == MFAMethod.SMS:
        phone_number = current_user.get("phone_number")
        if not phone_number:
            raise HTTPException(status_code=400, detail="Phone number required for SMS MFA")
        
        success = await sso_manager.mfa_manager.send_sms_code(user_id, phone_number)
        return {
            "success": success,
            "method": "sms",
            "message": "Verification code sent to your phone"
        }
    
    elif request.method == MFAMethod.EMAIL:
        email = current_user.get("email")
        success = await sso_manager.mfa_manager.send_email_code(user_id, email)
        return {
            "success": success,
            "method": "email",
            "message": "Verification code sent to your email"
        }
    
    else:
        raise HTTPException(status_code=400, detail="Unsupported MFA method")


@router.post("/mfa/verify")
async def verify_mfa(
    request: MFAVerifyRequest,
    current_user: dict = Depends(get_current_user)
):
    """Verify MFA code"""
    
    user_id = current_user.get("user_id")
    
    verified = await sso_manager.mfa_manager.verify_totp(user_id, request.code)
    
    if not verified:
        raise HTTPException(status_code=401, detail="Invalid MFA code")
    
    return {
        "success": True,
        "message": "MFA verified successfully"
    }


@router.delete("/mfa")
async def disable_mfa(
    current_user: dict = Depends(get_current_user)
):
    """Disable MFA for user"""
    
    user_id = current_user.get("user_id")
    
    # Remove MFA from database
    # In production, update user record
    
    return {
        "success": True,
        "message": "MFA disabled successfully"
    }


# Session Management

@router.post("/logout")
async def sso_logout(
    current_user: dict = Depends(get_current_user)
):
    """Logout from SSO session"""
    
    # In production, invalidate SSO session with provider
    # For SAML, initiate Single Logout (SLO)
    
    return {
        "success": True,
        "message": "Logged out successfully"
    }


@router.get("/session")
async def get_session(
    current_user: dict = Depends(get_current_user)
):
    """Get current SSO session info"""
    
    return {
        "user_id": current_user.get("user_id"),
        "email": current_user.get("email"),
        "role": current_user.get("role"),
        "tenant_id": current_user.get("tenant_id"),
        "sso_provider": current_user.get("sso_provider"),
        "mfa_enabled": False  # Check from database
    }
