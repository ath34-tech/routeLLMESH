from typing import List
from app.modules.chat.routing.policies.base import Router, RoutingResult
from app.modules.chat.schemas import ChatRequest


class CostRouter(Router):
    """
    Select cheapest enabled model.
    Pure deterministic scoring.
    """
    
    def __init__(self, redis_repo):
        self.redis = redis_repo
    
    async def route(self, request: ChatRequest, enabled_models: List[dict]) -> RoutingResult:
        """
        Select model with lowest total cost.
        """
        
        # Estimate tokens using ChatRequest helper
        input_tokens = request.estimate_tokens()
        output_tokens = 500  # Conservative estimate
        
        cheapest_model = None
        min_cost = float('inf')
        costs = {}
        
        for model in enabled_models:
            model_name = model.get("model_name")
            input_cost = model.get("input_cost", 0)
            output_cost = model.get("output_cost", 0)
            priority = model.get("priority", 50)
            
            # Calculate total cost
            total_cost = (
                input_tokens * input_cost +
                output_tokens * output_cost
            )
            
            # Apply priority as tiebreaker
            priority_bonus = priority * 0.001
            adjusted_cost = total_cost - priority_bonus
            
            costs[model_name] = {
                "total": total_cost,
                "adjusted": adjusted_cost,
                "input_cost": input_cost,
                "output_cost": output_cost
            }
            
            if adjusted_cost < min_cost:
                min_cost = adjusted_cost
                cheapest_model = model
        
        return RoutingResult(
            selected_model=cheapest_model["model_name"],
            routing_policy="cost",
            estimated_cost=min_cost,
            reasoning=f"Selected cheapest model: ${min_cost:.4f}",
            all_candidates=costs
        )
    
    async def observe_outcome(self, result: dict) -> None:
        """Cost router doesn't learn from outcomes."""
        pass