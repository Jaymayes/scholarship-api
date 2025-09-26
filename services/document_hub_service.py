# AI Scholarship Playbook - Document Hub Service
# OCR/NLP document processing for "upload once, use many"

import asyncio
import json
import logging
import uuid
from datetime import datetime

from models.document_hub import (
    AIDocumentProcessingResult,
    BulkDocumentAnalysis,
    DocumentRetrievalResponse,
    DocumentType,
    DocumentUploadRequest,
    DocumentUploadResponse,
    ExtractedAcademicData,
    ExtractedActivitiesData,
    ExtractedPersonalData,
    ProcessingStatus,
)
from services.openai_service import OpenAIService

logger = logging.getLogger(__name__)

class DocumentHubService:
    """Service for AI-powered document processing and management"""

    def __init__(self, openai_service: OpenAIService):
        self.openai_service = openai_service
        self.processed_documents: dict[str, AIDocumentProcessingResult] = {}
        self.user_documents: dict[str, list[str]] = {}  # user_id -> [document_ids]

    async def upload_document(self, user_id: str, request: DocumentUploadRequest) -> DocumentUploadResponse:
        """
        Upload and initiate processing of a document
        """
        try:
            document_id = str(uuid.uuid4())

            # Validate file type and size
            if request.file_size > 50 * 1024 * 1024:  # 50MB limit
                raise ValueError("File size exceeds 50MB limit")

            # Initialize processing result
            processing_result = AIDocumentProcessingResult(
                document_id=document_id,
                processing_status=ProcessingStatus.UPLOADED,
                document_type=request.document_type,
                confidence_score=0.0,
                extracted_text="",
                structured_data={},
                document_summary="Processing...",
                key_highlights=[],
                potential_scholarship_matches=[],
                data_quality_score=0.0
            )

            # Store for processing
            self.processed_documents[document_id] = processing_result

            # Track user's documents
            if user_id not in self.user_documents:
                self.user_documents[user_id] = []
            self.user_documents[user_id].append(document_id)

            # Start background processing
            asyncio.create_task(self._process_document(document_id, request))

            return DocumentUploadResponse(
                document_id=document_id,
                upload_url=f"/api/v1/documents/{document_id}/upload",  # Presigned URL would go here
                processing_started=True,
                estimated_processing_time=30  # seconds
            )

        except Exception as e:
            logger.error(f"Failed to upload document: {str(e)}")
            raise

    async def _process_document(self, document_id: str, request: DocumentUploadRequest):
        """
        Process document using AI OCR and NLP
        """
        try:
            processing_result = self.processed_documents[document_id]
            processing_result.processing_status = ProcessingStatus.PROCESSING

            # Simulate OCR text extraction
            # In production, this would use actual OCR service (Tesseract, AWS Textract, etc.)
            extracted_text = await self._simulate_ocr_extraction(request.file_name, request.document_type)
            processing_result.extracted_text = extracted_text
            processing_result.processing_status = ProcessingStatus.OCR_COMPLETE

            # AI-powered document analysis
            if self.openai_service.is_available():
                await self._ai_document_analysis(processing_result, request)
            else:
                # Fallback processing without AI
                processing_result.document_summary = f"Document uploaded: {request.file_name}"
                processing_result.confidence_score = 0.5

            processing_result.processing_status = ProcessingStatus.READY
            processing_result.processed_at = datetime.utcnow()

            logger.info(f"Completed processing document {document_id}")

        except Exception as e:
            logger.error(f"Failed to process document {document_id}: {str(e)}")
            processing_result.processing_status = ProcessingStatus.FAILED

    async def _simulate_ocr_extraction(self, filename: str, doc_type: DocumentType) -> str:
        """
        Simulate OCR text extraction based on document type
        In production, this would use actual OCR services
        """
        if doc_type == DocumentType.TRANSCRIPT:
            return """
            OFFICIAL TRANSCRIPT
            Student: John Doe
            Student ID: 12345678

            Fall 2023 Semester
            MATH 101 - Calculus I                    A    4.0   4 credits
            PHYS 201 - Physics I                     A-   3.7   3 credits
            ENG 101 - English Composition            B+   3.3   3 credits
            CS 150 - Introduction to Programming     A    4.0   3 credits

            Semester GPA: 3.75
            Cumulative GPA: 3.75
            Total Credits: 13

            Dean's List: Fall 2023
            """
        if doc_type == DocumentType.RESUME:
            return """
            John Doe
            Computer Science Student
            Email: john.doe@university.edu
            Phone: (555) 123-4567

            EDUCATION
            Bachelor of Science in Computer Science
            State University, Expected Graduation: May 2025
            GPA: 3.75/4.0

            EXPERIENCE
            Software Engineering Intern - Tech Corp (Summer 2023)
            - Developed web applications using React and Node.js
            - Collaborated with team of 5 engineers

            ACTIVITIES
            - President, Computer Science Club (2023-2024)
            - Volunteer tutor, Math Learning Center (2022-2023)
            - Hackathon winner, University Innovation Challenge (2023)

            SKILLS
            Programming: Python, Java, JavaScript, React
            """
        return f"Document content for {filename} (Type: {doc_type})"

    async def _ai_document_analysis(self, processing_result: AIDocumentProcessingResult, request: DocumentUploadRequest):
        """
        Perform AI analysis of extracted document text
        """
        processing_result.processing_status = ProcessingStatus.NLP_ANALYZING

        try:
            # Generate document summary
            summary_prompt = f"""
            Analyze this {request.document_type} document and create a comprehensive summary:

            Document Text:
            {processing_result.extracted_text}

            Provide:
            1. A brief summary of the document
            2. Key highlights and achievements
            3. Relevant information for scholarship applications
            4. Data quality assessment

            Return JSON format with summary, highlights, and quality_score (0-1).
            """

            summary_response = await self.openai_service.generate_chat_response(summary_prompt)
            try:
                summary_data = json.loads(summary_response)
                processing_result.document_summary = summary_data.get("summary", "Document processed")
                processing_result.key_highlights = summary_data.get("highlights", [])
                processing_result.data_quality_score = summary_data.get("quality_score", 0.7)
            except json.JSONDecodeError:
                processing_result.document_summary = summary_response
                processing_result.data_quality_score = 0.6

            # Extract structured data based on document type
            if request.extract_academic_data and request.document_type in [DocumentType.TRANSCRIPT]:
                processing_result.academic_data = await self._extract_academic_data(processing_result.extracted_text)

            if request.extract_personal_data:
                processing_result.personal_data = await self._extract_personal_data(processing_result.extracted_text)

            if request.extract_activities_data and request.document_type in [DocumentType.RESUME, DocumentType.CV]:
                processing_result.activities_data = await self._extract_activities_data(processing_result.extracted_text)

            # Set confidence score based on extraction success
            extraction_success = sum([
                1 if processing_result.academic_data else 0,
                1 if processing_result.personal_data else 0,
                1 if processing_result.activities_data else 0
            ])
            processing_result.confidence_score = min(0.9, 0.3 + (extraction_success * 0.2))

        except Exception as e:
            logger.error(f"AI analysis failed for document {processing_result.document_id}: {str(e)}")
            processing_result.document_summary = "Document processed (limited AI analysis)"
            processing_result.confidence_score = 0.5

    async def _extract_academic_data(self, text: str) -> ExtractedAcademicData | None:
        """Extract academic information from document text"""
        try:
            extraction_prompt = f"""
            Extract academic information from this transcript text:

            {text}

            Return JSON with:
            - overall_gpa (number)
            - graduation_date (ISO date or null)
            - degree_program (string)
            - major (string)
            - institution_name (string)
            - courses (array of course objects)
            - honors (array of strings)

            Use null for missing information.
            """

            response = await self.openai_service.generate_chat_response(extraction_prompt)
            data = json.loads(response)

            return ExtractedAcademicData(
                overall_gpa=data.get("overall_gpa"),
                graduation_date=datetime.fromisoformat(data["graduation_date"]) if data.get("graduation_date") else None,
                degree_program=data.get("degree_program"),
                major=data.get("major"),
                institution_name=data.get("institution_name"),
                courses=data.get("courses", []),
                honors=data.get("honors", [])
            )

        except Exception as e:
            logger.warning(f"Failed to extract academic data: {str(e)}")
            return None

    async def _extract_personal_data(self, text: str) -> ExtractedPersonalData | None:
        """Extract personal information from document text"""
        try:
            extraction_prompt = f"""
            Extract personal contact information from this document:

            {text}

            Return JSON with:
            - full_name (string)
            - email (string)
            - phone (string)
            - address (object with street, city, state, zip)

            Use null for missing information. Be careful with PII.
            """

            response = await self.openai_service.generate_chat_response(extraction_prompt)
            data = json.loads(response)

            return ExtractedPersonalData(
                full_name=data.get("full_name"),
                email=data.get("email"),
                phone=data.get("phone"),
                address=data.get("address")
            )

        except Exception as e:
            logger.warning(f"Failed to extract personal data: {str(e)}")
            return None

    async def _extract_activities_data(self, text: str) -> ExtractedActivitiesData | None:
        """Extract activities and achievements from document text"""
        try:
            extraction_prompt = f"""
            Extract activities, experience, and achievements from this resume/CV:

            {text}

            Return JSON with:
            - work_experience (array of job objects)
            - volunteer_experience (array of volunteer objects)
            - leadership_roles (array of leadership objects)
            - awards_honors (array of award objects)
            - clubs_organizations (array of strings)
            - skills (array of strings)

            Use empty arrays for missing categories.
            """

            response = await self.openai_service.generate_chat_response(extraction_prompt)
            data = json.loads(response)

            return ExtractedActivitiesData(
                work_experience=data.get("work_experience", []),
                volunteer_experience=data.get("volunteer_experience", []),
                leadership_roles=data.get("leadership_roles", []),
                awards_honors=data.get("awards_honors", []),
                clubs_organizations=data.get("clubs_organizations", []),
                skills=data.get("skills", [])
            )

        except Exception as e:
            logger.warning(f"Failed to extract activities data: {str(e)}")
            return None

    async def get_document(self, document_id: str, user_id: str) -> DocumentRetrievalResponse:
        """Retrieve processed document"""
        try:
            if document_id not in self.processed_documents:
                raise ValueError("Document not found")

            # Verify user owns this document
            user_docs = self.user_documents.get(user_id, [])
            if document_id not in user_docs:
                raise ValueError("Access denied to document")

            processing_result = self.processed_documents[document_id]

            return DocumentRetrievalResponse(
                document_id=document_id,
                original_filename="document.pdf",  # Would be stored in metadata
                document_type=processing_result.document_type,
                upload_date=datetime.utcnow(),  # Would be stored in metadata
                last_processed=processing_result.processed_at,
                processing_result=processing_result,
                usage_history=[],  # Would track where document was used
                download_url=f"/api/v1/documents/{document_id}/download",
                view_url=f"/api/v1/documents/{document_id}/view"
            )

        except Exception as e:
            logger.error(f"Failed to retrieve document {document_id}: {str(e)}")
            raise

    async def analyze_user_documents(self, user_id: str) -> BulkDocumentAnalysis:
        """Analyze all documents for a user to provide insights"""
        try:
            user_doc_ids = self.user_documents.get(user_id, [])
            documents = [self.processed_documents[doc_id] for doc_id in user_doc_ids
                        if doc_id in self.processed_documents]

            if not documents:
                return BulkDocumentAnalysis(
                    user_id=user_id,
                    document_count=0,
                    total_data_points=0,
                    consistency_score=1.0,
                    profile_completeness=0.0,
                    overall_quality_score=0.0
                )

            # Calculate metrics
            total_data_points = sum(len(doc.structured_data) for doc in documents)
            avg_quality = sum(doc.data_quality_score for doc in documents) / len(documents)

            # Identify missing document types
            present_types = {doc.document_type for doc in documents}
            all_important_types = {DocumentType.TRANSCRIPT, DocumentType.RESUME, DocumentType.PERSONAL_STATEMENT}
            missing_types = list(all_important_types - present_types)

            return BulkDocumentAnalysis(
                user_id=user_id,
                document_count=len(documents),
                total_data_points=total_data_points,
                consistency_score=0.85,  # Would calculate based on data consistency
                profile_completeness=len(present_types) / len(all_important_types),
                missing_document_types=missing_types,
                recommended_uploads=[f"Upload your {doc_type.value}" for doc_type in missing_types],
                overall_quality_score=avg_quality,
                verification_needed=[]
            )

        except Exception as e:
            logger.error(f"Failed to analyze documents for user {user_id}: {str(e)}")
            raise
