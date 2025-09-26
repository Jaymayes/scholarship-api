
from fastapi import APIRouter, Depends, HTTPException, Query

from middleware.auth import User, require_admin
from services.analytics_service import analytics_service
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

@router.get("/analytics/summary")
async def get_analytics_summary(
    days: int = Query(7, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(require_admin())
):
    """
    Get analytics summary for the specified time period.

    Provides insights into user interactions, search patterns, and
    scholarship engagement metrics.
    """
    try:
        return analytics_service.get_analytics_summary(days)

    except Exception as e:
        logger.error(f"Error generating analytics summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Error generating analytics summary")

@router.get("/analytics/user/{user_id}")
async def get_user_analytics(
    user_id: str,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(require_admin())
):
    """
    Get analytics for a specific user.

    Returns detailed activity history and engagement patterns
    for the specified user.
    """
    try:
        return analytics_service.get_user_analytics(user_id, days)

    except Exception as e:
        logger.error(f"Error generating user analytics for {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error generating user analytics")

@router.get("/analytics/interactions")
async def get_recent_interactions(
    limit: int = Query(50, ge=1, le=200, description="Number of interactions to return"),
    action: str | None = Query(None, description="Filter by interaction type"),
    current_user: User = Depends(require_admin())
):
    """
    Get recent user interactions with optional filtering.

    Returns a list of recent user interactions, optionally filtered
    by interaction type (search, view_scholarship, etc.).
    """
    try:
        interactions = analytics_service.interactions

        # Filter by action if specified
        if action:
            interactions = [i for i in interactions if i.action == action]

        # Sort by timestamp (most recent first)
        interactions.sort(key=lambda x: x.timestamp, reverse=True)

        # Apply limit
        interactions = interactions[:limit]

        # Convert to dict format for JSON response
        interaction_dicts = []
        for interaction in interactions:
            interaction_dict = {
                "user_id": interaction.user_id,
                "action": interaction.action,
                "scholarship_id": interaction.scholarship_id,
                "timestamp": interaction.timestamp,
                "metadata": interaction.metadata
            }
            interaction_dicts.append(interaction_dict)

        return {
            "interactions": interaction_dicts,
            "total_returned": len(interaction_dicts),
            "filtered_by_action": action
        }

    except Exception as e:
        logger.error(f"Error retrieving interactions: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving interactions")

@router.get("/analytics/popular-scholarships")
async def get_popular_scholarships(
    days: int = Query(7, ge=1, le=365, description="Number of days to analyze"),
    limit: int = Query(10, ge=1, le=50, description="Number of scholarships to return")
):
    """
    Get most popular scholarships based on view count.

    Returns scholarships ordered by popularity (view count) within
    the specified time period.
    """
    try:
        from collections import Counter
        from datetime import datetime, timedelta

        from services.scholarship_service import scholarship_service

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Get scholarship views within time period
        scholarship_views = [
            i for i in analytics_service.interactions
            if (i.action == "view_scholarship" and
                i.scholarship_id and
                i.timestamp >= cutoff_date)
        ]

        # Count views per scholarship
        view_counts = Counter(i.scholarship_id for i in scholarship_views)

        # Get top scholarships with details
        popular_scholarships = []
        for scholarship_id, view_count in view_counts.most_common(limit):
            if scholarship_id:  # Check if scholarship_id is not None
                scholarship = scholarship_service.get_scholarship_by_id(scholarship_id)
                if scholarship:
                    popular_scholarships.append({
                        "scholarship": {
                            "id": scholarship.id,
                            "name": scholarship.name,
                            "organization": scholarship.organization,
                            "amount": scholarship.amount,
                            "application_deadline": scholarship.application_deadline,
                            "scholarship_type": scholarship.scholarship_type
                        },
                        "view_count": view_count,
                        "popularity_rank": len(popular_scholarships) + 1
                    })

        return {
            "period_days": days,
            "popular_scholarships": popular_scholarships,
            "total_scholarship_views": len(scholarship_views),
            "unique_scholarships_viewed": len(view_counts)
        }

    except Exception as e:
        logger.error(f"Error retrieving popular scholarships: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving popular scholarships")

@router.get("/analytics/search-trends")
async def get_search_trends(
    days: int = Query(7, ge=1, le=365, description="Number of days to analyze")
):
    """
    Get search trends and patterns.

    Analyzes search queries, filters used, and search success rates
    to identify trends in user behavior.
    """
    try:
        from collections import Counter
        from datetime import datetime, timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Get search interactions within time period
        search_interactions = [
            i for i in analytics_service.interactions
            if (i.action == "search" and i.timestamp >= cutoff_date)
        ]

        # Analyze search queries
        search_queries = []
        zero_result_searches = 0
        total_results = 0

        for interaction in search_interactions:
            if interaction.metadata:
                query = interaction.metadata.get("query", "").strip()
                result_count = interaction.metadata.get("result_count", 0)

                if query:  # Non-empty query
                    search_queries.append(query.lower())

                if result_count == 0:
                    zero_result_searches += 1

                total_results += result_count

        # Calculate metrics
        popular_queries = dict(Counter(search_queries).most_common(15))
        avg_results_per_search = total_results / len(search_interactions) if search_interactions else 0
        zero_result_rate = zero_result_searches / len(search_interactions) if search_interactions else 0

        # Analyze search filters usage (simplified)
        filter_usage = Counter()
        for interaction in search_interactions:
            if interaction.metadata and "filters" in interaction.metadata:
                filters = interaction.metadata["filters"]
                for key, value in filters.items():
                    if value and key != "limit" and key != "offset":  # Skip pagination params
                        if isinstance(value, list) and value or not isinstance(value, list) and value is not None:
                            filter_usage[key] += 1

        return {
            "period_days": days,
            "search_statistics": {
                "total_searches": len(search_interactions),
                "unique_queries": len(set(search_queries)),
                "avg_results_per_search": round(avg_results_per_search, 2),
                "zero_result_rate": round(zero_result_rate, 2),
                "zero_result_searches": zero_result_searches
            },
            "popular_queries": popular_queries,
            "filter_usage": dict(filter_usage.most_common(10)),
            "search_quality_insights": [
                f"{zero_result_rate:.1%} of searches returned no results" if zero_result_rate > 0 else "All searches returned results",
                f"Average of {avg_results_per_search:.1f} results per search",
                f"Top query: '{list(popular_queries.keys())[0]}'" if popular_queries else "No queries with keywords"
            ]
        }

    except Exception as e:
        logger.error(f"Error analyzing search trends: {str(e)}")
        raise HTTPException(status_code=500, detail="Error analyzing search trends")
