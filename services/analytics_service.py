from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from models.user import UserInteraction
from utils.logger import get_logger

logger = get_logger(__name__)

class AnalyticsService:
    """Service for tracking and analyzing user interactions"""
    
    def __init__(self):
        self.interactions: List[UserInteraction] = []
        self.session_data: Dict[str, Any] = defaultdict(dict)
    
    def log_interaction(self, interaction: UserInteraction) -> None:
        """Log a user interaction"""
        self.interactions.append(interaction)
        logger.info(f"Logged interaction: {interaction.action} by user {interaction.user_id}")
    
    def log_search(self, user_id: Optional[str], query: str, result_count: int, 
                   filters: Dict[str, Any]) -> None:
        """Log a search interaction"""
        interaction = UserInteraction(
            user_id=user_id,
            action="search",
            scholarship_id=None,
            timestamp=datetime.utcnow(),
            metadata={
                "query": query,
                "result_count": result_count,
                "filters": filters
            }
        )
        self.log_interaction(interaction)
    
    def log_scholarship_view(self, user_id: Optional[str], scholarship_id: str) -> None:
        """Log when a user views a scholarship"""
        interaction = UserInteraction(
            user_id=user_id,
            action="view_scholarship",
            scholarship_id=scholarship_id,
            timestamp=datetime.utcnow()
        )
        self.log_interaction(interaction)
    
    def log_eligibility_check(self, user_id: Optional[str], scholarship_id: str, 
                            eligible: bool, match_score: float) -> None:
        """Log an eligibility check"""
        interaction = UserInteraction(
            user_id=user_id,
            action="eligibility_check",
            scholarship_id=scholarship_id,
            timestamp=datetime.utcnow(),
            metadata={
                "eligible": eligible,
                "match_score": match_score
            }
        )
        self.log_interaction(interaction)
    
    def log_recommendation_request(self, user_id: Optional[str], 
                                 recommendation_count: int) -> None:
        """Log a recommendation request"""
        interaction = UserInteraction(
            user_id=user_id,
            action="get_recommendations",
            scholarship_id=None,
            timestamp=datetime.utcnow(),
            metadata={
                "recommendation_count": recommendation_count
            }
        )
        self.log_interaction(interaction)
    
    def get_analytics_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get analytics summary for the specified number of days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        recent_interactions = [
            i for i in self.interactions 
            if i.timestamp >= cutoff_date
        ]
        
        # Basic metrics
        total_interactions = len(recent_interactions)
        unique_users = len(set(i.user_id for i in recent_interactions if i.user_id))
        
        # Action breakdown
        action_counts = Counter(i.action for i in recent_interactions)
        
        # Popular scholarships
        scholarship_views = [
            i for i in recent_interactions 
            if i.action == "view_scholarship" and i.scholarship_id
        ]
        popular_scholarships = Counter(i.scholarship_id for i in scholarship_views)
        
        # Search analytics
        search_interactions = [i for i in recent_interactions if i.action == "search"]
        total_searches = len(search_interactions)
        
        # Average results per search
        avg_results_per_search = 0
        if search_interactions:
            total_results = sum(
                i.metadata.get("result_count", 0) 
                for i in search_interactions 
                if i.metadata
            )
            avg_results_per_search = total_results / len(search_interactions)
        
        # Popular search terms
        search_terms = []
        for interaction in search_interactions:
            if interaction.metadata and "query" in interaction.metadata:
                query = interaction.metadata["query"]
                if query:  # Non-empty query
                    search_terms.append(query.lower())
        
        popular_search_terms = Counter(search_terms)
        
        # Eligibility check analytics
        eligibility_checks = [
            i for i in recent_interactions 
            if i.action == "eligibility_check"
        ]
        
        successful_eligibility = len([
            i for i in eligibility_checks
            if i.metadata and i.metadata.get("eligible", False)
        ])
        
        eligibility_rate = 0
        if eligibility_checks:
            eligibility_rate = successful_eligibility / len(eligibility_checks)
        
        return {
            "period_days": days,
            "total_interactions": total_interactions,
            "unique_users": unique_users,
            "interactions_by_action": dict(action_counts),
            "popular_scholarships": dict(popular_scholarships.most_common(10)),
            "search_analytics": {
                "total_searches": total_searches,
                "avg_results_per_search": round(avg_results_per_search, 2),
                "popular_terms": dict(popular_search_terms.most_common(10))
            },
            "eligibility_analytics": {
                "total_checks": len(eligibility_checks),
                "successful_checks": successful_eligibility,
                "eligibility_rate": round(eligibility_rate, 2)
            }
        }
    
    def get_user_analytics(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get analytics for a specific user"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        user_interactions = [
            i for i in self.interactions 
            if i.user_id == user_id and i.timestamp >= cutoff_date
        ]
        
        if not user_interactions:
            return {
                "user_id": user_id,
                "period_days": days,
                "total_interactions": 0,
                "message": "No interactions found for this user in the specified period"
            }
        
        # User activity breakdown
        action_counts = Counter(i.action for i in user_interactions)
        
        # Viewed scholarships
        viewed_scholarships = [
            i.scholarship_id for i in user_interactions
            if i.action == "view_scholarship" and i.scholarship_id
        ]
        
        # Search history
        searches = [
            {
                "timestamp": i.timestamp,
                "query": i.metadata.get("query", "") if i.metadata else "",
                "result_count": i.metadata.get("result_count", 0) if i.metadata else 0
            }
            for i in user_interactions if i.action == "search"
        ]
        
        # Eligibility checks
        eligibility_checks = [
            {
                "scholarship_id": i.scholarship_id,
                "eligible": i.metadata.get("eligible", False) if i.metadata else False,
                "match_score": i.metadata.get("match_score", 0) if i.metadata else 0,
                "timestamp": i.timestamp
            }
            for i in user_interactions if i.action == "eligibility_check"
        ]
        
        return {
            "user_id": user_id,
            "period_days": days,
            "total_interactions": len(user_interactions),
            "first_interaction": min(i.timestamp for i in user_interactions),
            "last_interaction": max(i.timestamp for i in user_interactions),
            "activity_breakdown": dict(action_counts),
            "viewed_scholarships": list(set(viewed_scholarships)),
            "search_history": searches[-10:],  # Last 10 searches
            "eligibility_checks": eligibility_checks[-10:]  # Last 10 checks
        }

# Global service instance
analytics_service = AnalyticsService()
