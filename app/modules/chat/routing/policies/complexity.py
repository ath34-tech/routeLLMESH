import numpy as np
from typing import List, Dict, Any
from app.modules.chat.routing.policies.base import Router, RoutingResult
from app.modules.chat.routing.analyzer import ComplexityAnalyzer

class ComplexityThompsonRouter(Router):
    """
    Thompson Sampling for complexity-aware routing.
    """
    
    def __init__(self, redis_repo):
        self.redis = redis_repo
        self.analyzer = ComplexityAnalyzer()
    
    async def route(self, request, enabled_models: List[dict]) -> RoutingResult:
        """
        Thompson Sampling routing.
        """
        
        # Step 1: Analyze complexity
        analysis = self.analyzer.analyze(request)
        complexity_score = analysis["score"]
        complexity_level = int(complexity_score)
        
        # Step 2: Load enabled models and sample from beliefs
        samples = {}
        
        for model in enabled_models:
            model_name = model.get("model_name")
            
            # Get Thompson Sampling beliefs
            alpha_key = f"routing:thompson:{model_name}:complexity_{complexity_level}:alpha"
            beta_key = f"routing:thompson:{model_name}:complexity_{complexity_level}:beta"
            
            alpha = float(await self.redis.get(alpha_key) or "1")
            beta = float(await self.redis.get(beta_key) or "1")
            
            # Sample from Beta distribution
            sample = np.random.beta(alpha, beta)
            
            samples[model_name] = {
                "sample": sample,
                "alpha": alpha,
                "beta": beta,
                "metadata": model
            }
        
        # Step 3: Filter by capability requirements
        candidates = self._filter_candidates(samples, complexity_score, request)
        
        if not candidates:
            # Fallback: pick highest priority model
            fallback = max(enabled_models, key=lambda m: m.get("priority", 0))
            return RoutingResult(
                selected_model=fallback["model_name"],
                routing_policy="complexity",
                complexity_score=complexity_score,
                reasoning="No suitable models, using fallback (highest priority)",
            )
        
        # Step 4: Select highest sampled model
        selected_name = max(candidates, key=lambda m: candidates[m]["sample"])
        selected = candidates[selected_name]
        
        return RoutingResult(
            selected_model=selected_name,
            routing_policy="complexity",
            complexity_score=complexity_score,
            reasoning=(
                f"Thompson Sampling: complexity={complexity_score:.1f}, "
                f"sample={selected['sample']:.3f}, "
                f"belief=(α={selected['alpha']:.0f}, β={selected['beta']:.0f})"
            ),
            all_candidates={
                m: v["sample"] for m, v in samples.items()
            },
            context={
                "analysis": analysis,
                "detected_categories": analysis["detected_categories"],
                "belief_distributions": {
                    m: {"alpha": v["alpha"], "beta": v["beta"]}
                    for m, v in samples.items()
                }
            }
        )
    
    async def observe_outcome(self, result: Dict[str, Any]) -> None:
        """Update belief distribution after observing outcome."""
        
        model_name = result.get("selected_model")
        complexity_score = result.get("complexity_score", 5)
        complexity_level = int(complexity_score)
        user_satisfied = result.get("user_satisfaction", False)
        
        if not model_name:
            return
        
        # Update Thompson Sampling beliefs
        alpha_key = f"routing:thompson:{model_name}:complexity_{complexity_level}:alpha"
        beta_key = f"routing:thompson:{model_name}:complexity_{complexity_level}:beta"
        
        if user_satisfied:
            await self.redis.increment(alpha_key)
        else:
            await self.redis.increment(beta_key)
    
    @staticmethod
    def _filter_candidates(samples: dict, complexity_score: float, request) -> dict:
        """Filter models that can't satisfy the request."""
        
        candidates = {}
        
        for model_name, data in samples.items():
            metadata = data["metadata"]
            
            # High complexity requires reasoning
            if complexity_score >= 7 and not metadata.get("supports_reasoning", False):
                continue
            
            # Vision required
            if ComplexityThompsonRouter._request_needs_vision(request) and not metadata.get("supports_vision", False):
                continue
            
            # Tools required
            if ComplexityThompsonRouter._request_has_tools(request) and not metadata.get("supports_tools", False):
                continue
            
            # Context window check
            estimated_tokens = ComplexityThompsonRouter._estimate_tokens(request)
            if metadata.get("context_window", 4096) < estimated_tokens * 2:
                continue
            
            candidates[model_name] = data
        
        return candidates
    
    @staticmethod
    def _request_needs_vision(request) -> bool:
        """Check if request needs vision capability."""
        for msg in request.messages:
            # Handle Pydantic model
            if hasattr(msg, "content"):
                content = msg.content
            # Handle dict
            elif isinstance(msg, dict):
                content = msg.get("content", "")
            else:
                continue
            
            # Check for images in multimodal content
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "image_url":
                        return True
                    elif hasattr(item, "type") and item.type == "image_url":
                        return True
        
        return False
    
    @staticmethod
    def _request_has_tools(request) -> bool:
        """Check if request has tools."""
        return hasattr(request, 'tools') and bool(request.tools)
    
    @staticmethod
    def _estimate_tokens(request) -> int:
        """Estimate request tokens."""
        text = ""
        for msg in request.messages:
            if hasattr(msg, "content"):
                content = msg.content
            elif isinstance(msg, dict):
                content = msg.get("content", "")
            else:
                continue
            
            if isinstance(content, str):
                text += content
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text += item.get("text", "")
                    elif hasattr(item, "text"):
                        text += item.text
        
        return max(10, len(text) // 4)