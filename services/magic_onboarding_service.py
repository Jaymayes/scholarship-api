# AI Scholarship Playbook - Magic Onboarding Service
# Conversational AI-powered profile intake system

import json
import logging
import uuid
from datetime import datetime
from typing import Any

from models.onboarding import (
    ConversationalContext,
    MagicOnboardingSession,
    OnboardingContinueRequest,
    OnboardingQuestion,
    OnboardingResponse,
    OnboardingStage,
    OnboardingStartRequest,
    ProfileCompletionStatus,
    QuestionType,
)
from services.openai_service import OpenAIService

logger = logging.getLogger(__name__)

class MagicOnboardingService:
    """Service for AI-powered conversational onboarding"""

    def __init__(self, openai_service: OpenAIService):
        self.openai_service = openai_service
        self.active_sessions: dict[str, MagicOnboardingSession] = {}

        # Conversation templates and flows
        self.conversation_templates = self._load_conversation_templates()
        self.profile_schema = self._load_profile_schema()

    async def start_onboarding(self, user_id: str, request: OnboardingStartRequest) -> OnboardingResponse:
        """Start a new magic onboarding session"""
        try:
            session_id = str(uuid.uuid4())

            # Create initial conversation context
            context = ConversationalContext(
                user_id=user_id,
                session_id=session_id,
                current_stage=OnboardingStage.WELCOME,
                conversation_history=[],
                extracted_data={},
                confidence_scores={},
                completion_percentage=0.0
            )

            # Create onboarding session
            session = MagicOnboardingSession(
                session_id=session_id,
                user_id=user_id,
                started_at=datetime.utcnow(),
                last_activity=datetime.utcnow(),
                current_stage=OnboardingStage.WELCOME,
                conversation_context=context,
                profile_completion_status=ProfileCompletionStatus(
                    overall_completion=0.0,
                    basic_info_completion=0.0,
                    academic_completion=0.0,
                    interests_completion=0.0,
                    financial_completion=0.0,
                    activities_completion=0.0,
                    documents_completion=0.0
                ),
                extracted_profile_data={}
            )

            # Store session
            self.active_sessions[session_id] = session

            # Generate AI welcome message
            welcome_prompt = self._create_welcome_prompt(request)
            ai_response = await self.openai_service.generate_chat_response(welcome_prompt)

            # Add to conversation history
            session.conversation_context.conversation_history.append({
                "role": "assistant",
                "content": ai_response,
                "timestamp": datetime.utcnow().isoformat()
            })

            # Generate first question
            first_question = self._get_next_question(session)

            return OnboardingResponse(
                session_id=session_id,
                current_stage=OnboardingStage.WELCOME,
                ai_message=ai_response,
                next_question=first_question,
                completion_percentage=0.0,
                suggested_actions=["Share some basic information about yourself"],
                estimated_completion_time=15,  # minutes
                next_recommended_step="Tell me about your academic background"
            )

        except Exception as e:
            logger.error(f"Failed to start onboarding for user {user_id}: {str(e)}")
            raise

    async def continue_onboarding(self, request: OnboardingContinueRequest) -> OnboardingResponse:
        """Continue an existing onboarding conversation"""
        try:
            session = self.active_sessions.get(request.session_id)
            if not session:
                raise ValueError(f"Onboarding session {request.session_id} not found")

            # Update last activity
            session.last_activity = datetime.utcnow()

            # Add user message to conversation history
            session.conversation_context.conversation_history.append({
                "role": "user",
                "content": request.user_message,
                "timestamp": datetime.utcnow().isoformat()
            })

            # Process user response with AI
            ai_analysis = await self._analyze_user_response(session, request.user_message)

            # Extract data from response
            extracted_data = await self._extract_profile_data(session, request.user_message)
            session.conversation_context.extracted_data.update(extracted_data)

            # Update profile completion
            completion_status = self._calculate_completion_status(session)
            session.profile_completion_status = completion_status
            session.completion_percentage = completion_status.overall_completion

            # Generate AI response
            ai_response = await self._generate_ai_response(session, ai_analysis)

            # Add AI response to conversation history
            session.conversation_context.conversation_history.append({
                "role": "assistant",
                "content": ai_response,
                "timestamp": datetime.utcnow().isoformat()
            })

            # Determine next stage and question
            next_stage = self._determine_next_stage(session)
            session.current_stage = next_stage
            session.conversation_context.current_stage = next_stage

            next_question = self._get_next_question(session)

            # Check if onboarding is complete
            is_complete = completion_status.overall_completion >= 0.8
            ready_for_matching = completion_status.overall_completion >= 0.6

            if is_complete:
                session.is_completed = True
                await self._finalize_onboarding(session)

            return OnboardingResponse(
                session_id=request.session_id,
                current_stage=next_stage,
                ai_message=ai_response,
                next_question=next_question if not is_complete else None,
                completion_percentage=completion_status.overall_completion,
                suggested_actions=self._get_suggested_actions(session),
                profile_insights=self._generate_profile_insights(session),
                estimated_completion_time=self._estimate_remaining_time(session),
                next_recommended_step=self._get_next_recommended_step(session),
                conversation_ended=is_complete,
                ready_for_matching=ready_for_matching
            )

        except Exception as e:
            logger.error(f"Failed to continue onboarding {request.session_id}: {str(e)}")
            raise

    async def _analyze_user_response(self, session: MagicOnboardingSession, user_message: str) -> dict[str, Any]:
        """Analyze user response using AI"""
        analysis_prompt = f"""
        Analyze this user response in the context of scholarship application onboarding:

        Current stage: {session.current_stage}
        User message: "{user_message}"

        Extract:
        1. Intent and emotion
        2. Key information mentioned
        3. Confidence level in understanding
        4. Follow-up questions needed
        5. Recommended next conversation direction

        Respond in JSON format.
        """

        try:
            analysis_text = await self.openai_service.generate_chat_response(analysis_prompt)
            return json.loads(analysis_text)
        except Exception as e:
            logger.warning(f"AI analysis failed, using fallback: {str(e)}")
            return {
                "intent": "general_response",
                "confidence": 0.5,
                "key_info": [],
                "follow_up_needed": False
            }

    async def _extract_profile_data(self, session: MagicOnboardingSession, user_message: str) -> dict[str, Any]:
        """Extract structured profile data from user message"""
        extraction_prompt = f"""
        Extract structured profile data from this user message for scholarship matching:

        Message: "{user_message}"
        Current extracted data: {json.dumps(session.conversation_context.extracted_data)}

        Look for:
        - Academic information (GPA, major, graduation date, school)
        - Personal details (name, age, location)
        - Financial information (family income, financial need)
        - Activities and achievements
        - Career goals and interests
        - Scholarship preferences

        Return only new or updated information in JSON format.
        Use null for unknown values.
        """

        try:
            extracted_text = await self.openai_service.generate_chat_response(extraction_prompt)
            return json.loads(extracted_text)
        except Exception as e:
            logger.warning(f"Data extraction failed: {str(e)}")
            return {}

    async def _generate_ai_response(self, session: MagicOnboardingSession, analysis: dict[str, Any]) -> str:
        """Generate AI response based on conversation context"""
        context = session.conversation_context

        response_prompt = f"""
        You are a friendly, helpful AI assistant helping students with scholarship applications.

        Conversation context:
        - Current stage: {session.current_stage}
        - Completion: {session.completion_percentage:.0%}
        - Recent analysis: {json.dumps(analysis)}
        - Extracted data so far: {json.dumps(context.extracted_data)}

        Generate a helpful, encouraging response that:
        1. Acknowledges what the user shared
        2. Provides relevant insights or encouragement
        3. Naturally transitions to the next helpful question
        4. Maintains a conversational, supportive tone
        5. Shows progress being made

        Keep response conversational and under 150 words.
        """

        return await self.openai_service.generate_chat_response(response_prompt)

    def _calculate_completion_status(self, session: MagicOnboardingSession) -> ProfileCompletionStatus:
        """Calculate profile completion status"""
        data = session.conversation_context.extracted_data

        # Calculate completion for each category
        basic_completion = self._calculate_category_completion(data, [
            'name', 'email', 'age', 'location'
        ])

        academic_completion = self._calculate_category_completion(data, [
            'gpa', 'major', 'graduation_date', 'school_name', 'degree_level'
        ])

        interests_completion = self._calculate_category_completion(data, [
            'career_goals', 'field_of_study', 'interests', 'values'
        ])

        financial_completion = self._calculate_category_completion(data, [
            'financial_need', 'family_income', 'work_experience'
        ])

        activities_completion = self._calculate_category_completion(data, [
            'extracurriculars', 'volunteer_work', 'leadership', 'achievements'
        ])

        # Calculate overall completion
        overall_completion = (
            basic_completion * 0.3 +
            academic_completion * 0.3 +
            interests_completion * 0.2 +
            financial_completion * 0.1 +
            activities_completion * 0.1
        )

        return ProfileCompletionStatus(
            overall_completion=overall_completion,
            basic_info_completion=basic_completion,
            academic_completion=academic_completion,
            interests_completion=interests_completion,
            financial_completion=financial_completion,
            activities_completion=activities_completion,
            documents_completion=0.0,  # Will be updated when document hub is integrated
            missing_critical_fields=self._identify_missing_critical_fields(data),
            suggested_improvements=self._generate_improvement_suggestions(data),
            estimated_time_to_complete=self._estimate_remaining_time(session)
        )

    def _calculate_category_completion(self, data: dict[str, Any], required_fields: list[str]) -> float:
        """Calculate completion percentage for a category"""
        if not required_fields:
            return 1.0

        completed_fields = sum(1 for field in required_fields if data.get(field) is not None)
        return completed_fields / len(required_fields)

    def _identify_missing_critical_fields(self, data: dict[str, Any]) -> list[str]:
        """Identify missing critical profile fields"""
        critical_fields = {
            'gpa': 'GPA',
            'major': 'Major/Field of Study',
            'graduation_date': 'Graduation Date',
            'career_goals': 'Career Goals',
            'financial_need': 'Financial Need Level'
        }

        return [name for field, name in critical_fields.items() if data.get(field) is None]

    def _generate_improvement_suggestions(self, data: dict[str, Any]) -> list[str]:
        """Generate suggestions for profile improvement"""
        suggestions = []

        if not data.get('gpa'):
            suggestions.append("Add your GPA to match with merit-based scholarships")

        if not data.get('extracurriculars'):
            suggestions.append("Share your activities and involvement to strengthen your profile")

        if not data.get('career_goals'):
            suggestions.append("Describe your career goals to find targeted scholarships")

        if not data.get('achievements'):
            suggestions.append("Mention any awards or achievements to stand out")

        return suggestions

    def _determine_next_stage(self, session: MagicOnboardingSession) -> OnboardingStage:
        """Determine the next stage of onboarding based on completion"""
        completion = session.profile_completion_status.overall_completion

        if completion < 0.2:
            return OnboardingStage.BASIC_INFO
        if completion < 0.4:
            return OnboardingStage.ACADEMIC_PROFILE
        if completion < 0.6:
            return OnboardingStage.INTERESTS_GOALS
        if completion < 0.8:
            return OnboardingStage.ACTIVITIES_ACHIEVEMENTS
        return OnboardingStage.REVIEW_COMPLETE

    def _get_next_question(self, session: MagicOnboardingSession) -> OnboardingQuestion | None:
        """Get the next appropriate question based on session state"""
        stage = session.current_stage

        # Define stage-specific questions
        questions_by_stage = {
            OnboardingStage.WELCOME: [
                OnboardingQuestion(
                    question_id="welcome_intro",
                    stage=OnboardingStage.WELCOME,
                    question_type=QuestionType.OPEN_TEXT,
                    question_text="Hi! I'm here to help you find scholarships that are perfect for you. Let's start with the basics - what's your name and what are you studying?",
                    is_required=False
                )
            ],
            OnboardingStage.BASIC_INFO: [
                OnboardingQuestion(
                    question_id="academic_level",
                    stage=OnboardingStage.BASIC_INFO,
                    question_type=QuestionType.MULTIPLE_CHOICE,
                    question_text="What's your current academic level?",
                    options=["High School Senior", "Undergraduate", "Graduate Student", "Other"],
                    is_required=True
                )
            ],
            OnboardingStage.ACADEMIC_PROFILE: [
                OnboardingQuestion(
                    question_id="gpa_major",
                    stage=OnboardingStage.ACADEMIC_PROFILE,
                    question_type=QuestionType.OPEN_TEXT,
                    question_text="What's your GPA and major? Don't worry if you're not sure about your exact GPA - an estimate is fine!",
                    is_required=True
                )
            ]
        }

        stage_questions = questions_by_stage.get(stage, [])

        # Return first unanswered question for this stage
        for question in stage_questions:
            if question.question_id not in session.conversation_context.extracted_data:
                return question

        return None

    def _get_suggested_actions(self, session: MagicOnboardingSession) -> list[str]:
        """Get suggested actions for the user"""
        completion = session.profile_completion_status.overall_completion

        if completion < 0.3:
            return [
                "Share your academic information",
                "Tell me about your interests and goals",
                "Upload your transcript if you have it"
            ]
        if completion < 0.6:
            return [
                "Add your activities and achievements",
                "Describe your financial situation",
                "Upload your resume or CV"
            ]
        return [
            "Review your profile for accuracy",
            "Start browsing matched scholarships",
            "Set up application deadline reminders"
        ]

    def _generate_profile_insights(self, session: MagicOnboardingSession) -> dict[str, Any] | None:
        """Generate insights about the user's profile"""
        data = session.conversation_context.extracted_data
        completion = session.profile_completion_status.overall_completion

        if completion < 0.3:
            return None

        insights = {
            "profile_strength": "developing" if completion < 0.6 else "strong",
            "top_match_categories": [],
            "estimated_scholarship_matches": 0,
            "profile_highlights": []
        }

        # Add specific insights based on available data
        if data.get('gpa') and float(data['gpa']) > 3.5:
            insights["profile_highlights"].append("Strong academic performance")

        if data.get('leadership'):
            insights["profile_highlights"].append("Leadership experience")

        return insights

    def _estimate_remaining_time(self, session: MagicOnboardingSession) -> int:
        """Estimate remaining time to complete onboarding (in minutes)"""
        completion = session.profile_completion_status.overall_completion
        remaining = 1.0 - completion
        base_time = 15  # Total estimated time for full onboarding

        return max(2, int(base_time * remaining))

    def _get_next_recommended_step(self, session: MagicOnboardingSession) -> str:
        """Get the next recommended step for the user"""
        completion = session.profile_completion_status.overall_completion
        missing_fields = session.profile_completion_status.missing_critical_fields

        if missing_fields:
            return f"Add your {missing_fields[0].lower()} to improve your matches"
        if completion < 0.8:
            return "Continue sharing information to find more scholarship opportunities"
        return "Start exploring your personalized scholarship recommendations"

    async def _finalize_onboarding(self, session: MagicOnboardingSession):
        """Finalize the onboarding process"""
        try:
            # Generate final profile summary
            summary_prompt = f"""
            Create a comprehensive profile summary for scholarship matching based on this conversation:

            Extracted data: {json.dumps(session.conversation_context.extracted_data)}

            Generate a structured profile that includes:
            1. Academic background and achievements
            2. Personal interests and career goals
            3. Financial situation and needs
            4. Activities and leadership experience
            5. Scholarship preferences and priorities

            Return as structured JSON for database storage.
            """

            profile_summary = await self.openai_service.generate_chat_response(summary_prompt)
            session.extracted_profile_data = json.loads(profile_summary)

            logger.info(f"Completed onboarding for session {session.session_id}")

        except Exception as e:
            logger.error(f"Failed to finalize onboarding: {str(e)}")

    def _create_welcome_prompt(self, request: OnboardingStartRequest) -> str:
        """Create welcome prompt based on user preferences"""
        style = request.preferred_communication_style or "friendly"
        time_available = request.time_available or 15

        return f"""
        Create a warm, {style} welcome message for a student starting scholarship application assistance.
        They have about {time_available} minutes available.
        The message should:
        1. Introduce yourself as their scholarship assistant
        2. Explain how you'll help them find scholarships
        3. Set expectations for the conversation
        4. Be encouraging and supportive
        5. Ask an engaging opening question

        Keep it conversational and under 100 words.
        """

    def _load_conversation_templates(self) -> dict[str, Any]:
        """Load conversation templates and flows"""
        # In a real implementation, this would load from files or database
        return {
            "welcome_messages": [],
            "question_flows": {},
            "response_templates": {}
        }

    def _load_profile_schema(self) -> dict[str, Any]:
        """Load profile schema for data extraction"""
        # In a real implementation, this would define the complete profile schema
        return {
            "required_fields": [],
            "optional_fields": [],
            "validation_rules": {}
        }
