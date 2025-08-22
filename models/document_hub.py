# AI Scholarship Playbook - AI Document Hub Models
# OCR/NLP document processing for "upload once, use many"

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum
import uuid

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
    overall_gpa: Optional[float] = None
    gpa_scale: Optional[str] = "4.0"  # 4.0, 5.0, 100, etc.
    graduation_date: Optional[datetime] = None
    degree_program: Optional[str] = None
    major: Optional[str] = None
    minor: Optional[List[str]] = []
    
    # Course information
    courses: List[Dict[str, Any]] = []
    credits_completed: Optional[float] = None
    class_rank: Optional[str] = None
    honors: List[str] = []
    
    # Institution details
    institution_name: Optional[str] = None
    institution_type: Optional[str] = None  # university, college, community_college
    
class ExtractedPersonalData(BaseModel):
    """Personal information extracted from documents"""
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[Dict[str, str]] = None
    date_of_birth: Optional[datetime] = None
    citizenship_status: Optional[str] = None
    
class ExtractedFinancialData(BaseModel):
    """Financial information extracted from documents"""
    family_income: Optional[float] = None
    efc: Optional[float] = None  # Expected Family Contribution
    financial_aid_received: List[Dict[str, Any]] = []
    employment_income: Optional[float] = None
    assets: Optional[float] = None
    dependencies: Optional[int] = None

class ExtractedActivitiesData(BaseModel):
    """Activities and achievements extracted from resumes/essays"""
    work_experience: List[Dict[str, Any]] = []
    volunteer_experience: List[Dict[str, Any]] = []
    leadership_roles: List[Dict[str, Any]] = []
    awards_honors: List[Dict[str, Any]] = []
    clubs_organizations: List[str] = []
    research_experience: List[Dict[str, Any]] = []
    publications: List[str] = []
    skills: List[str] = []

class DocumentMetadata(BaseModel):
    """Metadata about processed document"""
    file_size: int  # bytes
    page_count: Optional[int] = None
    language: str = "en"
    encoding: Optional[str] = None
    creation_date: Optional[datetime] = None
    ocr_confidence: Optional[float] = None
    extraction_confidence: Optional[float] = None
    
class AIDocumentProcessingResult(BaseModel):
    """Complete AI processing results for a document"""
    document_id: str
    processing_status: ProcessingStatus
    document_type: DocumentType
    confidence_score: float = Field(ge=0.0, le=1.0)
    
    # Raw text extraction
    extracted_text: str
    structured_data: Dict[str, Any]
    
    # Classified extracted data
    academic_data: Optional[ExtractedAcademicData] = None
    personal_data: Optional[ExtractedPersonalData] = None
    financial_data: Optional[ExtractedFinancialData] = None
    activities_data: Optional[ExtractedActivitiesData] = None
    
    # AI insights
    document_summary: str
    key_highlights: List[str] = []
    potential_scholarship_matches: List[str] = []
    data_quality_score: float = Field(ge=0.0, le=1.0)
    
    # Processing metadata
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    processing_time_ms: Optional[int] = None
    ai_model_version: str = "gpt-4"

class DocumentUploadRequest(BaseModel):
    """Request to upload and process a document"""
    file_name: str
    file_size: int
    document_type: Optional[DocumentType] = DocumentType.OTHER
    description: Optional[str] = None
    tags: List[str] = []
    
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
    upload_url: Optional[str] = None  # Presigned URL if using cloud storage
    processing_started: bool = False
    estimated_processing_time: int  # seconds
    
class DocumentProcessingRequest(BaseModel):
    """Request to reprocess or update document processing"""
    document_id: str
    processing_options: Dict[str, Any] = {}
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
    usage_history: List[Dict[str, Any]] = []  # Where this doc was used
    
    # Document access
    download_url: Optional[str] = None
    view_url: Optional[str] = None
    
class DocumentUsageContext(BaseModel):
    """Context for how a document is being used"""
    usage_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    context_type: str  # scholarship_application, profile_update, verification
    scholarship_id: Optional[str] = None
    application_id: Optional[str] = None
    extracted_fields_used: List[str] = []
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class BulkDocumentAnalysis(BaseModel):
    """Analysis across multiple documents for a user"""
    user_id: str
    document_count: int
    total_data_points: int
    consistency_score: float = Field(ge=0.0, le=1.0)  # Data consistency across docs
    
    # Cross-document insights
    profile_completeness: float = Field(ge=0.0, le=1.0)
    data_conflicts: List[Dict[str, Any]] = []
    missing_document_types: List[DocumentType] = []
    recommended_uploads: List[str] = []
    
    # Quality assessment
    overall_quality_score: float = Field(ge=0.0, le=1.0)
    verification_needed: List[str] = []
    
class DocumentHubDashboard(BaseModel):
    """Dashboard view of user's document hub"""
    total_documents: int
    documents_by_type: Dict[DocumentType, int]
    processing_status_summary: Dict[ProcessingStatus, int]
    storage_used_mb: float
    
    # Actionable insights
    profile_improvement_opportunities: List[str] = []
    missing_documents_for_scholarships: List[Dict[str, Any]] = []
    document_update_recommendations: List[str] = []
    
    # Usage analytics
    most_used_documents: List[Dict[str, Any]] = []
    recent_activity: List[Dict[str, Any]] = []