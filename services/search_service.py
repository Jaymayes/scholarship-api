from typing import Any

from models.scholarship import Scholarship, SearchFilters
from models.user import RecommendationRequest, UserProfile
from services.eligibility_service import eligibility_service
from services.scholarship_service import scholarship_service
from utils.logger import get_logger

logger = get_logger(__name__)

class SearchService:
    """Advanced search and recommendation service"""

    def get_recommendations(self, request: RecommendationRequest) -> list[dict[str, Any]]:
        """Generate personalized scholarship recommendations"""
        logger.info(f"Generating recommendations for user {request.user_profile.id}")

        # Get all scholarships
        all_scholarships = scholarship_service.get_all_scholarships()
        recommendations = []

        for scholarship in all_scholarships:
            # Check eligibility
            eligibility_result = eligibility_service._evaluate_eligibility(
                request.user_profile, scholarship
            )

            # Include scholarship if eligible or if including ineligible ones
            if eligibility_result.eligible or request.include_ineligible:
                recommendation = {
                    "scholarship": {
                        "id": scholarship.id,
                        "name": scholarship.name,
                        "organization": scholarship.organization,
                        "amount": scholarship.amount,
                        "application_deadline": scholarship.application_deadline,
                        "scholarship_type": scholarship.scholarship_type,
                        "description": scholarship.description[:200] + "..." if len(scholarship.description) > 200 else scholarship.description
                    },
                    "eligibility": {
                        "eligible": eligibility_result.eligible,
                        "match_score": eligibility_result.match_score,
                        "reasons": eligibility_result.reasons
                    },
                    "recommendation_score": self._calculate_recommendation_score(
                        request.user_profile, scholarship, eligibility_result.match_score
                    )
                }
                recommendations.append(recommendation)

        # Sort by recommendation score (highest first)
        recommendations.sort(key=lambda x: x["recommendation_score"], reverse=True)

        # Apply limit
        recommendations = recommendations[:request.limit]

        logger.info(f"Generated {len(recommendations)} recommendations")
        return recommendations

    def _calculate_recommendation_score(self, user_profile: UserProfile,
                                      scholarship: Scholarship,
                                      eligibility_score: float) -> float:
        """Calculate recommendation score based on various factors"""
        score = eligibility_score * 0.4  # Base eligibility weight

        # Field of study match bonus
        if (user_profile.field_of_study and
            user_profile.field_of_study in scholarship.eligibility_criteria.fields_of_study):
            score += 0.3

        # Amount factor (higher amounts get slight preference)
        if scholarship.amount >= 5000:
            score += 0.1
        elif scholarship.amount >= 1000:
            score += 0.05

        # Deadline factor (prefer scholarships with reasonable time to apply)
        from datetime import datetime
        days_until_deadline = (scholarship.application_deadline - datetime.utcnow()).days

        if 30 <= days_until_deadline <= 180:  # Sweet spot for application time
            score += 0.1
        elif 7 <= days_until_deadline < 30:  # Still time but urgent
            score += 0.05
        elif days_until_deadline < 7:  # Too urgent
            score -= 0.1

        # Scholarship type preferences (can be customized based on user profile)
        type_preferences = {
            "merit_based": 0.05,
            "need_based": 0.05 if user_profile.financial_need else 0.0,
            "academic_achievement": 0.05
        }

        if scholarship.scholarship_type.value in type_preferences:
            score += type_preferences[scholarship.scholarship_type.value]

        return min(1.0, max(0.0, score))

    def search_with_smart_suggestions(self, filters: SearchFilters) -> dict[str, Any]:
        """Enhanced search with smart suggestions"""
        # Get regular search results
        search_response = scholarship_service.search_scholarships(filters)

        # Generate smart suggestions based on search
        suggestions = self._generate_search_suggestions(filters, search_response.total_count)

        return {
            "results": search_response,
            "suggestions": suggestions,
            "search_metadata": {
                "filters_applied": self._get_applied_filters(filters),
                "search_quality": self._assess_search_quality(filters, search_response.total_count)
            }
        }

    def _generate_search_suggestions(self, filters: SearchFilters, result_count: int) -> list[str]:
        """Generate helpful search suggestions"""
        suggestions = []

        if result_count == 0:
            suggestions.append("Try broadening your search criteria")
            if filters.min_amount:
                suggestions.append("Consider lowering the minimum scholarship amount")
            if filters.fields_of_study:
                suggestions.append("Try removing or changing field of study filters")
            if filters.states:
                suggestions.append("Expand to include more states or remove location restrictions")

        elif result_count < 5:
            suggestions.append("Consider expanding your search criteria for more options")
            if filters.min_gpa:
                suggestions.append("Try lowering the minimum GPA requirement")

        elif result_count > 50:
            suggestions.append("Narrow your search for more targeted results")
            if not filters.fields_of_study:
                suggestions.append("Add field of study filters to focus results")
            if not filters.min_amount:
                suggestions.append("Set a minimum amount to filter by scholarship value")

        return suggestions

    def _get_applied_filters(self, filters: SearchFilters) -> list[str]:
        """Get list of applied filters for metadata"""
        applied = []

        if filters.keyword:
            applied.append(f"keyword: {filters.keyword}")
        if filters.fields_of_study:
            applied.append(f"fields_of_study: {[f.value for f in filters.fields_of_study]}")
        if filters.min_amount is not None:
            applied.append(f"min_amount: ${filters.min_amount}")
        if filters.max_amount is not None:
            applied.append(f"max_amount: ${filters.max_amount}")
        if filters.scholarship_types:
            applied.append(f"types: {[t.value for t in filters.scholarship_types]}")
        if filters.states:
            applied.append(f"states: {filters.states}")
        if filters.min_gpa is not None:
            applied.append(f"min_gpa: {filters.min_gpa}")

        return applied

    def _assess_search_quality(self, filters: SearchFilters, result_count: int) -> str:
        """Assess the quality of search results"""
        if result_count == 0:
            return "no_results"
        if result_count < 5:
            return "few_results"
        if result_count <= 20:
            return "good_results"
        if result_count <= 50:
            return "many_results"
        return "too_many_results"

# Global service instance
search_service = SearchService()
