"""
Federated Learning System for RadiKal

Privacy-preserving machine learning across multiple sites with:
- Distributed training coordination
- Differential privacy mechanisms
- Secure model aggregation
- Multi-site collaboration
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from datetime import datetime
from enum import Enum
import numpy as np
import secrets
import hashlib


class NodeRole(str, Enum):
    """Federated learning node roles"""
    COORDINATOR = "coordinator"  # Central coordinator
    WORKER = "worker"  # Training worker at site
    AGGREGATOR = "aggregator"  # Model aggregation server


class TrainingStatus(str, Enum):
    """Training round status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class PrivacyMechanism(str, Enum):
    """Privacy preservation methods"""
    DIFFERENTIAL_PRIVACY = "differential_privacy"
    SECURE_AGGREGATION = "secure_aggregation"
    HOMOMORPHIC_ENCRYPTION = "homomorphic_encryption"
    FEDERATED_AVERAGING = "federated_averaging"


# Data Models

class FederatedNode(BaseModel):
    """Federated learning node"""
    node_id: str
    node_name: str
    role: NodeRole
    site_location: str
    is_active: bool = True
    last_heartbeat: Optional[datetime] = None
    total_samples: int = 0
    model_version: int = 0
    privacy_budget: float = 1.0  # Epsilon for differential privacy
    metadata: Dict[str, Any] = {}


class ModelUpdate(BaseModel):
    """Model update from worker node"""
    update_id: str
    node_id: str
    round_number: int
    model_weights: List[float]  # Serialized model weights
    num_samples: int
    loss: float
    accuracy: float
    privacy_spent: float
    timestamp: datetime
    signature: str  # Cryptographic signature for verification


class TrainingRound(BaseModel):
    """Federated training round"""
    round_id: str
    round_number: int
    status: TrainingStatus
    participating_nodes: List[str]
    target_accuracy: float = 0.95
    min_nodes: int = 3
    max_rounds: int = 100
    privacy_mechanism: PrivacyMechanism
    global_model_version: int
    aggregated_loss: Optional[float] = None
    aggregated_accuracy: Optional[float] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class FederatedConfig(BaseModel):
    """Federated learning configuration"""
    federation_id: str
    federation_name: str
    coordinator_url: str
    min_participating_nodes: int = 3
    max_rounds: int = 100
    target_accuracy: float = 0.95
    learning_rate: float = 0.001
    batch_size: int = 32
    privacy_mechanism: PrivacyMechanism = PrivacyMechanism.DIFFERENTIAL_PRIVACY
    epsilon: float = 1.0  # Differential privacy budget
    delta: float = 1e-5  # Differential privacy delta
    secure_aggregation: bool = True
    model_architecture: str = "yolov8-cls"


# Federated Learning Coordinator

