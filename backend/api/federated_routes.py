"""
Federated Learning API Routes

Endpoints for:
- Node registration
- Training round coordination
- Model updates
- Privacy management
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import numpy as np

from ml.federated_learning import (
    federated_coordinator,
    FederatedWorker,
    NodeRole,
    PrivacyMechanism
)


router = APIRouter(prefix="/api/federated", tags=["federated-learning"])


# Request/Response Models

class NodeRegistrationRequest(BaseModel):
    node_name: str
    role: str
    compute_capacity: float
    privacy_budget: float


class TrainingRoundRequest(BaseModel):
    min_nodes: int = 3
    privacy_mechanism: str = "differential_privacy"
    epsilon: float = 1.0
    delta: float = 1e-5


class ModelUpdateRequest(BaseModel):
    node_id: str
    round_id: str
    weights: List[List[float]]
    num_samples: int


# Endpoints

@router.post("/nodes/register")
async def register_node(request: NodeRegistrationRequest):
    """Register a federated learning node"""
    try:
        role = NodeRole(request.role)
        
        node = federated_coordinator.register_node(
            node_name=request.node_name,
            role=role,
            compute_capacity=request.compute_capacity,
            privacy_budget=request.privacy_budget
        )
        
        return {
            "status": "success",
            "node_id": node.node_id,
            "registered_at": node.registered_at.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/nodes/{node_id}")
async def unregister_node(node_id: str):
    """Unregister a node"""
    try:
        success = federated_coordinator.unregister_node(node_id)
        
        if success:
            return {
                "status": "success",
                "message": "Node unregistered"
            }
        else:
            raise HTTPException(status_code=404, detail="Node not found")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/training/start")
async def start_training_round(request: TrainingRoundRequest):
    """Start a new training round"""
    try:
        privacy_mechanism = PrivacyMechanism(request.privacy_mechanism)
        
        round = federated_coordinator.start_training_round(
            min_nodes=request.min_nodes,
            privacy_mechanism=privacy_mechanism,
            epsilon=request.epsilon,
            delta=request.delta
        )
        
        return {
            "status": "success",
            "round_id": round.round_id,
            "started_at": round.started_at.isoformat(),
            "participating_nodes": round.participating_nodes
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/training/update")
async def submit_model_update(request: ModelUpdateRequest):
    """Submit model update from worker"""
    try:
        # Convert weights to numpy array
        weights_array = np.array(request.weights)
        
        # Submit update to coordinator
        update = federated_coordinator.aggregate_updates(
            round_id=request.round_id,
            node_id=request.node_id,
            weights=weights_array,
            num_samples=request.num_samples
        )
        
        return {
            "status": "success",
            "message": "Model update received"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/training/complete/{round_id}")
async def complete_training_round(round_id: str):
    """Complete training round and aggregate models"""
    try:
        global_model = federated_coordinator.complete_round(round_id)
        
        if global_model is not None:
            return {
                "status": "success",
                "round_id": round_id,
                "global_model_shape": list(global_model.shape)
            }
        else:
            raise HTTPException(status_code=400, detail="No updates received")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/training/status/{round_id}")
async def get_training_status(round_id: str):
    """Get training round status"""
    try:
        convergence = federated_coordinator.get_convergence_status()
        
        return {
            "status": "success",
            "round_id": round_id,
            "convergence": convergence
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/privacy/budget/{node_id}")
async def get_privacy_budget(node_id: str):
    """Get remaining privacy budget for node"""
    try:
        # Get node privacy budget
        node = federated_coordinator.nodes.get(node_id)
        
        if node:
            return {
                "status": "success",
                "node_id": node_id,
                "privacy_budget": node.privacy_budget,
                "privacy_spent": node.privacy_spent,
                "budget_remaining": node.privacy_budget - node.privacy_spent
            }
        else:
            raise HTTPException(status_code=404, detail="Node not found")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
