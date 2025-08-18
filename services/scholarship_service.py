from typing import List, Optional
from models.scholarship import Scholarship, ScholarshipSummary, SearchFilters, SearchResponse
from data.scholarships import MOCK_SCHOLARSHIPS
from utils.logger import get_logger

logger = get_logger(__name__)

class ScholarshipService:
    """Service for managing scholarship operations"""
    
    def __init__(self):
        self.scholarships = {sch.id: sch for sch in MOCK_SCHOLARSHIPS}
        logger.info(f"Initialized ScholarshipService with {len(self.scholarships)} scholarships")
    
    def get_scholarship_by_id(self, scholarship_id: str) -> Optional[Scholarship]:
        """Get a specific scholarship by ID"""
        scholarship = self.scholarships.get(scholarship_id)
        if scholarship:
            logger.info(f"Retrieved scholarship: {scholarship_id}")
        else:
            logger.warning(f"Scholarship not found: {scholarship_id}")
        return scholarship
    
    def get_all_scholarships(self) -> List[Scholarship]:
        """Get all scholarships"""
        logger.info("Retrieved all scholarships")
        return list(self.scholarships.values())
    
    def search_scholarships(self, filters: SearchFilters) -> SearchResponse:
        """Search scholarships with filters"""
        logger.info(f"Searching scholarships with filters: {filters}")
        
        # Start with all scholarships
        results = list(self.scholarships.values())
        
        # Apply keyword filter
        if filters.keyword:
            keyword_lower = filters.keyword.lower()
            results = [
                sch for sch in results
                if (keyword_lower in sch.name.lower() or 
                    keyword_lower in sch.description.lower() or
                    keyword_lower in sch.organization.lower())
            ]
        
        # Apply field of study filter
        if filters.fields_of_study:
            results = [
                sch for sch in results
                if any(field in sch.eligibility_criteria.fields_of_study 
                      for field in filters.fields_of_study)
            ]
        
        # Apply amount filters
        if filters.min_amount is not None:
            results = [sch for sch in results if sch.amount >= filters.min_amount]
        
        if filters.max_amount is not None:
            results = [sch for sch in results if sch.amount <= filters.max_amount]
        
        # Apply scholarship type filter
        if filters.scholarship_types:
            results = [
                sch for sch in results
                if sch.scholarship_type in filters.scholarship_types
            ]
        
        # Apply state filter
        if filters.states:
            results = [
                sch for sch in results
                if any(state in sch.eligibility_criteria.residency_states 
                      for state in filters.states) or
                not sch.eligibility_criteria.residency_states  # No state restriction
            ]
        
        # Apply GPA filter - user qualifies if they meet or exceed scholarship requirement
        if filters.min_gpa is not None:
            results = [
                sch for sch in results
                if (sch.eligibility_criteria.min_gpa is None or 
                    filters.min_gpa >= sch.eligibility_criteria.min_gpa)
            ]
        
        # Apply citizenship filter
        if filters.citizenship:
            results = [
                sch for sch in results
                if (sch.eligibility_criteria.citizenship_required is None or
                    sch.eligibility_criteria.citizenship_required == filters.citizenship)
            ]
        
        # Apply deadline filters
        if filters.deadline_after:
            results = [sch for sch in results if sch.application_deadline >= filters.deadline_after]
        
        if filters.deadline_before:
            results = [sch for sch in results if sch.application_deadline <= filters.deadline_before]
        
        # Sort by deadline (earliest first)
        results.sort(key=lambda x: x.application_deadline)
        
        # Calculate pagination
        total_count = len(results)
        page_size = filters.limit
        page = (filters.offset // page_size) + 1
        
        # Apply pagination
        start_idx = filters.offset
        end_idx = start_idx + filters.limit
        paginated_results = results[start_idx:end_idx]
        
        # Convert to summary format
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
            for sch in paginated_results
        ]
        
        response = SearchResponse(
            scholarships=scholarship_summaries,
            total_count=total_count,
            page=page,
            page_size=page_size,
            has_next=end_idx < total_count,
            has_previous=filters.offset > 0
        )
        
        logger.info(f"Search completed: {len(scholarship_summaries)} results out of {total_count} total")
        return response
    
    def get_scholarships_by_organization(self, organization: str) -> List[Scholarship]:
        """Get scholarships by organization"""
        results = [
            sch for sch in self.scholarships.values()
            if organization.lower() in sch.organization.lower()
        ]
        logger.info(f"Found {len(results)} scholarships for organization: {organization}")
        return results

# Global service instance
scholarship_service = ScholarshipService()