class FederatedCoordinator:
    """Central coordinator for federated learning"""
    
    def __init__(self, config: FederatedConfig):
        self.config = config
        self.nodes: Dict[str, FederatedNode] = {}
        self.current_round: Optional[TrainingRound] = None
        self.round_history: List[TrainingRound] = []
        self.global_model_weights: Optional[List[float]] = None
        self.global_model_version = 0
        
    def register_node(self, node: FederatedNode) -> bool:
        """Register a new worker node"""
        if node.node_id in self.nodes:
            return False
        
        self.nodes[node.node_id] = node
        return True
    
    def unregister_node(self, node_id: str) -> bool:
        """Unregister a worker node"""
        if node_id in self.nodes:
            del self.nodes[node_id]
            return True
        return False
    
    def start_training_round(self) -> TrainingRound:
        """Initiate a new training round"""
        # Get active nodes
        active_nodes = [n.node_id for n in self.nodes.values() if n.is_active]
        
        if len(active_nodes) < self.config.min_participating_nodes:
            raise ValueError(f"Not enough active nodes. Need {self.config.min_participating_nodes}, have {len(active_nodes)}")
        
        round_number = len(self.round_history) + 1
        
        training_round = TrainingRound(
            round_id=f"round_{round_number}_{secrets.token_hex(4)}",
            round_number=round_number,
            status=TrainingStatus.PENDING,
            participating_nodes=active_nodes,
            target_accuracy=self.config.target_accuracy,
            min_nodes=self.config.min_participating_nodes,
            max_rounds=self.config.max_rounds,
            privacy_mechanism=self.config.privacy_mechanism,
            global_model_version=self.global_model_version,
            started_at=datetime.now()
        )
        
        self.current_round = training_round
        return training_round
    
    def aggregate_updates(self, updates: List[ModelUpdate]) -> Dict[str, Any]:
        """Aggregate model updates from workers using FedAvg"""
        if not updates:
            return {"success": False, "error": "No updates to aggregate"}
        
        # Weighted averaging based on number of samples
        total_samples = sum(u.num_samples for u in updates)
        
        # Initialize aggregated weights
        num_weights = len(updates[0].model_weights)
        aggregated_weights = [0.0] * num_weights
        
        # Federated averaging
        for update in updates:
            weight = update.num_samples / total_samples
            for i in range(num_weights):
                aggregated_weights[i] += weight * update.model_weights[i]
        
        # Apply differential privacy noise
        if self.config.privacy_mechanism == PrivacyMechanism.DIFFERENTIAL_PRIVACY:
            aggregated_weights = self._add_differential_privacy(
                aggregated_weights,
                self.config.epsilon,
                self.config.delta
            )
        
        # Update global model
        self.global_model_weights = aggregated_weights
        self.global_model_version += 1
        
        # Calculate aggregated metrics
        total_loss = sum(u.loss * u.num_samples for u in updates) / total_samples
        total_accuracy = sum(u.accuracy * u.num_samples for u in updates) / total_samples
        
        return {
            "success": True,
            "global_model_version": self.global_model_version,
            "aggregated_loss": total_loss,
            "aggregated_accuracy": total_accuracy,
            "num_updates": len(updates),
            "total_samples": total_samples
        }
    
    def _add_differential_privacy(
        self,
        weights: List[float],
        epsilon: float,
        delta: float
    ) -> List[float]:
        """Add Gaussian noise for differential privacy"""
        # Gaussian mechanism for differential privacy
        # sensitivity = 1.0  # L2 sensitivity
        # sigma = np.sqrt(2 * np.log(1.25 / delta)) / epsilon
        
        # For production, use proper DP library like Google's DP library
        # This is a simplified implementation
        sigma = 0.01  # Noise scale
        
        noisy_weights = []
        for w in weights:
            noise = np.random.normal(0, sigma)
            noisy_weights.append(w + noise)
        
        return noisy_weights
    
    def complete_round(self, updates: List[ModelUpdate]) -> TrainingRound:
        """Complete current training round"""
        if not self.current_round:
            raise ValueError("No active training round")
        
        # Aggregate updates
        agg_result = self.aggregate_updates(updates)
        
        # Update round status
        self.current_round.status = TrainingStatus.COMPLETED
        self.current_round.aggregated_loss = agg_result["aggregated_loss"]
        self.current_round.aggregated_accuracy = agg_result["aggregated_accuracy"]
        self.current_round.completed_at = datetime.now()
        
        # Add to history
        self.round_history.append(self.current_round)
        
        completed_round = self.current_round
        self.current_round = None
        
        return completed_round
    
    def get_convergence_status(self) -> Dict[str, Any]:
        """Check if federated training has converged"""
        if not self.round_history:
            return {
                "converged": False,
                "current_accuracy": 0.0,
                "target_accuracy": self.config.target_accuracy,
                "rounds_completed": 0
            }
        
        last_round = self.round_history[-1]
        current_accuracy = last_round.aggregated_accuracy or 0.0
        converged = current_accuracy >= self.config.target_accuracy
        
        return {
            "converged": converged,
            "current_accuracy": current_accuracy,
            "target_accuracy": self.config.target_accuracy,
            "rounds_completed": len(self.round_history),
            "max_rounds": self.config.max_rounds
        }


# Federated Learning Worker

