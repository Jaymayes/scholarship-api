# AI Scholarship Playbook - Magic Onboarding Models
# Conversational profile intake system

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum

class OnboardingStage(str, Enum):
    """Stages of the magic onboarding process"""
    WELCOME = "welcome"
    BASIC_INFO = "basic_info"
    ACADEMIC_PROFILE = "academic_profile"
    INTERESTS_GOALS = "interests_goals"
    FINANCIAL_SITUATION = "financial_situation"
    ACTIVITIES_ACHIEVEMENTS = "activities_achievements"
    DOCUMENTS_UPLOAD = "documents_upload"
    REVIEW_COMPLETE = "review_complete"

class QuestionType(str, Enum):
    """Types of onboarding questions"""
    OPEN_TEXT = "open_text"
    MULTIPLE_CHOICE = "multiple_choice"
    SCALE_RATING = "scale_rating"
    DATE_PICKER = "date_picker"
    NUMBER_INPUT = "number_input"
    DOCUMENT_UPLOAD = "document_upload"
    CONFIRMATION = "confirmation"

class OnboardingQuestion(BaseModel):
    """Individual question in the magic onboarding flow"""
    question_id: str
    stage: OnboardingStage
    question_type: QuestionType
    question_text: str
    help_text: Optional[str] = None
    is_required: bool = True
    validation_rules: Optional[Dict[str, Any]] = None
    options: Optional[List[str]] = None  # For multiple choice
    follow_up_questions: Optional[List[str]] = None  # Conditional questions
    ai_context: Optional[str] = None  # Context for AI processing
    
class OnboardingUserResponse(BaseModel):
    """User response to an onboarding question"""
    question_id: str
    response_value: Union[str, int, float, List[str]]
    confidence_level: Optional[float] = None  # AI confidence in understanding
    needs_clarification: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ConversationalContext(BaseModel):
    """AI conversation context for magic onboarding"""
    user_id: str
    session_id: str
    current_stage: OnboardingStage
    conversation_history: List[Dict[str, str]] = []
    extracted_data: Dict[str, Any] = {}
    confidence_scores: Dict[str, float] = {}
    suggested_next_questions: List[str] = []
    completion_percentage: float = 0.0
    
class ProfileCompletionStatus(BaseModel):
    """Track profile completion across different areas"""
    overall_completion: float = Field(ge=0.0, le=1.0)
    basic_info_completion: float = Field(ge=0.0, le=1.0)
    academic_completion: float = Field(ge=0.0, le=1.0)
    interests_completion: float = Field(ge=0.0, le=1.0)
    financial_completion: float = Field(ge=0.0, le=1.0)
    activities_completion: float = Field(ge=0.0, le=1.0)
    documents_completion: float = Field(ge=0.0, le=1.0)
    
    missing_critical_fields: List[str] = []
    suggested_improvements: List[str] = []
    estimated_time_to_complete: Optional[int] = None  # minutes

class MagicOnboardingSession(BaseModel):
    """Complete magic onboarding session"""
    session_id: str
    user_id: str
    started_at: datetime
    last_activity: datetime
    current_stage: OnboardingStage
    is_completed: bool = False
    completion_percentage: float = 0.0
    
    # Conversation state
    conversation_context: ConversationalContext
    responses: List[OnboardingUserResponse] = []
    
    # AI analysis
    personality_insights: Optional[Dict[str, Any]] = None
    academic_strengths: List[str] = []
    financial_need_level: Optional[str] = None
    scholarship_preferences: Dict[str, Any] = {}
    
    # Profile building
    extracted_profile_data: Dict[str, Any] = {}
    profile_completion_status: ProfileCompletionStatus
    
class OnboardingStartRequest(BaseModel):
    """Request to start magic onboarding"""
    user_message: Optional[str] = None
    preferred_communication_style: Optional[str] = "friendly"  # friendly, professional, casual
    time_available: Optional[int] = None  # minutes user has available
    priority_areas: Optional[List[str]] = None  # what they want to focus on first

class OnboardingContinueRequest(BaseModel):
    """Request to continue onboarding conversation"""
    session_id: str
    user_message: str
    clarification_needed: Optional[bool] = False
    skip_current_question: Optional[bool] = False

class OnboardingResponse(BaseModel):
    """Response from magic onboarding system"""
    session_id: str
    current_stage: OnboardingStage
    ai_message: str
    next_question: Optional[OnboardingQuestion] = None
    completion_percentage: float
    suggested_actions: List[str] = []
    
    # Progress indicators
    profile_insights: Optional[Dict[str, Any]] = None
    estimated_completion_time: Optional[int] = None
    next_recommended_step: Optional[str] = None
    
    # Conversation flow
    conversation_ended: bool = False
    ready_for_matching: bool = False

class SmartProfileSuggestion(BaseModel):
    """AI-generated profile improvement suggestions"""
    suggestion_id: str
    category: str  # academic, financial, activities, etc.
    suggestion_text: str
    impact_level: str  # high, medium, low
    estimated_time: int  # minutes to implement
    ai_confidence: float = Field(ge=0.0, le=1.0)
    
    # Contextual data
    why_important: str
    example_response: Optional[str] = None
    related_scholarships: List[str] = []

class ProfileUpdateRequest(BaseModel):
    """Request to update user profile with onboarding data"""
    session_id: str
    field_updates: Dict[str, Any]
    override_existing: bool = False
    source: str = "magic_onboarding"

class ProfileUpdateResponse(BaseModel):
    """Response after profile update"""
    updated_fields: List[str]
    new_completion_percentage: float
    improved_match_count: Optional[int] = None
    new_recommendations: List[str] = []
    next_suggested_action: Optional[str] = None