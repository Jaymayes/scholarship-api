"""
Secure Scholarship Service - SQL Injection Prevention

This service layer implements secure data access patterns with:
- Parameterized queries only 
- Input validation and sanitization
- Comprehensive logging for security monitoring
- Defense-in-depth protection against SQL injection
"""

from typing import List, Optional, Dict, Any
from models.scholarship import Scholarship, ScholarshipSummary, SearchFilters, SearchResponse
from data.scholarships import MOCK_SCHOLARSHIPS
from database.secure_query_builder import get_secure_query_builder, SortField
from utils.logger import get_logger
import re

logger = get_logger(__name__)

class SecureScholarshipService:
    """
    Security-hardened scholarship service implementing comprehensive
    SQL injection prevention measures
    """
    
    def __init__(self):
        # Initialize with mock data - in production this would connect to secure database
        self.scholarships = {sch.id: sch for sch in MOCK_SCHOLARSHIPS}
        self._query_count = 0
        logger.info(f"Initialized SecureScholarshipService with {len(self.scholarships)} scholarships")
    
    def _sanitize_keyword(self, keyword: str) -> Optional[str]:
        """
        Sanitize search keywords to prevent injection attacks
        
        SECURITY FEATURES:
        - Remove SQL metacharacters
        - Validate input length and content
        - Log suspicious patterns
        """
        
        if not keyword or not keyword.strip():
            return None
        
        # Remove potential SQL injection characters
        keyword = keyword.strip()
        
        # Check for suspicious patterns
        sql_patterns = [
            r"('|('')|(\')|(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|EXEC)",
            r"(;|\||&|<|>|\*)",
            r"(\bOR\b|\bAND\b).*(\=|\<|\>)",
            r"(-{2,}|/\*|\*/)"
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, keyword, re.IGNORECASE):
                logger.warning(f"Suspicious keyword pattern detected and sanitized: {pattern}")
                # Remove the suspicious content
                keyword = re.sub(pattern, "", keyword, flags=re.IGNORECASE)
        
        # Limit keyword length to prevent buffer overflow attacks
        if len(keyword) > 100:
            logger.warning(f"Keyword truncated from {len(keyword)} to 100 characters")
            keyword = keyword[:100]
        
        # Final validation
        if not keyword.strip():
            return None
            
        return keyword.strip()
    
    def _validate_numeric_filters(self, min_amount: Optional[float], max_amount: Optional[float]) -> tuple:
        """
        Validate and sanitize numeric filter inputs
        
        SECURITY FEATURES:
        - Range validation to prevent overflow
        - Type coercion safety
        - Logical consistency checking
        """
        
        validated_min = None
        validated_max = None
        
        if min_amount is not None:
            try:
                validated_min = float(min_amount)
                if validated_min < 0:
                    logger.warning("Negative min_amount corrected to 0")
                    validated_min = 0.0
                elif validated_min > 1000000:  # Reasonable max scholarship amount
                    logger.warning("Min amount capped at $1M")
                    validated_min = 1000000.0
            except (ValueError, TypeError):
                logger.warning(f"Invalid min_amount ignored: {min_amount}")
                validated_min = None
        
        if max_amount is not None:
            try:
                validated_max = float(max_amount)
                if validated_max < 0:
                    logger.warning("Negative max_amount corrected to 0")
                    validated_max = 0.0
                elif validated_max > 1000000:  # Reasonable max scholarship amount  
                    logger.warning("Max amount capped at $1M")
                    validated_max = 1000000.0
            except (ValueError, TypeError):
                logger.warning(f"Invalid max_amount ignored: {max_amount}")
                validated_max = None
        
        # Logical validation
        if validated_min is not None and validated_max is not None:
            if validated_min > validated_max:
                logger.warning("min_amount > max_amount - swapping values")
                validated_min, validated_max = validated_max, validated_min
        
        return validated_min, validated_max
    
    def _validate_pagination(self, limit: int, offset: int) -> tuple:
        """
        Validate pagination parameters to prevent abuse
        
        SECURITY FEATURES:
        - Range limits to prevent resource exhaustion
        - Integer overflow protection
        - Performance impact mitigation
        """
        
        # Validate limit
        try:
            validated_limit = int(limit)
            if validated_limit < 1:
                validated_limit = 20
            elif validated_limit > 100:  # Prevent excessive resource usage
                logger.warning(f"Limit capped from {validated_limit} to 100")
                validated_limit = 100
        except (ValueError, TypeError):
            logger.warning(f"Invalid limit defaulted to 20: {limit}")
            validated_limit = 20
        
        # Validate offset
        try:
            validated_offset = int(offset)
            if validated_offset < 0:
                validated_offset = 0
            elif validated_offset > 100000:  # Prevent excessive pagination
                logger.warning(f"Offset capped from {validated_offset} to 100000")
                validated_offset = 100000
        except (ValueError, TypeError):
            logger.warning(f"Invalid offset defaulted to 0: {offset}")
            validated_offset = 0
        
        return validated_limit, validated_offset
    
    def secure_search_scholarships(self, filters: SearchFilters) -> SearchResponse:
        """
        Execute secure scholarship search with comprehensive protection
        
        SECURITY FEATURES:
        - All inputs validated and sanitized
        - No direct SQL construction from user input
        - Parameterized filtering with whitelisted fields
        - Comprehensive audit logging
        - Resource usage limits enforced
        """
        
        self._query_count += 1
        logger.info(f"Secure search initiated - Query #{self._query_count}")
        
        # SECURITY: Sanitize all inputs
        safe_keyword = self._sanitize_keyword(filters.keyword)
        safe_min, safe_max = self._validate_numeric_filters(filters.min_amount, filters.max_amount)
        safe_limit, safe_offset = self._validate_pagination(filters.limit, filters.offset)
        
        # Log security-relevant parameters
        logger.debug(f"Sanitized search params - keyword: {bool(safe_keyword)}, "
                    f"amount_range: [{safe_min}, {safe_max}], "
                    f"pagination: {safe_limit}/{safe_offset}")
        
        # Start with all scholarships (mock data - would be secure DB query in production)
        results = list(self.scholarships.values())
        
        # Apply secure keyword filtering
        if safe_keyword:
            keyword_lower = safe_keyword.lower()
            results = [
                sch for sch in results
                if (keyword_lower in sch.name.lower() or 
                    keyword_lower in sch.description.lower() or
                    keyword_lower in sch.organization.lower())
            ]
        
        # Apply validated numeric filters
        if safe_min is not None:
            results = [sch for sch in results if sch.amount >= safe_min]
        
        if safe_max is not None:
            results = [sch for sch in results if sch.amount <= safe_max]
        
        # Apply other validated filters
        if filters.fields_of_study:
            # Validate field of study values
            valid_fields = [field for field in filters.fields_of_study if isinstance(field, str) and len(field) < 50]
            if valid_fields:
                results = [
                    sch for sch in results
                    if any(field in sch.eligibility_criteria.fields_of_study 
                          for field in valid_fields)
                ]
        
        if filters.scholarship_types:
            # Validate scholarship type values  
            valid_types = [stype for stype in filters.scholarship_types if isinstance(stype, str) and len(stype) < 50]
            if valid_types:
                results = [
                    sch for sch in results
                    if sch.scholarship_type in valid_types
                ]
        
        # Calculate totals before pagination
        total_count = len(results)
        
        # Apply secure pagination
        start_idx = safe_offset
        end_idx = start_idx + safe_limit
        paginated_results = results[start_idx:end_idx]
        
        # Generate secure summaries
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
        
        # Generate secure response
        response = SearchResponse(
            scholarships=scholarship_summaries,
            total_count=total_count,
            page=(safe_offset // safe_limit) + 1,
            page_size=safe_limit,
            has_next=end_idx < total_count,
            has_previous=safe_offset > 0
        )
        
        # Security audit logging
        logger.info(f"Secure search completed - Query #{self._query_count}: "
                   f"{len(scholarship_summaries)} results out of {total_count} total")
        
        if safe_keyword != filters.keyword:
            logger.warning(f"Keyword was sanitized during search - original length: {len(filters.keyword or '')}")
        
        return response
    
    def get_scholarship_by_id(self, scholarship_id: str) -> Optional[Scholarship]:
        """
        Secure scholarship retrieval by ID with input validation
        
        SECURITY FEATURES:
        - ID format validation
        - Existence checking without information disclosure
        - Audit logging for access patterns
        """
        
        # Validate ID format
        if not scholarship_id or not isinstance(scholarship_id, str):
            logger.warning("Invalid scholarship ID format")
            return None
        
        # Limit ID length to prevent buffer attacks
        if len(scholarship_id) > 50:
            logger.warning(f"Scholarship ID truncated from {len(scholarship_id)} to 50")
            scholarship_id = scholarship_id[:50]
        
        # Remove potentially dangerous characters
        safe_id = re.sub(r"[^\w\-]", "", scholarship_id)
        
        if safe_id != scholarship_id:
            logger.warning("Scholarship ID was sanitized")
        
        # Secure lookup
        scholarship = self.scholarships.get(safe_id)
        
        if scholarship:
            logger.info(f"Scholarship retrieved: {safe_id}")
        else:
            logger.info(f"Scholarship not found: {safe_id}")
        
        return scholarship

# Global secure service instance
secure_scholarship_service = SecureScholarshipService()