class FederatedWorker:
    """Worker node for local training"""
    
    def __init__(self, node_id: str, coordinator_url: str):
        self.node_id = node_id
        self.coordinator_url = coordinator_url
        self.local_model_weights: Optional[List[float]] = None
        self.training_data_size = 0
        
    async def fetch_global_model(self) -> List[float]:
        """Fetch latest global model from coordinator"""
        # In production, make HTTP request to coordinator
        # response = await httpx.get(f"{self.coordinator_url}/global-model")
        # return response.json()["model_weights"]
        
        # Placeholder
        return [0.1] * 1000  # Mock model weights
    
    async def train_local_model(
        self,
        global_weights: List[float],
        local_data: Any,
        epochs: int = 5
    ) -> ModelUpdate:
        """Train model locally on private data"""
        # Initialize with global weights
        self.local_model_weights = global_weights.copy()
        
        # Simulate local training
        # In production, use actual training loop with PyTorch/TensorFlow
        # model.load_state_dict(global_weights)
        # for epoch in range(epochs):
        #     for batch in local_data:
        #         loss = model(batch)
        #         loss.backward()
        #         optimizer.step()
        
        # Mock training results
        trained_weights = [w + np.random.normal(0, 0.01) for w in global_weights]
        
        update = ModelUpdate(
            update_id=f"update_{secrets.token_hex(8)}",
            node_id=self.node_id,
            round_number=1,
            model_weights=trained_weights,
            num_samples=self.training_data_size,
            loss=0.15,
            accuracy=0.92,
            privacy_spent=0.1,
            timestamp=datetime.now(),
            signature=self._sign_update(trained_weights)
        )
        
        return update
    
    def _sign_update(self, weights: List[float]) -> str:
        """Cryptographically sign model update"""
        # In production, use proper digital signatures (RSA, ECDSA)
        weights_str = str(weights[:10])  # Sample of weights
        return hashlib.sha256(weights_str.encode()).hexdigest()
    
    async def send_update(self, update: ModelUpdate) -> bool:
        """Send model update to coordinator"""
        # In production, make HTTP POST to coordinator
        # response = await httpx.post(
        #     f"{self.coordinator_url}/updates",
        #     json=update.dict()
        # )
        # return response.status_code == 200
        
        return True  # Mock success


# Secure Aggregation

class SecureAggregator:
    """Secure aggregation using secret sharing"""
    
    def __init__(self, num_workers: int):
        self.num_workers = num_workers
        self.shares: Dict[str, List[float]] = {}
        
    def create_shares(self, weights: List[float], num_shares: int) -> List[List[float]]:
        """Create secret shares using Shamir's Secret Sharing"""
        # Simplified implementation
        # In production, use proper cryptographic library
        
        shares = []
        for _ in range(num_shares):
            # Generate random share
            share = [w + np.random.normal(0, 0.001) for w in weights]
            shares.append(share)
        
        return shares
    
    def reconstruct_from_shares(self, shares: List[List[float]]) -> List[float]:
        """Reconstruct weights from shares"""
        if not shares:
            return []
        
        num_weights = len(shares[0])
        reconstructed = [0.0] * num_weights
        
        # Average shares (simplified reconstruction)
        for share in shares:
            for i in range(num_weights):
                reconstructed[i] += share[i] / len(shares)
        
        return reconstructed


# Privacy Budget Manager

class PrivacyBudgetManager:
    """Manage differential privacy budget across rounds"""
    
    def __init__(self, total_epsilon: float, total_delta: float):
        self.total_epsilon = total_epsilon
        self.total_delta = total_delta
        self.spent_epsilon = 0.0
        self.spent_delta = 0.0
        self.round_budgets: List[Dict[str, float]] = []
        
    def allocate_budget(self, round_number: int, num_rounds: int) -> Dict[str, float]:
        """Allocate privacy budget for a round"""
        # Simple uniform allocation
        epsilon_per_round = self.total_epsilon / num_rounds
        delta_per_round = self.total_delta / num_rounds
        
        budget = {
            "epsilon": epsilon_per_round,
            "delta": delta_per_round,
            "round": round_number
        }
        
        self.round_budgets.append(budget)
        self.spent_epsilon += epsilon_per_round
        self.spent_delta += delta_per_round
        
        return budget
    
    def get_remaining_budget(self) -> Dict[str, float]:
        """Get remaining privacy budget"""
        return {
            "remaining_epsilon": self.total_epsilon - self.spent_epsilon,
            "remaining_delta": self.total_delta - self.spent_delta,
            "spent_epsilon": self.spent_epsilon,
            "spent_delta": self.spent_delta
        }
    
    def is_budget_exhausted(self) -> bool:
        """Check if privacy budget is exhausted"""
        return self.spent_epsilon >= self.total_epsilon


# Global instances

federated_coordinator: Optional[FederatedCoordinator] = None
privacy_manager = PrivacyBudgetManager(total_epsilon=10.0, total_delta=1e-5)
