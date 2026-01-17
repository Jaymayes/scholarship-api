"""
Scholarship Service - Database-Backed Real-Time Data
SRE DIRECTIVE: Zero-Staleness - All data from Production Database
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from models.database import ScholarshipDB, SessionLocal
from models.scholarship import (
    EligibilityCriteria,
    FieldOfStudy,
    Scholarship,
    ScholarshipSummary,
    ScholarshipType,
    SearchFilters,
    SearchResponse,
)
from utils.logger import get_logger

logger = get_logger(__name__)


def get_db_session() -> Session:
    """Get a database session"""
    return SessionLocal()


class ScholarshipService:
    """
    Service for managing scholarship operations.
    SRE DIRECTIVE: All data sourced from Production Database.
    No in-memory caching. No mock data fallback.
    """

    def __init__(self):
        logger.info("ScholarshipService initialized - Database-backed mode (Zero-Staleness)")
        self._update_metrics()

    def get_scholarship_count(self) -> int:
        """Get count of active scholarships from database"""
        db = get_db_session()
        try:
            count = db.query(ScholarshipDB).filter(ScholarshipDB.is_active == True).count()
            return count
        except Exception as e:
            logger.error(f"Database error getting scholarship count: {str(e)}")
            return 0
        finally:
            db.close()

    def _update_metrics(self):
        """Update scholarship count metrics from database"""
        try:
            db = get_db_session()
            try:
                count = db.query(ScholarshipDB).filter(ScholarshipDB.is_active == True).count()
                from observability.metrics import metrics_service
                metrics_service.update_scholarship_count(count)
                logger.info(f"Updated active_scholarships_total metric to {count}")
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"Failed to update scholarship metrics: {str(e)}")

    def _db_to_scholarship(self, db_sch: ScholarshipDB) -> Scholarship:
        """Convert database model to Pydantic model"""
        eligibility_data = db_sch.eligibility_criteria or {}
        
        fields = []
        for field_name in eligibility_data.get("fields_of_study", []):
            try:
                fields.append(FieldOfStudy(field_name))
            except ValueError:
                pass
        
        eligibility = EligibilityCriteria(
            min_gpa=eligibility_data.get("min_gpa"),
            max_gpa=eligibility_data.get("max_gpa"),
            grade_levels=eligibility_data.get("grade_levels", []),
            citizenship_required=eligibility_data.get("citizenship_required"),
            residency_states=eligibility_data.get("residency_states", []),
            min_age=eligibility_data.get("min_age"),
            max_age=eligibility_data.get("max_age"),
            financial_need=eligibility_data.get("financial_need"),
            fields_of_study=fields,
            essay_required=eligibility_data.get("essay_required", False),
            recommendation_letters=eligibility_data.get("recommendation_letters", 0)
        )
        
        try:
            sch_type = ScholarshipType(db_sch.scholarship_type)
        except ValueError:
            sch_type = ScholarshipType.MERIT_BASED
        
        return Scholarship(
            id=db_sch.id,
            name=db_sch.name,
            organization=db_sch.organization,
            description=db_sch.description,
            amount=db_sch.amount,
            max_awards=db_sch.max_awards if db_sch.max_awards is not None else 1,
            application_deadline=db_sch.application_deadline,
            notification_date=db_sch.notification_date,
            scholarship_type=sch_type,
            eligibility_criteria=eligibility,
            application_url=db_sch.application_url if db_sch.application_url is not None else "",
            contact_email=db_sch.contact_email if db_sch.contact_email is not None else "",
            renewable=db_sch.renewable or False
        )

    def get_scholarship_by_id(self, scholarship_id: str) -> Scholarship | None:
        """Get a specific scholarship by ID from database"""
        db = get_db_session()
        try:
            db_sch = db.query(ScholarshipDB).filter(
                ScholarshipDB.id == scholarship_id,
                ScholarshipDB.is_active == True
            ).first()
            
            if db_sch:
                logger.info(f"Retrieved scholarship from DB: {scholarship_id}")
                return self._db_to_scholarship(db_sch)
            else:
                logger.warning(f"Scholarship not found in DB: {scholarship_id}")
                return None
        except Exception as e:
            logger.error(f"Database error retrieving scholarship {scholarship_id}: {str(e)}")
            raise
        finally:
            db.close()

    def get_all_scholarships(self) -> list[Scholarship]:
        """Get all active scholarships from database"""
        db = get_db_session()
        try:
            db_scholarships = db.query(ScholarshipDB).filter(
                ScholarshipDB.is_active == True
            ).order_by(desc(ScholarshipDB.application_deadline)).all()
            
            result = [self._db_to_scholarship(sch) for sch in db_scholarships]
            logger.info(f"Retrieved {len(result)} scholarships from database")
            return result
        except Exception as e:
            logger.error(f"Database error retrieving all scholarships: {str(e)}")
            raise
        finally:
            db.close()

    def search_scholarships(self, filters: SearchFilters) -> SearchResponse:
        """Search scholarships with filters - queries database directly"""
        logger.info(f"Searching scholarships with filters: {filters}")
        db = get_db_session()
        
        try:
            query = db.query(ScholarshipDB).filter(ScholarshipDB.is_active == True)
            
            if filters.keyword:
                keyword_filter = or_(
                    ScholarshipDB.name.ilike(f"%{filters.keyword}%"),
                    ScholarshipDB.description.ilike(f"%{filters.keyword}%"),
                    ScholarshipDB.organization.ilike(f"%{filters.keyword}%")
                )
                query = query.filter(keyword_filter)
            
            if filters.min_amount is not None:
                query = query.filter(ScholarshipDB.amount >= filters.min_amount)
            
            if filters.max_amount is not None:
                query = query.filter(ScholarshipDB.amount <= filters.max_amount)
            
            if filters.scholarship_types:
                type_values = [t.value if hasattr(t, 'value') else str(t) for t in filters.scholarship_types]
                query = query.filter(ScholarshipDB.scholarship_type.in_(type_values))
            
            if filters.deadline_after:
                query = query.filter(ScholarshipDB.application_deadline >= filters.deadline_after)
            
            if filters.deadline_before:
                query = query.filter(ScholarshipDB.application_deadline <= filters.deadline_before)
            
            total_count = query.count()
            
            db_scholarships = query.order_by(
                ScholarshipDB.application_deadline
            ).offset(filters.offset).limit(filters.limit).all()
            
            scholarships = [self._db_to_scholarship(sch) for sch in db_scholarships]
            
            if filters.fields_of_study:
                scholarships = [
                    sch for sch in scholarships
                    if any(field in sch.eligibility_criteria.fields_of_study
                          for field in filters.fields_of_study)
                ]
            
            if filters.states:
                scholarships = [
                    sch for sch in scholarships
                    if (any(state in (sch.eligibility_criteria.residency_states or [])
                          for state in filters.states) or
                       not sch.eligibility_criteria.residency_states)
                ]
            
            if filters.min_gpa is not None:
                scholarships = [
                    sch for sch in scholarships
                    if (sch.eligibility_criteria.min_gpa is None or
                        filters.min_gpa >= sch.eligibility_criteria.min_gpa)
                ]
            
            if filters.citizenship:
                scholarships = [
                    sch for sch in scholarships
                    if (sch.eligibility_criteria.citizenship_required is None or
                        sch.eligibility_criteria.citizenship_required == filters.citizenship)
                ]
            
            page_size = filters.limit
            page = (filters.offset // page_size) + 1
            
            scholarship_summaries = [
                ScholarshipSummary(
                    id=sch.id,
                    name=sch.name,
                    organization=sch.organization,
                    amount=sch.amount,
                    application_deadline=sch.application_deadline,
                    scholarship_type=sch.scholarship_type,
                    description=sch.description[:197] + "..." if len(sch.description) > 200 else sch.description,
                    eligibility_criteria=sch.eligibility_criteria
                )
                for sch in scholarships
            ]
            
            has_next = (filters.offset + filters.limit) < total_count
            has_previous = filters.offset > 0
            
            response = SearchResponse(
                scholarships=scholarship_summaries,
                total_count=total_count,
                page=page,
                page_size=page_size,
                has_next=has_next,
                has_previous=has_previous
            )
            
            logger.info(f"Database search completed: {len(scholarship_summaries)} results out of {total_count} total")
            return response
            
        except Exception as e:
            logger.error(f"Database error during search: {str(e)}")
            raise
        finally:
            db.close()

    def get_scholarships_by_organization(self, organization: str) -> list[Scholarship]:
        """Get scholarships by organization from database"""
        db = get_db_session()
        try:
            db_scholarships = db.query(ScholarshipDB).filter(
                ScholarshipDB.is_active == True,
                ScholarshipDB.organization.ilike(f"%{organization}%")
            ).all()
            
            results = [self._db_to_scholarship(sch) for sch in db_scholarships]
            logger.info(f"Found {len(results)} scholarships for organization: {organization}")
            return results
        except Exception as e:
            logger.error(f"Database error for organization search: {str(e)}")
            raise
        finally:
            db.close()


scholarship_service = ScholarshipService()
