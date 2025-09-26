# AI Scholarship Playbook - Predictive Matching Models
# "Likelihood to win" scoring and intelligent matching

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class CompetitionLevel(str, Enum):
    """Competition level categories"""
    VERY_LOW = "very_low"      # <50 applicants
    LOW = "low"                # 50-200 applicants
    MEDIUM = "medium"          # 200-500 applicants
    HIGH = "high"              # 500-1000 applicants
    VERY_HIGH = "very_high"    # 1000+ applicants

class MatchConfidence(str, Enum):
    """Confidence level in match prediction"""
    VERY_HIGH = "very_high"    # 90%+ confidence
    HIGH = "high"              # 75-90% confidence
    MEDIUM = "medium"          # 50-75% confidence
    LOW = "low"                # 25-50% confidence
    VERY_LOW = "very_low"      # <25% confidence

class EligibilityStatus(str, Enum):
    """Detailed eligibility status"""
    FULLY_ELIGIBLE = "fully_eligible"
    MOSTLY_ELIGIBLE = "mostly_eligible"  # Minor gaps
    PARTIALLY_ELIGIBLE = "partially_eligible"  # Some requirements met
    CONDITIONALLY_ELIGIBLE = "conditionally_eligible"  # With future changes
    NOT_ELIGIBLE = "not_eligible"

class WinProbabilityFactors(BaseModel):
    """Factors contributing to win probability calculation"""

    # Eligibility matching (40% weight)
    eligibility_score: float = Field(ge=0.0, le=1.0)
    requirements_met: int
    total_requirements: int
    critical_requirements_met: bool

    # Academic strength (25% weight)
    gpa_percentile: float | None = None  # Among eligible candidates
    academic_achievements_score: float = Field(ge=0.0, le=1.0)
    test_scores_percentile: float | None = None

    # Fit and alignment (20% weight)
    field_of_study_match: float = Field(ge=0.0, le=1.0)
    career_goals_alignment: float = Field(ge=0.0, le=1.0)
    values_alignment: float = Field(ge=0.0, le=1.0)
    geographic_preference: float = Field(ge=0.0, le=1.0)

    # Experience and activities (10% weight)
    relevant_experience_score: float = Field(ge=0.0, le=1.0)
    leadership_score: float = Field(ge=0.0, le=1.0)
    community_service_score: float = Field(ge=0.0, le=1.0)

    # Application quality potential (5% weight)
    essay_quality_prediction: float = Field(ge=0.0, le=1.0)
    recommendation_strength_prediction: float = Field(ge=0.0, le=1.0)
    application_completeness_likelihood: float = Field(ge=0.0, le=1.0)

class HistoricalWinnerProfile(BaseModel):
    """Profile of historical scholarship winners for comparison"""
    scholarship_id: str
    winner_year: int

    # Anonymized winner characteristics
    avg_gpa: float | None = None
    gpa_range: tuple | None = None
    common_majors: list[str] = []
    common_activities: list[str] = []
    common_achievements: list[str] = []

    # Demographics (aggregated/anonymized)
    geographic_distribution: dict[str, float] = {}
    school_type_distribution: dict[str, float] = {}

    # Application patterns
    avg_application_submission_days_before_deadline: int | None = None
    common_essay_themes: list[str] = []

class CompetitionAnalysis(BaseModel):
    """Analysis of competition for a specific scholarship"""
    scholarship_id: str
    analysis_date: datetime = Field(default_factory=datetime.utcnow)

    # Competition metrics
    estimated_applicant_count: int
    competition_level: CompetitionLevel
    applicant_pool_quality: float = Field(ge=0.0, le=1.0)  # Average quality of likely applicants

    # Historical context
    historical_winner_profiles: list[HistoricalWinnerProfile] = []
    acceptance_rate: float | None = None  # If known
    avg_winner_characteristics: dict[str, Any] = {}

    # Current cycle insights
    application_trend: str  # increasing, stable, decreasing
    deadline_pressure: float = Field(ge=0.0, le=1.0)  # How close to deadline
    similar_scholarships_competition: list[str] = []  # IDs of competing scholarships

class PredictiveMatchResult(BaseModel):
    """Complete predictive matching result for a scholarship"""
    scholarship_id: str
    user_id: str
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Core predictions
    likelihood_to_win: float = Field(ge=0.0, le=1.0)
    match_confidence: MatchConfidence
    eligibility_status: EligibilityStatus

    # Detailed scoring
    overall_match_score: float = Field(ge=0.0, le=1.0)
    win_probability_factors: WinProbabilityFactors
    competition_analysis: CompetitionAnalysis

    # Explanatory information
    why_matched_reasons: list[str] = []
    strength_indicators: list[str] = []
    improvement_opportunities: list[str] = []
    potential_weaknesses: list[str] = []

    # Actionable insights
    recommended_actions: list[str] = []
    estimated_time_investment: int  # hours to optimize application
    application_strategy_tips: list[str] = []

class PredictiveMatchingRequest(BaseModel):
    """Request for predictive matching analysis"""
    user_id: str
    scholarship_ids: list[str] | None = None  # If None, analyze all relevant
    include_ineligible: bool = False
    analysis_depth: str = "standard"  # basic, standard, comprehensive

    # Filtering options
    min_likelihood_threshold: float = Field(default=0.1, ge=0.0, le=1.0)
    max_competition_level: CompetitionLevel | None = None
    preferred_award_range: tuple | None = None

class RankedScholarshipRecommendation(BaseModel):
    """Scholarship recommendation with predictive ranking"""
    scholarship_id: str
    scholarship_title: str
    award_amount: float
    deadline: datetime

    # Predictive scores
    predictive_match_result: PredictiveMatchResult
    priority_rank: int  # 1 = highest priority

    # Quick insights
    quick_win_indicator: bool  # High likelihood, low competition
    stretch_opportunity: bool  # Lower likelihood but very high value
    safety_option: bool  # Very high likelihood

    # Application guidance
    estimated_application_time: int  # hours
    key_requirements_to_highlight: list[str] = []
    suggested_approach: str

class PredictiveMatchingResponse(BaseModel):
    """Response from predictive matching system"""
    user_id: str
    analysis_timestamp: datetime
    total_scholarships_analyzed: int

    # Recommendations grouped by priority
    high_priority_matches: list[RankedScholarshipRecommendation] = []
    medium_priority_matches: list[RankedScholarshipRecommendation] = []
    stretch_opportunities: list[RankedScholarshipRecommendation] = []

    # Summary insights
    overall_competitiveness_score: float = Field(ge=0.0, le=1.0)
    profile_strength_summary: dict[str, str] = {}
    top_improvement_recommendations: list[str] = []

    # Application strategy
    recommended_application_count: int
    estimated_total_time_investment: int  # hours
    success_probability_range: tuple  # (min, max) likelihood of winning at least one

class WinProbabilityCalculationRequest(BaseModel):
    """Request to calculate win probability for specific scholarship"""
    scholarship_id: str
    user_id: str
    include_improvement_scenarios: bool = True

class WinProbabilityResponse(BaseModel):
    """Detailed win probability calculation"""
    scholarship_id: str
    user_id: str
    current_win_probability: float = Field(ge=0.0, le=1.0)

    # Factor breakdown
    factor_contributions: dict[str, float] = {}
    factor_explanations: dict[str, str] = {}

    # Improvement scenarios
    improvement_scenarios: list[dict[str, Any]] = []  # What if scenarios
    max_achievable_probability: float = Field(ge=0.0, le=1.0)

    # Comparison context
    percentile_among_likely_applicants: float | None = None
    similar_profile_success_rate: float | None = None
