from datetime import datetime, timedelta
from models.scholarship import (
    Scholarship, EligibilityCriteria, ScholarshipType, FieldOfStudy
)

# Mock scholarship data as requested in success criteria
MOCK_SCHOLARSHIPS = [
    Scholarship(
        id="sch_001",
        name="National Merit Engineering Scholarship",
        organization="Engineering Excellence Foundation",
        description="A prestigious scholarship for outstanding engineering students who demonstrate academic excellence, leadership qualities, and commitment to innovation. This scholarship supports students pursuing degrees in various engineering disciplines including mechanical, electrical, civil, and computer engineering.",
        amount=15000.0,
        max_awards=50,
        application_deadline=datetime(2025, 12, 15),
        notification_date=datetime(2026, 2, 1),
        scholarship_type=ScholarshipType.MERIT_BASED,
        eligibility_criteria=EligibilityCriteria(
            min_gpa=3.5,
            max_gpa=None,
            grade_levels=["undergraduate", "graduate"],
            citizenship_required="US",
            min_age=None,
            max_age=None,
            financial_need=None,
            fields_of_study=[FieldOfStudy.ENGINEERING, FieldOfStudy.TECHNOLOGY],
            essay_required=True,
            recommendation_letters=2
        ),
        application_url="https://example.com/apply/engineering-scholarship",
        contact_email="scholarships@engineering-excellence.org",
        renewable=True
    ),
    
    Scholarship(
        id="sch_002", 
        name="Future Healthcare Leaders Award",
        organization="Medical Professionals Association",
        description="Supporting the next generation of healthcare professionals through financial assistance and mentorship opportunities. Open to students pursuing careers in medicine, nursing, pharmacy, physical therapy, and other healthcare fields.",
        amount=8000.0,
        max_awards=25,
        application_deadline=datetime(2025, 11, 30),
        notification_date=datetime(2026, 1, 15),
        scholarship_type=ScholarshipType.ACADEMIC_ACHIEVEMENT,
        eligibility_criteria=EligibilityCriteria(
            min_gpa=3.2,
            max_gpa=None,
            grade_levels=["undergraduate", "graduate"],
            citizenship_required="US",
            residency_states=["CA", "NY", "TX", "FL", "IL"],
            min_age=18,
            max_age=30,
            financial_need=None,
            fields_of_study=[FieldOfStudy.MEDICINE, FieldOfStudy.SCIENCE],
            essay_required=True,
            recommendation_letters=3
        ),
        application_url="https://example.com/apply/healthcare-scholarship",
        contact_email="awards@medical-professionals.org"
    ),
    
    Scholarship(
        id="sch_003",
        name="Business Innovation Grant",
        organization="Entrepreneurship Institute",
        description="Encouraging entrepreneurial spirit and business innovation among students. This scholarship is designed for students who have demonstrated leadership in business ventures, startup experience, or innovative business ideas.",
        amount=12000.0,
        max_awards=30,
        application_deadline=datetime(2025, 10, 31),
        notification_date=datetime(2025, 12, 15),
        scholarship_type=ScholarshipType.MERIT_BASED,
        eligibility_criteria=EligibilityCriteria(
            min_gpa=3.0,
            max_gpa=None,
            grade_levels=["undergraduate", "graduate"],
            citizenship_required=None,
            min_age=None,
            max_age=None,
            financial_need=None,
            fields_of_study=[FieldOfStudy.BUSINESS],
            essay_required=True,
            recommendation_letters=1
        ),
        application_url="https://example.com/apply/business-innovation",
        contact_email="grants@entrepreneurship-institute.org",
        renewable=True
    ),
    
    Scholarship(
        id="sch_004",
        name="Need-Based Student Support Fund",
        organization="Community Education Foundation",
        description="Providing financial assistance to students from low-income families who demonstrate financial need and academic potential. This scholarship aims to remove financial barriers to higher education.",
        amount=5000.0,
        max_awards=100,
        application_deadline=datetime(2026, 3, 1),
        notification_date=datetime(2026, 4, 15),
        scholarship_type=ScholarshipType.NEED_BASED,
        eligibility_criteria=EligibilityCriteria(
            min_gpa=2.5,
            max_gpa=None,
            grade_levels=["undergraduate"],
            citizenship_required="US",
            max_age=None,
            min_age=None,
            financial_need=True,
            essay_required=True,
            recommendation_letters=2
        ),
        application_url="https://example.com/apply/need-based-support",
        contact_email="support@community-education.org",
        renewable=True
    ),
    
    Scholarship(
        id="sch_005",
        name="Arts and Creativity Scholarship",
        organization="Creative Arts Society",
        description="Supporting talented students in visual arts, performing arts, creative writing, and digital media. Recipients must demonstrate exceptional artistic ability and commitment to their craft.",
        amount=7500.0,
        max_awards=20,
        application_deadline=datetime(2026, 1, 15),
        notification_date=datetime(2026, 3, 1),
        scholarship_type=ScholarshipType.MERIT_BASED,
        eligibility_criteria=EligibilityCriteria(
            min_gpa=2.8,
            max_gpa=None,
            grade_levels=["undergraduate", "graduate"],
            citizenship_required=None,
            max_age=None,
            min_age=None,
            financial_need=None,
            fields_of_study=[FieldOfStudy.ARTS],
            essay_required=True,
            recommendation_letters=2
        ),
        application_url="https://example.com/apply/arts-creativity",
        contact_email="scholarships@creative-arts-society.org"
    ),
    
    Scholarship(
        id="sch_006",
        name="STEM Excellence Award",
        organization="Science & Technology Foundation",
        description="Recognizing outstanding achievements in Science, Technology, Engineering, and Mathematics. This award supports students who have demonstrated excellence in STEM fields and plan to pursue careers in scientific research or technology development.",
        amount=20000.0,
        max_awards=15,
        application_deadline=datetime(2025, 12, 31),
        notification_date=datetime(2026, 2, 15),
        scholarship_type=ScholarshipType.ACADEMIC_ACHIEVEMENT,
        eligibility_criteria=EligibilityCriteria(
            min_gpa=3.7,
            max_gpa=None,
            grade_levels=["undergraduate", "graduate"],
            citizenship_required="US",
            max_age=None,
            min_age=None,
            financial_need=None,
            fields_of_study=[FieldOfStudy.SCIENCE, FieldOfStudy.TECHNOLOGY, FieldOfStudy.ENGINEERING],
            essay_required=True,
            recommendation_letters=3
        ),
        application_url="https://example.com/apply/stem-excellence",
        contact_email="awards@stem-foundation.org",
        renewable=True
    ),
    
    Scholarship(
        id="sch_007",
        name="Community Service Leadership Award",
        organization="Civic Engagement Alliance",
        description="Honoring students who have made significant contributions to their communities through volunteer work and civic engagement. This scholarship recognizes leadership in community service and social impact initiatives.",
        amount=6000.0,
        max_awards=40,
        application_deadline=datetime(2026, 2, 28),
        notification_date=datetime(2026, 4, 1),
        scholarship_type=ScholarshipType.COMMUNITY_SERVICE,
        eligibility_criteria=EligibilityCriteria(
            min_gpa=3.0,
            max_gpa=None,
            grade_levels=["undergraduate"],
            citizenship_required="US",
            max_age=None,
            min_age=None,
            essay_required=True,
            recommendation_letters=2
        ),
        application_url="https://example.com/apply/community-service",
        contact_email="awards@civic-engagement.org"
    ),
    
    Scholarship(
        id="sch_008",
        name="First-Generation College Student Grant",
        organization="Educational Access Foundation",
        description="Supporting first-generation college students who are the first in their families to pursue higher education. This grant provides financial assistance and mentorship to help students succeed in their academic journey.",
        amount=4500.0,
        max_awards=75,
        application_deadline=datetime(2026, 4, 30),
        notification_date=datetime(2026, 6, 15),
        scholarship_type=ScholarshipType.NEED_BASED,
        eligibility_criteria=EligibilityCriteria(
            min_gpa=2.5,
            max_gpa=None,
            grade_levels=["undergraduate"],
            citizenship_required="US",
            max_age=None,
            min_age=None,
            financial_need=True,
            essay_required=True,
            recommendation_letters=1
        ),
        application_url="https://example.com/apply/first-generation",
        contact_email="grants@educational-access.org",
        renewable=True
    ),
    
    Scholarship(
        id="sch_009",
        name="International Student Excellence Award",
        organization="Global Education Initiative",
        description="Supporting outstanding international students pursuing higher education in the United States. This award recognizes academic excellence and cross-cultural leadership among international students.",
        amount=10000.0,
        max_awards=25,
        application_deadline=datetime(2025, 11, 15),
        notification_date=datetime(2026, 1, 1),
        scholarship_type=ScholarshipType.MERIT_BASED,
        eligibility_criteria=EligibilityCriteria(
            min_gpa=3.4,
            max_gpa=None,
            grade_levels=["undergraduate", "graduate"],
            citizenship_required=None,
            max_age=None,
            min_age=None,
            essay_required=True,
            recommendation_letters=2
        ),
        application_url="https://example.com/apply/international-excellence",
        contact_email="international@global-education.org"
    ),
    
    Scholarship(
        id="sch_010",
        name="Women in Technology Scholarship",
        organization="Tech Diversity Coalition",
        description="Encouraging women to pursue careers in technology and computer science. This scholarship supports female students in STEM fields with a focus on technology, programming, and digital innovation.",
        amount=9000.0,
        max_awards=35,
        application_deadline=datetime(2025, 12, 1),
        notification_date=datetime(2026, 1, 30),
        scholarship_type=ScholarshipType.MINORITY,
        eligibility_criteria=EligibilityCriteria(
            min_gpa=3.2,
            max_gpa=None,
            grade_levels=["undergraduate", "graduate"],
            citizenship_required="US",
            max_age=None,
            min_age=None,
            financial_need=None,
            fields_of_study=[FieldOfStudy.TECHNOLOGY, FieldOfStudy.ENGINEERING, FieldOfStudy.SCIENCE],
            essay_required=True,
            recommendation_letters=2
        ),
        application_url="https://example.com/apply/women-in-tech",
        contact_email="scholarships@tech-diversity.org",
        renewable=True
    ),
    
    Scholarship(
        id="sch_011",
        name="Rural Community Education Fund",
        organization="Rural Development Alliance",
        description="Supporting students from rural communities who face unique challenges in accessing higher education. This fund provides financial assistance to help rural students pursue their educational goals.",
        amount=3500.0,
        max_awards=60,
        application_deadline=datetime(2026, 3, 15),
        notification_date=datetime(2026, 5, 1),
        scholarship_type=ScholarshipType.NEED_BASED,
        eligibility_criteria=EligibilityCriteria(
            min_gpa=2.7,
            max_gpa=None,
            grade_levels=["undergraduate"],
            citizenship_required="US",
            residency_states=["MT", "WY", "ND", "SD", "NE", "KS", "OK", "TX", "NM"],
            max_age=None,
            min_age=None,
            financial_need=True,
            essay_required=True,
            recommendation_letters=1
        ),
        application_url="https://example.com/apply/rural-education",
        contact_email="rural-fund@development-alliance.org",
        renewable=True
    ),
    
    Scholarship(
        id="sch_012",
        name="Graduate Research Excellence Award",
        organization="Academic Research Council",
        description="Supporting exceptional graduate students conducting groundbreaking research across various disciplines. This award recognizes students whose research has the potential for significant academic and societal impact.",
        amount=18000.0,
        max_awards=12,
        application_deadline=datetime(2025, 10, 15),
        notification_date=datetime(2025, 12, 1),
        scholarship_type=ScholarshipType.ACADEMIC_ACHIEVEMENT,
        eligibility_criteria=EligibilityCriteria(
            min_gpa=3.8,
            max_gpa=None,
            grade_levels=["graduate"],
            citizenship_required=None,
            max_age=None,
            min_age=None,
            essay_required=True,
            recommendation_letters=3
        ),
        application_url="https://example.com/apply/graduate-research",
        contact_email="research-awards@academic-council.org"
    ),
    
    Scholarship(
        id="sch_013",
        name="Legal Studies Scholarship",
        organization="Justice Education Foundation",
        description="Supporting students pursuing legal education and careers in law. This scholarship is available to pre-law undergraduates and law school students who demonstrate academic excellence and commitment to justice.",
        amount=11000.0,
        max_awards=20,
        application_deadline=datetime(2026, 1, 31),
        notification_date=datetime(2026, 3, 15),
        scholarship_type=ScholarshipType.MERIT_BASED,
        eligibility_criteria=EligibilityCriteria(
            min_gpa=3.4,
            max_gpa=None,
            grade_levels=["undergraduate", "graduate"],
            citizenship_required="US",
            max_age=None,
            min_age=None,
            financial_need=None,
            fields_of_study=[FieldOfStudy.LAW],
            essay_required=True,
            recommendation_letters=2
        ),
        application_url="https://example.com/apply/legal-studies",
        contact_email="legal-scholarships@justice-education.org"
    ),
    
    Scholarship(
        id="sch_014",
        name="Social Sciences Research Grant",
        organization="Behavioral Research Institute",
        description="Funding research projects in psychology, sociology, anthropology, and related social science fields. This grant supports students conducting innovative research that contributes to our understanding of human behavior and society.",
        amount=6500.0,
        max_awards=30,
        application_deadline=datetime(2026, 2, 15),
        notification_date=datetime(2026, 4, 1),
        scholarship_type=ScholarshipType.ACADEMIC_ACHIEVEMENT,
        eligibility_criteria=EligibilityCriteria(
            min_gpa=3.3,
            max_gpa=None,
            grade_levels=["undergraduate", "graduate"],
            citizenship_required=None,
            max_age=None,
            min_age=None,
            financial_need=None,
            fields_of_study=[FieldOfStudy.SOCIAL_SCIENCES],
            essay_required=True,
            recommendation_letters=2
        ),
        application_url="https://example.com/apply/social-sciences",
        contact_email="grants@behavioral-research.org"
    ),
    
    Scholarship(
        id="sch_015",
        name="Athletic Academic Achievement Award",
        organization="Student Athlete Foundation",
        description="Recognizing student-athletes who excel both in their sport and in the classroom. This award supports student-athletes who demonstrate outstanding academic performance while participating in competitive sports.",
        amount=7000.0,
        max_awards=45,
        application_deadline=datetime(2025, 11, 30),
        notification_date=datetime(2026, 1, 15),
        scholarship_type=ScholarshipType.ATHLETIC,
        eligibility_criteria=EligibilityCriteria(
            min_gpa=3.0,
            max_gpa=None,
            grade_levels=["undergraduate"],
            citizenship_required="US",
            max_age=None,
            min_age=None,
            essay_required=True,
            recommendation_letters=2
        ),
        application_url="https://example.com/apply/athletic-academic",
        contact_email="athletics@student-athlete-foundation.org",
        renewable=True
    )
]
