# Same as before
from typing import Dict
from app.modules.chat.routing.policies.base import Router
from app.modules.chat.routing.policies.cost import CostRouter
from app.modules.chat.routing.policies.complexity import ComplexityThompsonRouter
from app.modules.chat.routing.policies.complexity_v1 import ComplexityRouter
class RouterRegistry:
    """Registry pattern for routing policies."""
    
    def __init__(self, redis_repo):
        self.redis = redis_repo
        self._registry: Dict[str, Router] = {}
        self._register_default_routers()
    
    def _register_default_routers(self):
        """Initialize default routing policies."""
        self._registry["cost"] = CostRouter(self.redis)
        self._registry["complexity"] = ComplexityRouter(self.redis)
    
    def register(self, policy_name: str, router: Router) -> None:
        """Register a new router."""
        self._registry[policy_name] = router
    
    def get(self, policy_name: str) -> Router:
        """Get router by policy name."""
        if policy_name not in self._registry:
            raise ValueError(
                f"Routing policy '{policy_name}' not found. "
                f"Available: {list(self._registry.keys())}"
            )
        return self._registry[policy_name]
    
    def list_policies(self) -> list:
        """List all registered policies."""
        return list(self._registry.keys())