from app.modules.chat.schemas import ChatRequest


class ComplexityAnalyzer:
    """
    Heuristic analyzer for request complexity.
    Returns score 1-10.
    """
    
    KEYWORDS = {
        "reasoning": [
            "deduce", "explain", "analyze", "prove", "derive",
            "infer", "logic", "reason", "evaluate"
        ],
        "coding": [
            "code", "debug", "algorithm", "compile", "regex",
            "function", "class", "method", "syntax", "error",
            "implement", "optimize"
        ],
        "architecture": [
            "design", "system", "scale", "distributed", "async",
            "architecture", "throughput", "latency", "microservice"
        ],
        "math": [
            "integral", "derivative", "theorem", "equation",
            "proof", "matrix", "vector", "calculus", "linear"
        ],
        "analysis": [
            "compare", "evaluate", "summarize", "critique",
            "review", "assess", "analyze"
        ]
    }
    
    @staticmethod
    def analyze(request: ChatRequest) -> dict:
        """
        Analyze request complexity.
        Returns score 1-10.
        """
        
        # Get text content using helper method
        text = request.get_text_content()
        
        # Base score from structural features
        base_score = 1.0
        
        # Structural complexity
        base_score += len(request.messages) / 3  # Multi-turn penalty
        base_score += len(text.split()) / 500    # Length penalty
        
        # Keyword detection
        text_lower = text.lower()
        detected_categories = {}
        
        for category, keywords in ComplexityAnalyzer.KEYWORDS.items():
            matches = sum(1 for kw in keywords if kw in text_lower)
            detected_categories[category] = matches
            base_score += matches * 0.5
        
        # Non-linear scaling for very complex requests
        if base_score > 7:
            base_score *= 1.1
        
        # Clamp to 1-10
        final_score = max(1.0, min(10.0, base_score))
        
        return {
            "score": final_score,
            "detected_categories": detected_categories,
            "message_count": len(request.messages),
            "word_count": len(text.split())
        }