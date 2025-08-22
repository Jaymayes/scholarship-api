"""
OpenAI Service for AI-powered scholarship features
"""

import json
import os
from typing import List, Dict, Any, Optional
from openai import OpenAI
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)

class OpenAIService:
    """Service for OpenAI-powered scholarship features"""
    
    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not found, AI features will be disabled")
            self.client = None
        else:
            self.client = OpenAI(api_key=self.api_key)
            logger.info("OpenAI service initialized successfully")
    
    def is_available(self) -> bool:
        """Check if OpenAI service is available"""
        return self.client is not None
    
    def enhance_search_query(self, query: str, user_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Enhance search query using AI to extract better search terms and filters
        """
        if not self.is_available():
            return {"enhanced_query": query, "suggested_filters": {}}
        
        try:
            context_info = ""
            if user_context:
                context_info = f"User context: {json.dumps(user_context)}"
            
            prompt = f"""
            Analyze this scholarship search query and enhance it for better results.
            Original query: "{query}"
            {context_info}
            
            Extract and return JSON with:
            1. enhanced_query: improved search terms
            2. suggested_filters: relevant filters like field_of_study, scholarship_type, etc.
            3. search_intent: what the user is likely looking for
            4. confidence: how confident you are in the enhancement (0-1)
            
            Focus on scholarship-related terms and educational context.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
                messages=[
                    {"role": "system", "content": "You are a scholarship search expert. Analyze queries and suggest improvements for finding relevant scholarships."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content)
            logger.info(f"Enhanced search query: {query} -> {result.get('enhanced_query')}")
            return result
            
        except Exception as e:
            logger.error(f"Error enhancing search query: {e}")
            return {"enhanced_query": query, "suggested_filters": {}}
    
    def generate_scholarship_summary(self, scholarship_data: Dict[str, Any]) -> str:
        """
        Generate a concise, student-friendly summary of a scholarship
        """
        if not self.is_available():
            return scholarship_data.get("description", "")[:200] + "..."
        
        try:
            prompt = f"""
            Create a concise, engaging summary for this scholarship that highlights:
            - Key benefits and opportunity
            - Eligibility requirements
            - Application deadline
            - Scholarship amount
            
            Scholarship data:
            Name: {scholarship_data.get('name')}
            Organization: {scholarship_data.get('organization')}
            Amount: ${scholarship_data.get('amount', 0):,.2f}
            Type: {scholarship_data.get('scholarship_type')}
            Description: {scholarship_data.get('description')}
            Eligibility: {scholarship_data.get('eligibility_criteria')}
            Deadline: {scholarship_data.get('application_deadline')}
            
            Keep it under 150 words and make it appealing to students.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that creates engaging scholarship summaries for students."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=200
            )
            
            summary = response.choices[0].message.content.strip()
            logger.info(f"Generated summary for scholarship: {scholarship_data.get('name')}")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating scholarship summary: {e}")
            return scholarship_data.get("description", "")[:200] + "..."
    
    def analyze_eligibility_match(self, user_profile: Dict[str, Any], scholarship: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use AI to analyze how well a user matches scholarship eligibility
        """
        if not self.is_available():
            return {"match_score": 0.5, "analysis": "AI analysis not available", "recommendations": []}
        
        try:
            prompt = f"""
            Analyze how well this student profile matches the scholarship eligibility criteria.
            
            Student Profile:
            {json.dumps(user_profile, indent=2)}
            
            Scholarship:
            Name: {scholarship.get('name')}
            Eligibility Criteria: {json.dumps(scholarship.get('eligibility_criteria', {}), indent=2)}
            Type: {scholarship.get('scholarship_type')}
            Amount: ${scholarship.get('amount', 0):,.2f}
            
            Return JSON with:
            1. match_score: 0.0-1.0 rating of how well they match
            2. analysis: brief explanation of the match
            3. recommendations: list of specific advice for the student
            4. missing_requirements: what the student lacks (if any)
            5. strengths: what makes them a good candidate
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
                messages=[
                    {"role": "system", "content": "You are a scholarship advisor analyzing student-scholarship matches."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.4
            )
            
            result = json.loads(response.choices[0].message.content)
            logger.info(f"Analyzed eligibility match for {scholarship.get('name')}: {result.get('match_score')}")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing eligibility match: {e}")
            return {"match_score": 0.5, "analysis": "Analysis unavailable", "recommendations": []}
    
    def generate_search_suggestions(self, partial_query: str, search_history: List[str] = None) -> List[str]:
        """
        Generate intelligent search suggestions based on partial query
        """
        if not self.is_available():
            return [partial_query + " scholarship", partial_query + " grant", partial_query + " award"]
        
        try:
            history_context = ""
            if search_history:
                history_context = f"Recent searches: {', '.join(search_history[-5:])}"
            
            prompt = f"""
            Generate 5 relevant scholarship search suggestions based on this partial query.
            Partial query: "{partial_query}"
            {history_context}
            
            Return JSON array of suggestion strings that are:
            - Specific to scholarships and education funding
            - Complete and actionable search terms
            - Relevant to the partial input
            - Diverse in scope (merit, need-based, field-specific, etc.)
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
                messages=[
                    {"role": "system", "content": "You are a scholarship search assistant providing helpful query suggestions."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.6
            )
            
            result = json.loads(response.choices[0].message.content)
            suggestions = result.get("suggestions", [])
            logger.info(f"Generated {len(suggestions)} search suggestions for: {partial_query}")
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating search suggestions: {e}")
            return [partial_query + " scholarship"]
    
    def analyze_scholarship_trends(self, scholarships: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze scholarship data to identify trends and insights
        """
        if not self.is_available():
            return {"insights": "AI analysis not available"}
        
        try:
            # Sample data for analysis (limit to avoid token limits)
            sample_scholarships = scholarships[:10] if len(scholarships) > 10 else scholarships
            
            prompt = f"""
            Analyze these scholarship offerings and identify key trends and insights.
            
            Scholarship Data:
            {json.dumps(sample_scholarships, indent=2, default=str)}
            
            Return JSON with:
            1. top_fields: most common fields of study
            2. funding_trends: insights about scholarship amounts
            3. eligibility_patterns: common eligibility requirements
            4. deadline_insights: timing patterns
            5. recommendations: advice for students based on trends
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
                messages=[
                    {"role": "system", "content": "You are a scholarship data analyst providing insights on funding opportunities."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.4
            )
            
            result = json.loads(response.choices[0].message.content)
            logger.info("Generated scholarship trend analysis")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing scholarship trends: {e}")
            return {"insights": "Analysis failed"}
    
    async def generate_chat_response(self, prompt: str, system_message: Optional[str] = None) -> str:
        """
        Generate a conversational AI response for Magic Onboarding
        """
        if not self.is_available():
            return "AI service is currently unavailable. Please try again later."
        
        try:
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            else:
                messages.append({"role": "system", "content": "You are a helpful, friendly AI assistant specializing in scholarship applications and student guidance."})
            
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating chat response: {e}")
            return "I apologize, but I'm having trouble responding right now. Please try again."

# Global service instance
openai_service = OpenAIService()