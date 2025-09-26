"""
Database Service Layer
Handles database operations and data persistence
"""

from datetime import datetime
from typing import Any

from sqlalchemy import and_, desc, or_
from sqlalchemy.orm import Session

# Import types for type hints only
# from models.scholarship import Scholarship
# from models.user import UserProfile, UserInteraction
from data.scholarships import MOCK_SCHOLARSHIPS
from models.database import (
    ScholarshipDB,
    SearchAnalyticsDB,
    UserInteractionDB,
)
from utils.logger import get_logger

logger = get_logger("database_service")

class DatabaseService:
    """Service for database operations"""

    def __init__(self, db_session: Session):
        self.db = db_session

    def migrate_mock_data(self):
        """Migrate mock scholarship data to database"""
        try:
            # Check if data already exists
            existing_count = self.db.query(ScholarshipDB).count()
            if existing_count > 0:
                logger.info(f"Database already contains {existing_count} scholarships")
                return existing_count

            # Insert mock scholarships
            inserted_count = 0
            for mock_scholarship in MOCK_SCHOLARSHIPS:
                db_scholarship = ScholarshipDB(
                    id=mock_scholarship.id,
                    name=mock_scholarship.name,
                    organization=mock_scholarship.organization,
                    description=mock_scholarship.description,
                    amount=mock_scholarship.amount,
                    max_awards=mock_scholarship.max_awards,
                    application_deadline=mock_scholarship.application_deadline,
                    notification_date=mock_scholarship.notification_date,
                    scholarship_type=mock_scholarship.scholarship_type.value,
                    application_url=mock_scholarship.application_url,
                    contact_email=mock_scholarship.contact_email,
                    renewable=mock_scholarship.renewable,
                    eligibility_criteria=mock_scholarship.eligibility_criteria.dict()
                )
                self.db.add(db_scholarship)
                inserted_count += 1

            self.db.commit()
            logger.info(f"Successfully migrated {inserted_count} scholarships to database")
            return inserted_count

        except Exception as e:
            logger.error(f"Error migrating mock data: {str(e)}")
            self.db.rollback()
            raise

    def get_scholarships(
        self,
        keyword: str | None = None,
        fields_of_study: list[str] = None,
        min_amount: float | None = None,
        max_amount: float | None = None,
        scholarship_types: list[str] = None,
        states: list[str] = None,
        min_gpa: float | None = None,
        citizenship: str | None = None,
        deadline_after: datetime | None = None,
        deadline_before: datetime | None = None,
        limit: int = 20,
        offset: int = 0
    ) -> dict[str, Any]:
        """Get scholarships with filtering and pagination"""
        try:
            query = self.db.query(ScholarshipDB).filter(ScholarshipDB.is_active)

            # Apply filters
            if keyword:
                keyword_filter = or_(
                    ScholarshipDB.name.ilike(f"%{keyword}%"),
                    ScholarshipDB.description.ilike(f"%{keyword}%"),
                    ScholarshipDB.organization.ilike(f"%{keyword}%")
                )
                query = query.filter(keyword_filter)

            if min_amount:
                query = query.filter(ScholarshipDB.amount >= min_amount)

            if max_amount:
                query = query.filter(ScholarshipDB.amount <= max_amount)

            if scholarship_types:
                query = query.filter(ScholarshipDB.scholarship_type.in_(scholarship_types))

            if deadline_after:
                query = query.filter(ScholarshipDB.application_deadline >= deadline_after)

            if deadline_before:
                query = query.filter(ScholarshipDB.application_deadline <= deadline_before)

            # Additional filtering would require JSON queries for eligibility_criteria
            # This is simplified for the initial implementation

            # Get total count
            total_count = query.count()

            # Apply pagination and ordering
            scholarships = query.order_by(desc(ScholarshipDB.amount)).offset(offset).limit(limit).all()

            # Convert to response format
            scholarship_list = []
            for db_scholarship in scholarships:
                scholarship_dict = {
                    "id": db_scholarship.id,
                    "name": db_scholarship.name,
                    "organization": db_scholarship.organization,
                    "description": db_scholarship.description,
                    "amount": db_scholarship.amount,
                    "max_awards": db_scholarship.max_awards,
                    "application_deadline": db_scholarship.application_deadline.isoformat(),
                    "notification_date": db_scholarship.notification_date.isoformat() if db_scholarship.notification_date else None,
                    "scholarship_type": db_scholarship.scholarship_type,
                    "application_url": db_scholarship.application_url,
                    "contact_email": db_scholarship.contact_email,
                    "renewable": db_scholarship.renewable,
                    "eligibility_criteria": db_scholarship.eligibility_criteria
                }
                scholarship_list.append(scholarship_dict)

            return {
                "scholarships": scholarship_list,
                "total_count": total_count,
                "page": (offset // limit) + 1,
                "page_size": limit,
                "has_next": offset + limit < total_count,
                "has_previous": offset > 0
            }

        except Exception as e:
            logger.error(f"Error retrieving scholarships: {str(e)}")
            raise

    def get_scholarship_by_id(self, scholarship_id: str) -> dict[str, Any] | None:
        """Get a specific scholarship by ID"""
        try:
            db_scholarship = self.db.query(ScholarshipDB).filter(
                and_(ScholarshipDB.id == scholarship_id, ScholarshipDB.is_active)
            ).first()

            if not db_scholarship:
                return None

            return {
                "id": db_scholarship.id,
                "name": db_scholarship.name,
                "organization": db_scholarship.organization,
                "description": db_scholarship.description,
                "amount": db_scholarship.amount,
                "max_awards": db_scholarship.max_awards,
                "application_deadline": db_scholarship.application_deadline.isoformat(),
                "notification_date": db_scholarship.notification_date.isoformat() if db_scholarship.notification_date else None,
                "scholarship_type": db_scholarship.scholarship_type,
                "application_url": db_scholarship.application_url,
                "contact_email": db_scholarship.contact_email,
                "renewable": db_scholarship.renewable,
                "eligibility_criteria": db_scholarship.eligibility_criteria,
                "created_at": db_scholarship.created_at.isoformat(),
                "updated_at": db_scholarship.updated_at.isoformat()
            }

        except Exception as e:
            logger.error(f"Error retrieving scholarship {scholarship_id}: {str(e)}")
            raise

    def log_user_interaction(
        self,
        user_id: str | None,
        scholarship_id: str,
        interaction_type: str,
        search_query: str | None = None,
        filters_applied: dict | None = None,
        match_score: float | None = None,
        position_in_results: int | None = None,
        session_id: str | None = None,
        source: str = "direct"
    ) -> str:
        """Log user interaction with scholarship"""
        try:
            interaction = UserInteractionDB(
                user_id=user_id or "anonymous",
                scholarship_id=scholarship_id,
                interaction_type=interaction_type,
                search_query=search_query,
                filters_applied=filters_applied or {},
                match_score=match_score,
                position_in_results=position_in_results,
                session_id=session_id,
                source=source
            )

            self.db.add(interaction)
            self.db.commit()

            logger.info(f"Logged {interaction_type} interaction for scholarship {scholarship_id}")
            return interaction.id

        except Exception as e:
            logger.error(f"Error logging interaction: {str(e)}")
            self.db.rollback()
            raise

    def log_search_analytics(
        self,
        search_query: str | None,
        filters_applied: dict,
        results_count: int,
        user_id: str | None = None,
        response_time_ms: float | None = None,
        session_id: str | None = None,
        user_agent: str | None = None,
        ip_address: str | None = None
    ) -> str:
        """Log search analytics"""
        try:
            analytics = SearchAnalyticsDB(
                search_query=search_query,
                filters_applied=filters_applied,
                results_count=results_count,
                user_id=user_id,
                response_time_ms=response_time_ms,
                session_id=session_id,
                user_agent=user_agent,
                ip_address=ip_address
            )

            self.db.add(analytics)
            self.db.commit()

            return analytics.id

        except Exception as e:
            logger.error(f"Error logging search analytics: {str(e)}")
            self.db.rollback()
            raise

    def get_popular_scholarships(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get most popular scholarships based on interactions"""
        try:
            # Query scholarships with most interactions
            popular_query = (
                self.db.query(ScholarshipDB, self.db.func.count(UserInteractionDB.id).label('interaction_count'))
                .join(UserInteractionDB, ScholarshipDB.id == UserInteractionDB.scholarship_id)
                .filter(ScholarshipDB.is_active)
                .group_by(ScholarshipDB.id)
                .order_by(desc('interaction_count'))
                .limit(limit)
            )

            results = []
            for scholarship, interaction_count in popular_query.all():
                results.append({
                    "scholarship": {
                        "id": scholarship.id,
                        "name": scholarship.name,
                        "organization": scholarship.organization,
                        "amount": scholarship.amount,
                        "application_deadline": scholarship.application_deadline.isoformat()
                    },
                    "interaction_count": interaction_count
                })

            return results

        except Exception as e:
            logger.error(f"Error getting popular scholarships: {str(e)}")
            raise

    def get_analytics_summary(self) -> dict[str, Any]:
        """Get overall analytics summary"""
        try:
            total_scholarships = self.db.query(ScholarshipDB).filter(ScholarshipDB.is_active).count()
            total_interactions = self.db.query(UserInteractionDB).count()
            total_searches = self.db.query(SearchAnalyticsDB).count()

            # Recent activity (last 7 days)
            week_ago = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            recent_interactions = (
                self.db.query(UserInteractionDB)
                .filter(UserInteractionDB.timestamp >= week_ago)
                .count()
            )

            recent_searches = (
                self.db.query(SearchAnalyticsDB)
                .filter(SearchAnalyticsDB.timestamp >= week_ago)
                .count()
            )

            return {
                "total_scholarships": total_scholarships,
                "total_interactions": total_interactions,
                "total_searches": total_searches,
                "recent_interactions_7_days": recent_interactions,
                "recent_searches_7_days": recent_searches,
                "average_interactions_per_scholarship": total_interactions / total_scholarships if total_scholarships > 0 else 0
            }

        except Exception as e:
            logger.error(f"Error getting analytics summary: {str(e)}")
            raise
