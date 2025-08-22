# AI Scholarship Playbook - Predictive Matching Service
# "Likelihood to win" scoring and intelligent ranking engine

import logging
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import math

from models.predictive_matching import (
    PredictiveMatchResult, WinProbabilityFactors, CompetitionAnalysis,
    CompetitionLevel, MatchConfidence, EligibilityStatus,
    RankedScholarshipRecommendation, PredictiveMatchingResponse,
    HistoricalWinnerProfile
)
from models.scholarship import Scholarship
from models.user import UserProfile
from services.openai_service import OpenAIService
from services.eligibility_service import EligibilityService

logger = logging.getLogger(__name__)

class PredictiveMatchingService:
    """Service for AI-powered predictive scholarship matching"""
    
    def __init__(self, openai_service: OpenAIService, eligibility_service: EligibilityService):
        self.openai_service = openai_service
        self.eligibility_service = eligibility_service
        
        # Historical data for prediction modeling
        self.historical_winners = self._load_historical_data()
        self.competition_models = self._load_competition_models()
        
    async def predict_scholarship_matches(
        self, 
        user_profile: UserProfile, 
        scholarships: List[Scholarship],
        analysis_depth: str = "standard"
    ) -> PredictiveMatchingResponse:
        """
        Generate predictive scholarship matches with likelihood scoring
        """
        try:
            logger.info(f"Starting predictive matching for user with {len(scholarships)} scholarships")
            
            # Calculate predictions for each scholarship
            match_results = []
            for scholarship in scholarships:
                result = await self._calculate_scholarship_prediction(
                    user_profile, scholarship, analysis_depth
                )
                if result:
                    match_results.append(result)
            
            # Sort by likelihood to win (descending)
            match_results.sort(key=lambda x: x.likelihood_to_win, reverse=True)
            
            # Create ranked recommendations
            recommendations = []
            for i, result in enumerate(match_results):
                scholarship = next(s for s in scholarships if s.id == result.scholarship_id)
                
                # Determine recommendation category
                rec = RankedScholarshipRecommendation(
                    scholarship_id=result.scholarship_id,
                    scholarship_title=scholarship.title,
                    award_amount=scholarship.amount,
                    deadline=scholarship.deadline,
                    predictive_match_result=result,
                    priority_rank=i + 1,
                    quick_win_indicator=self._is_quick_win(result),
                    stretch_opportunity=self._is_stretch_opportunity(result),
                    safety_option=self._is_safety_option(result),
                    estimated_application_time=self._estimate_application_time(result),
                    key_requirements_to_highlight=self._get_key_requirements(result),
                    suggested_approach=self._get_application_strategy(result)
                )
                recommendations.append(rec)
            
            # Categorize recommendations
            high_priority = [r for r in recommendations if r.predictive_match_result.likelihood_to_win >= 0.75]
            medium_priority = [r for r in recommendations if 0.5 <= r.predictive_match_result.likelihood_to_win < 0.75]
            stretch_opportunities = [r for r in recommendations if r.stretch_opportunity]
            
            # Calculate overall competitiveness
            overall_score = self._calculate_overall_competitiveness(user_profile, match_results)
            
            # Generate profile strength summary
            strength_summary = await self._generate_profile_strength_summary(user_profile, match_results)
            
            # Generate improvement recommendations
            improvements = await self._generate_improvement_recommendations(user_profile, match_results)
            
            # Calculate application strategy
            recommended_count = min(8, len([r for r in recommendations if r.predictive_match_result.likelihood_to_win >= 0.3]))
            total_time = sum(r.estimated_application_time for r in recommendations[:recommended_count])
            
            # Calculate success probability range
            success_prob_range = self._calculate_success_probability_range(recommendations[:recommended_count])
            
            return PredictiveMatchingResponse(
                user_id=user_profile.user_id,
                analysis_timestamp=datetime.utcnow(),
                total_scholarships_analyzed=len(scholarships),
                high_priority_matches=high_priority[:5],
                medium_priority_matches=medium_priority[:5], 
                stretch_opportunities=stretch_opportunities[:3],
                overall_competitiveness_score=overall_score,
                profile_strength_summary=strength_summary,
                top_improvement_recommendations=improvements,
                recommended_application_count=recommended_count,
                estimated_total_time_investment=total_time,
                success_probability_range=success_prob_range
            )
            
        except Exception as e:
            logger.error(f"Predictive matching failed: {str(e)}")
            raise
    
    async def _calculate_scholarship_prediction(
        self, 
        user_profile: UserProfile, 
        scholarship: Scholarship,
        analysis_depth: str
    ) -> Optional[PredictiveMatchResult]:
        """Calculate predictive match for a single scholarship"""
        try:
            # Basic eligibility check first
            eligibility_result = self.eligibility_service.check_eligibility(user_profile, scholarship.id)
            
            if not eligibility_result.eligible and eligibility_result.match_score < 0.3:
                return None  # Skip obviously ineligible scholarships
            
            # Calculate win probability factors
            factors = await self._calculate_win_probability_factors(user_profile, scholarship)
            
            # Analyze competition
            competition = await self._analyze_competition(scholarship)
            
            # Calculate overall likelihood to win
            likelihood = self._calculate_likelihood_to_win(factors, competition)
            
            # Determine match confidence
            confidence = self._determine_match_confidence(factors, competition, analysis_depth)
            
            # Generate explanatory insights
            why_matched = await self._generate_why_matched_explanation(user_profile, scholarship, factors)
            strengths = await self._identify_strength_indicators(user_profile, scholarship, factors)
            improvements = await self._identify_improvement_opportunities(user_profile, scholarship, factors)
            weaknesses = await self._identify_potential_weaknesses(user_profile, scholarship, factors)
            
            # Generate actionable recommendations
            actions = await self._generate_recommended_actions(user_profile, scholarship, factors)
            strategy_tips = await self._generate_strategy_tips(user_profile, scholarship, factors)
            
            return PredictiveMatchResult(
                scholarship_id=scholarship.id,
                user_id=user_profile.user_id,
                likelihood_to_win=likelihood,
                match_confidence=confidence,
                eligibility_status=self._map_eligibility_status(eligibility_result),
                overall_match_score=factors.eligibility_score,
                win_probability_factors=factors,
                competition_analysis=competition,
                why_matched_reasons=why_matched,
                strength_indicators=strengths,
                improvement_opportunities=improvements,
                potential_weaknesses=weaknesses,
                recommended_actions=actions,
                estimated_time_investment=self._estimate_application_time_for_scholarship(scholarship),
                application_strategy_tips=strategy_tips
            )
            
        except Exception as e:
            logger.warning(f"Failed to calculate prediction for scholarship {scholarship.id}: {str(e)}")
            return None
    
    async def _calculate_win_probability_factors(
        self, 
        user_profile: UserProfile, 
        scholarship: Scholarship
    ) -> WinProbabilityFactors:
        """Calculate detailed factors contributing to win probability"""
        
        # Eligibility scoring (40% weight)
        eligibility_result = self.eligibility_service.check_eligibility(user_profile, scholarship.id)
        eligibility_score = eligibility_result.match_score
        requirements_met = len([r for r in eligibility_result.reasons if "meets" in r.lower()])
        total_requirements = len(scholarship.eligibility_criteria) if hasattr(scholarship, 'eligibility_criteria') else 5
        critical_met = eligibility_score > 0.8
        
        # Academic strength (25% weight)
        gpa_percentile = self._calculate_gpa_percentile(user_profile.gpa, scholarship)
        academic_score = min(1.0, (user_profile.gpa or 3.0) / 4.0)
        test_percentile = None  # Would calculate if test scores available
        
        # Fit and alignment (20% weight)
        field_match = self._calculate_field_match(user_profile, scholarship)
        career_alignment = self._calculate_career_alignment(user_profile, scholarship)
        values_alignment = self._calculate_values_alignment(user_profile, scholarship)
        geo_preference = self._calculate_geographic_preference(user_profile, scholarship)
        
        # Experience and activities (10% weight)
        experience_score = self._calculate_experience_score(user_profile)
        leadership_score = self._calculate_leadership_score(user_profile)
        service_score = self._calculate_service_score(user_profile)
        
        # Application quality potential (5% weight)
        essay_prediction = self._predict_essay_quality(user_profile, scholarship)
        rec_prediction = self._predict_recommendation_strength(user_profile)
        completeness_likelihood = 0.9  # Based on user engagement level
        
        return WinProbabilityFactors(
            eligibility_score=eligibility_score,
            requirements_met=requirements_met,
            total_requirements=total_requirements,
            critical_requirements_met=critical_met,
            gpa_percentile=gpa_percentile,
            academic_achievements_score=academic_score,
            test_scores_percentile=test_percentile,
            field_of_study_match=field_match,
            career_goals_alignment=career_alignment,
            values_alignment=values_alignment,
            geographic_preference=geo_preference,
            relevant_experience_score=experience_score,
            leadership_score=leadership_score,
            community_service_score=service_score,
            essay_quality_prediction=essay_prediction,
            recommendation_strength_prediction=rec_prediction,
            application_completeness_likelihood=completeness_likelihood
        )
    
    async def _analyze_competition(self, scholarship: Scholarship) -> CompetitionAnalysis:
        """Analyze competition level for a scholarship"""
        
        # Estimate applicant count based on award amount and criteria
        estimated_applicants = self._estimate_applicant_count(scholarship)
        
        # Determine competition level
        if estimated_applicants < 50:
            level = CompetitionLevel.VERY_LOW
        elif estimated_applicants < 200:
            level = CompetitionLevel.LOW
        elif estimated_applicants < 500:
            level = CompetitionLevel.MEDIUM
        elif estimated_applicants < 1000:
            level = CompetitionLevel.HIGH
        else:
            level = CompetitionLevel.VERY_HIGH
        
        # Calculate applicant pool quality
        pool_quality = self._estimate_applicant_pool_quality(scholarship)
        
        # Load historical winner profiles
        historical_profiles = self._get_historical_winners(scholarship.id)
        
        # Calculate acceptance rate if known
        acceptance_rate = self._estimate_acceptance_rate(scholarship, estimated_applicants)
        
        # Analyze trends
        trend = self._analyze_application_trend(scholarship)
        
        # Calculate deadline pressure
        days_to_deadline = (scholarship.deadline - datetime.now()).days
        deadline_pressure = max(0.0, min(1.0, (90 - days_to_deadline) / 90))
        
        return CompetitionAnalysis(
            scholarship_id=scholarship.id,
            estimated_applicant_count=estimated_applicants,
            competition_level=level,
            applicant_pool_quality=pool_quality,
            historical_winner_profiles=historical_profiles,
            acceptance_rate=acceptance_rate,
            application_trend=trend,
            deadline_pressure=deadline_pressure,
            similar_scholarships_competition=[]  # Would analyze similar opportunities
        )
    
    def _calculate_likelihood_to_win(
        self, 
        factors: WinProbabilityFactors, 
        competition: CompetitionAnalysis
    ) -> float:
        """Calculate overall likelihood to win using weighted factors"""
        
        # Base score from eligibility and fit
        base_score = (
            factors.eligibility_score * 0.4 +
            factors.academic_achievements_score * 0.25 +
            factors.field_of_study_match * 0.1 +
            factors.career_goals_alignment * 0.1 +
            factors.relevant_experience_score * 0.05 +
            factors.leadership_score * 0.05 +
            factors.essay_quality_prediction * 0.05
        )
        
        # Adjust for competition level
        competition_multiplier = {
            CompetitionLevel.VERY_LOW: 1.2,
            CompetitionLevel.LOW: 1.1,
            CompetitionLevel.MEDIUM: 1.0,
            CompetitionLevel.HIGH: 0.9,
            CompetitionLevel.VERY_HIGH: 0.8
        }
        
        adjusted_score = base_score * competition_multiplier[competition.competition_level]
        
        # Apply quality of applicant pool adjustment
        pool_adjustment = 1.0 - (competition.applicant_pool_quality - 0.5) * 0.3
        final_score = adjusted_score * pool_adjustment
        
        # Apply deadline pressure (slight boost for early applications)
        if competition.deadline_pressure < 0.3:  # Applying early
            final_score *= 1.05
        elif competition.deadline_pressure > 0.8:  # Last minute
            final_score *= 0.95
        
        return max(0.0, min(1.0, final_score))
    
    def _estimate_applicant_count(self, scholarship: Scholarship) -> int:
        """Estimate number of applicants based on scholarship characteristics"""
        base_applicants = 100
        
        # Award amount impact
        if scholarship.amount > 10000:
            base_applicants *= 3
        elif scholarship.amount > 5000:
            base_applicants *= 2
        elif scholarship.amount > 1000:
            base_applicants *= 1.5
        
        # Specificity impact (more specific = fewer applicants)
        specificity_factors = 0
        if hasattr(scholarship, 'field_of_study') and scholarship.field_of_study:
            specificity_factors += 1
        if hasattr(scholarship, 'gpa_requirement') and scholarship.gpa_requirement > 3.5:
            specificity_factors += 1
        if hasattr(scholarship, 'geographic_restriction') and scholarship.geographic_restriction:
            specificity_factors += 1
        
        # Apply specificity reduction
        reduction_factor = 0.7 ** specificity_factors
        
        return int(base_applicants * reduction_factor)
    
    def _calculate_gpa_percentile(self, user_gpa: Optional[float], scholarship: Scholarship) -> Optional[float]:
        """Calculate user's GPA percentile among likely applicants"""
        if not user_gpa:
            return None
        
        # Estimate typical applicant GPA distribution for this scholarship
        if scholarship.amount > 5000:  # Competitive scholarship
            mean_gpa = 3.6
            std_dev = 0.3
        else:  # Less competitive
            mean_gpa = 3.3
            std_dev = 0.4
        
        # Calculate percentile using normal distribution approximation
        z_score = (user_gpa - mean_gpa) / std_dev
        percentile = 0.5 * (1 + math.erf(z_score / math.sqrt(2)))
        
        return max(0.0, min(1.0, percentile))
    
    def _calculate_field_match(self, user_profile: UserProfile, scholarship: Scholarship) -> float:
        """Calculate how well user's field matches scholarship focus"""
        if not hasattr(scholarship, 'field_of_study') or not scholarship.field_of_study:
            return 0.7  # Neutral if no specific field requirement
        
        user_field = user_profile.field_of_study.lower()
        scholarship_field = scholarship.field_of_study.lower()
        
        # Exact match
        if user_field == scholarship_field:
            return 1.0
        
        # Related fields
        field_relations = {
            'computer science': ['software engineering', 'information technology', 'data science'],
            'engineering': ['computer science', 'mechanical engineering', 'electrical engineering'],
            'business': ['finance', 'marketing', 'management', 'economics']
        }
        
        for base_field, related in field_relations.items():
            if base_field in scholarship_field and user_field in related:
                return 0.8
            if base_field in user_field and scholarship_field in related:
                return 0.8
        
        # STEM fields
        stem_fields = ['computer science', 'engineering', 'mathematics', 'physics', 'chemistry', 'biology']
        if any(field in user_field for field in stem_fields) and any(field in scholarship_field for field in stem_fields):
            return 0.6
        
        return 0.3  # Low match
    
    def _calculate_career_alignment(self, user_profile: UserProfile, scholarship: Scholarship) -> float:
        """Calculate alignment between career goals and scholarship mission"""
        # This would use AI to analyze career goals vs scholarship values
        # For now, return reasonable estimate
        return 0.75
    
    def _calculate_values_alignment(self, user_profile: UserProfile, scholarship: Scholarship) -> float:
        """Calculate alignment with scholarship organization values"""
        # This would analyze user activities vs scholarship mission
        return 0.7
    
    def _calculate_geographic_preference(self, user_profile: UserProfile, scholarship: Scholarship) -> float:
        """Calculate geographic preference matching"""
        if not hasattr(scholarship, 'geographic_restriction'):
            return 1.0  # No restriction
        
        # Would compare user location with scholarship geographic preferences
        return 0.8
    
    def _calculate_experience_score(self, user_profile: UserProfile) -> float:
        """Score user's relevant experience"""
        score = 0.5  # Base score
        
        # Add points for various experiences
        if hasattr(user_profile, 'work_experience') and user_profile.work_experience:
            score += 0.2
        if hasattr(user_profile, 'internships') and user_profile.internships:
            score += 0.2
        if hasattr(user_profile, 'research_experience') and user_profile.research_experience:
            score += 0.1
        
        return min(1.0, score)
    
    def _calculate_leadership_score(self, user_profile: UserProfile) -> float:
        """Score user's leadership experience"""
        score = 0.3  # Base score
        
        # Check for leadership indicators
        if hasattr(user_profile, 'leadership_roles') and user_profile.leadership_roles:
            score += 0.4
        if hasattr(user_profile, 'club_officer_positions') and user_profile.club_officer_positions:
            score += 0.3
        
        return min(1.0, score)
    
    def _calculate_service_score(self, user_profile: UserProfile) -> float:
        """Score user's community service"""
        score = 0.4  # Base score
        
        if hasattr(user_profile, 'volunteer_hours') and user_profile.volunteer_hours:
            if user_profile.volunteer_hours > 100:
                score += 0.4
            elif user_profile.volunteer_hours > 50:
                score += 0.3
            else:
                score += 0.2
        
        return min(1.0, score)
    
    # Additional helper methods would continue here...
    # For brevity, including key framework methods
    
    def _is_quick_win(self, result: PredictiveMatchResult) -> bool:
        """Determine if this is a quick win opportunity"""
        return (result.likelihood_to_win > 0.7 and 
                result.competition_analysis.competition_level in [CompetitionLevel.VERY_LOW, CompetitionLevel.LOW])
    
    def _is_stretch_opportunity(self, result: PredictiveMatchResult) -> bool:
        """Determine if this is a stretch opportunity"""
        return (result.likelihood_to_win < 0.6 and 
                hasattr(result, 'scholarship_value') and result.scholarship_value > 5000)
    
    def _is_safety_option(self, result: PredictiveMatchResult) -> bool:
        """Determine if this is a safety option"""
        return result.likelihood_to_win > 0.8
    
    def _load_historical_data(self) -> Dict[str, Any]:
        """Load historical winner data for prediction modeling"""
        # In production, this would load from database
        return {}
    
    def _load_competition_models(self) -> Dict[str, Any]:
        """Load competition analysis models"""
        # In production, this would load ML models
        return {}
    
    # Many more helper methods would be implemented for a complete service...
    
    async def get_win_probability_explanation(
        self, 
        user_id: str, 
        scholarship_id: str
    ) -> Dict[str, Any]:
        """Get detailed explanation of win probability calculation"""
        # This would provide transparent explanation of scoring
        return {
            "probability": 0.75,
            "factors": {
                "eligibility": {"score": 0.9, "explanation": "Meets all requirements"},
                "academic": {"score": 0.8, "explanation": "Strong GPA in competitive range"},
                "competition": {"score": 0.7, "explanation": "Medium competition level"}
            }
        }