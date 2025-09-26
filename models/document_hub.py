# AI Scholarship Playbook - AI Document Hub Models
# OCR/NLP document processing for "upload once, use many"

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    """Types of documents in the AI Document Hub"""
    TRANSCRIPT = "transcript"
    RESUME = "resume"
    CV = "cv"
    PERSONAL_STATEMENT = "personal_statement"
    ESSAY = "essay"
    RECOMMENDATION_LETTER = "recommendation_letter"
    FINANCIAL_AID_FORM = "financial_aid_form"
    TAX_DOCUMENT = "tax_document"
    SCHOLARSHIP_CERTIFICATE = "scholarship_certificate"
    ID_DOCUMENT = "id_document"
    OTHER = "other"

class ProcessingStatus(str, Enum):
    """Document processing status"""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    OCR_COMPLETE = "ocr_complete"
    NLP_ANALYZING = "nlp_analyzing"
    EXTRACTED = "extracted"
    READY = "ready"
    FAILED = "failed"
    ARCHIVED = "archived"

class DocumentFormat(str, Enum):
    """Supported document formats"""
    PDF = "pdf"
    PNG = "png"
    JPG = "jpg"
    JPEG = "jpeg"
    DOCX = "docx"
    DOC = "doc"
    TXT = "txt"

class ExtractedAcademicData(BaseModel):
    """Academic information extracted from transcripts"""
    overall_gpa: float | None = None
    gpa_scale: str | None = "4.0"  # 4.0, 5.0, 100, etc.
    graduation_date: datetime | None = None
    degree_program: str | None = None
    major: str | None = None
    minor: list[str] | None = []

    # Course information
    courses: list[dict[str, Any]] = []
    credits_completed: float | None = None
    class_rank: str | None = None
    honors: list[str] = []

    # Institution details
    institution_name: str | None = None
    institution_type: str | None = None  # university, college, community_college

class ExtractedPersonalData(BaseModel):
    """Personal information extracted from documents"""
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    address: dict[str, str] | None = None
    date_of_birth: datetime | None = None
    citizenship_status: str | None = None

class ExtractedFinancialData(BaseModel):
    """Financial information extracted from documents"""
    family_income: float | None = None
    efc: float | None = None  # Expected Family Contribution
    financial_aid_received: list[dict[str, Any]] = []
    employment_income: float | None = None
    assets: float | None = None
    dependencies: int | None = None

class ExtractedActivitiesData(BaseModel):
    """Activities and achievements extracted from resumes/essays"""
    work_experience: list[dict[str, Any]] = []
    volunteer_experience: list[dict[str, Any]] = []
    leadership_roles: list[dict[str, Any]] = []
    awards_honors: list[dict[str, Any]] = []
    clubs_organizations: list[str] = []
    research_experience: list[dict[str, Any]] = []
    publications: list[str] = []
    skills: list[str] = []

class DocumentMetadata(BaseModel):
    """Metadata about processed document"""
    file_size: int  # bytes
    page_count: int | None = None
    language: str = "en"
    encoding: str | None = None
    creation_date: datetime | None = None
    ocr_confidence: float | None = None
    extraction_confidence: float | None = None

class AIDocumentProcessingResult(BaseModel):
    """Complete AI processing results for a document"""
    document_id: str
    processing_status: ProcessingStatus
    document_type: DocumentType
    confidence_score: float = Field(ge=0.0, le=1.0)

    # Raw text extraction
    extracted_text: str
    structured_data: dict[str, Any]

    # Classified extracted data
    academic_data: ExtractedAcademicData | None = None
    personal_data: ExtractedPersonalData | None = None
    financial_data: ExtractedFinancialData | None = None
    activities_data: ExtractedActivitiesData | None = None

    # AI insights
    document_summary: str
    key_highlights: list[str] = []
    potential_scholarship_matches: list[str] = []
    data_quality_score: float = Field(ge=0.0, le=1.0)

    # Processing metadata
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    processing_time_ms: int | None = None
    ai_model_version: str = "gpt-4"

class DocumentUploadRequest(BaseModel):
    """Request to upload and process a document"""
    file_name: str
    file_size: int
    document_type: DocumentType | None = DocumentType.OTHER
    description: str | None = None
    tags: list[str] = []

    # Processing options
    extract_personal_data: bool = True
    extract_academic_data: bool = True
    extract_financial_data: bool = False  # Privacy sensitive
    extract_activities_data: bool = True

    # AI processing preferences
    ai_analysis_level: str = "comprehensive"  # basic, standard, comprehensive
    auto_profile_update: bool = True

class DocumentUploadResponse(BaseModel):
    """Response after document upload"""
    document_id: str
    upload_url: str | None = None  # Presigned URL if using cloud storage
    processing_started: bool = False
    estimated_processing_time: int  # seconds

class DocumentProcessingRequest(BaseModel):
    """Request to reprocess or update document processing"""
    document_id: str
    processing_options: dict[str, Any] = {}
    force_reprocess: bool = False

class DocumentRetrievalResponse(BaseModel):
    """Response when retrieving processed document"""
    document_id: str
    original_filename: str
    document_type: DocumentType
    upload_date: datetime
    last_processed: datetime

    # Processing results
    processing_result: AIDocumentProcessingResult
    usage_history: list[dict[str, Any]] = []  # Where this doc was used

    # Document access
    download_url: str | None = None
    view_url: str | None = None

class DocumentUsageContext(BaseModel):
    """Context for how a document is being used"""
    usage_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    context_type: str  # scholarship_application, profile_update, verification
    scholarship_id: str | None = None
    application_id: str | None = None
    extracted_fields_used: list[str] = []
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class BulkDocumentAnalysis(BaseModel):
    """Analysis across multiple documents for a user"""
    user_id: str
    document_count: int
    total_data_points: int
    consistency_score: float = Field(ge=0.0, le=1.0)  # Data consistency across docs

    # Cross-document insights
    profile_completeness: float = Field(ge=0.0, le=1.0)
    data_conflicts: list[dict[str, Any]] = []
    missing_document_types: list[DocumentType] = []
    recommended_uploads: list[str] = []

    # Quality assessment
    overall_quality_score: float = Field(ge=0.0, le=1.0)
    verification_needed: list[str] = []

class DocumentHubDashboard(BaseModel):
    """Dashboard view of user's document hub"""
    total_documents: int
    documents_by_type: dict[DocumentType, int]
    processing_status_summary: dict[ProcessingStatus, int]
    storage_used_mb: float

    # Actionable insights
    profile_improvement_opportunities: list[str] = []
    missing_documents_for_scholarships: list[dict[str, Any]] = []
    document_update_recommendations: list[str] = []

    # Usage analytics
    most_used_documents: list[dict[str, Any]] = []
    recent_activity: list[dict[str, Any]] = []
