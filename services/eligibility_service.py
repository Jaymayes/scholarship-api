
from models.scholarship import Scholarship
from models.user import EligibilityResult, UserProfile
from services.scholarship_service import scholarship_service
from utils.logger import get_logger

logger = get_logger(__name__)

class EligibilityService:
    """Service for checking scholarship eligibility"""

    def check_eligibility(self, user_profile: UserProfile, scholarship_id: str) -> EligibilityResult:
        """Check if user is eligible for a specific scholarship"""
        logger.info(f"Checking eligibility for user {user_profile.id} and scholarship {scholarship_id}")

        scholarship = scholarship_service.get_scholarship_by_id(scholarship_id)
        if not scholarship:
            return EligibilityResult(
                scholarship_id=scholarship_id,
                eligible=False,
                reasons=["Scholarship not found"],
                match_score=0.0
            )

        return self._evaluate_eligibility(user_profile, scholarship)

    def check_multiple_eligibilities(self, user_profile: UserProfile,
                                   scholarship_ids: list[str]) -> list[EligibilityResult]:
        """Check eligibility for multiple scholarships"""
        results = []
        for scholarship_id in scholarship_ids:
            result = self.check_eligibility(user_profile, scholarship_id)
            results.append(result)

        logger.info(f"Checked eligibility for {len(scholarship_ids)} scholarships")
        return results

    def get_eligible_scholarships(self, user_profile: UserProfile,
                                min_match_score: float = 0.7) -> list[EligibilityResult]:
        """Get all scholarships user is eligible for"""
        all_scholarships = scholarship_service.get_all_scholarships()
        eligible_results = []

        for scholarship in all_scholarships:
            result = self._evaluate_eligibility(user_profile, scholarship)
            if result.eligible and result.match_score >= min_match_score:
                eligible_results.append(result)

        # Sort by match score (highest first)
        eligible_results.sort(key=lambda x: x.match_score, reverse=True)

        logger.info(f"Found {len(eligible_results)} eligible scholarships for user")
        return eligible_results

    def _evaluate_eligibility(self, user_profile: UserProfile,
                            scholarship: Scholarship) -> EligibilityResult:
        """Evaluate user eligibility for a scholarship"""
        criteria = scholarship.eligibility_criteria
        reasons = []
        match_score = 1.0
        eligible = True

        # Check GPA requirements
        if criteria.min_gpa is not None:
            if user_profile.gpa is None:
                reasons.append("GPA information required")
                match_score -= 0.3
            elif user_profile.gpa < criteria.min_gpa:
                reasons.append(f"GPA too low (required: {criteria.min_gpa}, yours: {user_profile.gpa})")
                eligible = False
                match_score -= 0.4

        if criteria.max_gpa is not None:
            if user_profile.gpa is not None and user_profile.gpa > criteria.max_gpa:
                reasons.append(f"GPA too high (maximum: {criteria.max_gpa}, yours: {user_profile.gpa})")
                eligible = False
                match_score -= 0.4

        # Check grade level requirements
        if criteria.grade_levels:
            if user_profile.grade_level is None:
                reasons.append("Grade level information required")
                match_score -= 0.2
            elif user_profile.grade_level not in criteria.grade_levels:
                reasons.append(f"Grade level not eligible (required: {', '.join(criteria.grade_levels)})")
                eligible = False
                match_score -= 0.3

        # Check citizenship requirements
        if criteria.citizenship_required:
            if user_profile.citizenship is None:
                reasons.append("Citizenship information required")
                match_score -= 0.2
            elif user_profile.citizenship != criteria.citizenship_required:
                reasons.append(f"Citizenship requirement not met (required: {criteria.citizenship_required})")
                eligible = False
                match_score -= 0.4

        # Check residency state requirements
        if criteria.residency_states:
            if user_profile.state_of_residence is None:
                reasons.append("State of residence information required")
                match_score -= 0.2
            elif user_profile.state_of_residence not in criteria.residency_states:
                reasons.append(f"State of residence not eligible (eligible states: {', '.join(criteria.residency_states)})")
                eligible = False
                match_score -= 0.3

        # Check field of study requirements
        if criteria.fields_of_study:
            if user_profile.field_of_study is None:
                reasons.append("Field of study information required")
                match_score -= 0.2
            elif user_profile.field_of_study not in criteria.fields_of_study:
                reasons.append(f"Field of study not eligible (eligible fields: {', '.join([f.value for f in criteria.fields_of_study])})")
                eligible = False
                match_score -= 0.3

        # Check age requirements
        if criteria.min_age is not None:
            if user_profile.age is None:
                reasons.append("Age information required")
                match_score -= 0.1
            elif user_profile.age < criteria.min_age:
                reasons.append(f"Age too young (minimum: {criteria.min_age})")
                eligible = False
                match_score -= 0.2

        if criteria.max_age is not None:
            if user_profile.age is not None and user_profile.age > criteria.max_age:
                reasons.append(f"Age too old (maximum: {criteria.max_age})")
                eligible = False
                match_score -= 0.2

        # Check financial need requirements
        if criteria.financial_need is not None:
            if user_profile.financial_need is None:
                reasons.append("Financial need information required")
                match_score -= 0.1
            elif criteria.financial_need and not user_profile.financial_need:
                reasons.append("Financial need requirement not met")
                eligible = False
                match_score -= 0.2

        # Ensure match_score is within bounds
        match_score = max(0.0, min(1.0, match_score))

        # If eligible, add positive reasons
        if eligible and not reasons:
            reasons.append("All eligibility criteria met")

        return EligibilityResult(
            scholarship_id=scholarship.id,
            eligible=eligible,
            reasons=reasons,
            match_score=match_score
        )

# Global service instance
eligibility_service = EligibilityService()
