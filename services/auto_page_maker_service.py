# AI Scholarship Playbook - Auto Page Maker Engine
# Programmatic SEO content generation with quality gates

import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import json
import asyncio

from models.scholarship import Scholarship
from services.openai_service import OpenAIService
from utils.logger import get_logger

logger = get_logger(__name__)

class ContentQualityAssurance:
    """Quality assessment for programmatic content"""
    
    @staticmethod
    def calculate_readability_score(text: str) -> float:
        """Calculate Flesch-Kincaid readability score"""
        sentences = len(re.findall(r'[.!?]+', text))
        words = len(text.split())
        syllables = sum([ContentQualityAssurance._count_syllables(word) for word in text.split()])
        
        if sentences == 0 or words == 0:
            return 0.0
        
        # Flesch Reading Ease formula
        score = 206.835 - (1.015 * (words / sentences)) - (84.6 * (syllables / words))
        return max(0.0, min(100.0, score))
    
    @staticmethod
    def _count_syllables(word: str) -> int:
        """Count syllables in a word"""
        word = word.lower()
        vowels = "aeiouy"
        syllables = 0
        prev_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_was_vowel:
                syllables += 1
            prev_was_vowel = is_vowel
        
        return max(1, syllables)
    
    @staticmethod
    def assess_uniqueness(content: str, existing_content: List[str]) -> float:
        """Assess content uniqueness against existing content"""
        if not existing_content:
            return 1.0
        
        content_words = set(content.lower().split())
        similarities = []
        
        for existing in existing_content:
            existing_words = set(existing.lower().split())
            if len(content_words) == 0 or len(existing_words) == 0:
                similarities.append(0.0)
                continue
            
            intersection = len(content_words.intersection(existing_words))
            union = len(content_words.union(existing_words))
            similarity = intersection / union if union > 0 else 0
            similarities.append(similarity)
        
        # Return inverse of maximum similarity
        max_similarity = max(similarities) if similarities else 0
        return 1.0 - max_similarity
    
    @staticmethod
    def assess_value_score(content: str) -> float:
        """Assess content value based on actionable information"""
        value_indicators = [
            "application deadline", "requirements", "eligibility", "how to apply",
            "tips", "strategy", "checklist", "step-by-step", "example",
            "award amount", "selection criteria", "contact information"
        ]
        
        content_lower = content.lower()
        found_indicators = sum(1 for indicator in value_indicators if indicator in content_lower)
        
        # Score based on presence of value indicators
        max_indicators = len(value_indicators)
        base_score = found_indicators / max_indicators
        
        # Bonus for length (comprehensive content)
        length_bonus = min(0.3, len(content) / 5000)  # Up to 30% bonus for 5000+ chars
        
        return min(1.0, base_score + length_bonus)

class ScholarshipPageGenerator:
    """Generate individual scholarship pages"""
    
    def __init__(self, openai_service: OpenAIService):
        self.openai_service = openai_service
        self.qa = ContentQualityAssurance()
    
    async def generate_scholarship_page(self, scholarship: Scholarship) -> Dict[str, Any]:
        """Generate comprehensive scholarship page content"""
        try:
            # Generate main content sections
            overview_section = await self._generate_overview_section(scholarship)
            eligibility_section = await self._generate_eligibility_section(scholarship)
            application_section = await self._generate_application_section(scholarship)
            strategy_section = await self._generate_strategy_section(scholarship)
            
            # Combine sections
            full_content = f"{overview_section}\n\n{eligibility_section}\n\n{application_section}\n\n{strategy_section}"
            
            # Generate SEO metadata
            seo_metadata = await self._generate_seo_metadata(scholarship, full_content)
            
            # Assess content quality
            quality_score = self._assess_content_quality(full_content)
            
            return {
                "scholarship_id": scholarship.id,
                "slug": self._generate_slug(scholarship.title),
                "title": seo_metadata["title"],
                "meta_description": seo_metadata["meta_description"],
                "content": {
                    "overview": overview_section,
                    "eligibility": eligibility_section,
                    "application": application_section,
                    "strategy": strategy_section,
                    "full_content": full_content
                },
                "seo": seo_metadata,
                "quality": quality_score,
                "word_count": len(full_content.split()),
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate page for scholarship {scholarship.id}: {str(e)}")
            raise
    
    async def _generate_overview_section(self, scholarship: Scholarship) -> str:
        """Generate scholarship overview section"""
        prompt = f"""
        Write a comprehensive overview section for the {scholarship.title} scholarship page.
        
        Scholarship Details:
        - Title: {scholarship.title}
        - Award Amount: ${scholarship.amount:,}
        - Deadline: {scholarship.deadline.strftime('%B %d, %Y')}
        - Organization: {scholarship.organization}
        - Description: {scholarship.description}
        
        Create an engaging overview that includes:
        1. Clear scholarship summary and value proposition
        2. Key details (amount, deadline, organization)
        3. Who should apply (target audience)
        4. Why this scholarship matters
        
        Write in a helpful, informative tone. Use specific details. Keep it 300-400 words.
        """
        
        response = await self.openai_service.generate_completion(prompt)
        return response.strip()
    
    async def _generate_eligibility_section(self, scholarship: Scholarship) -> str:
        """Generate detailed eligibility section"""
        prompt = f"""
        Create a detailed eligibility requirements section for {scholarship.title}.
        
        Scholarship Context:
        - Award: ${scholarship.amount:,}
        - Field: {getattr(scholarship, 'field_of_study', 'General')}
        - Organization: {scholarship.organization}
        
        Include:
        1. Academic requirements (GPA, grade level, etc.)
        2. Demographic requirements (if applicable)
        3. Field of study requirements
        4. Other specific criteria
        5. Common eligibility misconceptions to avoid
        
        Format as clear sections with bullet points. Be specific and actionable.
        Target 250-300 words.
        """
        
        response = await self.openai_service.generate_completion(prompt)
        return response.strip()
    
    async def _generate_application_section(self, scholarship: Scholarship) -> str:
        """Generate application process section"""
        prompt = f"""
        Write a comprehensive application guide for {scholarship.title}.
        
        Details:
        - Deadline: {scholarship.deadline.strftime('%B %d, %Y')}
        - Award: ${scholarship.amount:,}
        - Organization: {scholarship.organization}
        
        Cover:
        1. Application timeline and key dates
        2. Required materials and documents
        3. Step-by-step application process
        4. Common application mistakes to avoid
        5. Tips for standing out
        
        Make it actionable with specific steps. Include deadline reminders.
        Target 350-400 words.
        """
        
        response = await self.openai_service.generate_completion(prompt)
        return response.strip()
    
    async def _generate_strategy_section(self, scholarship: Scholarship) -> str:
        """Generate application strategy section"""
        prompt = f"""
        Create a strategic application advice section for {scholarship.title}.
        
        Scholarship Profile:
        - Amount: ${scholarship.amount:,}
        - Organization: {scholarship.organization}
        - Competitiveness: {"High" if scholarship.amount > 5000 else "Medium"}
        
        Include:
        1. Competition analysis and win likelihood factors
        2. What selection committees look for
        3. How to position your application effectively
        4. Related scholarships to also consider
        5. Success timeline and follow-up steps
        
        Focus on strategic insights that help applicants succeed.
        Target 250-300 words.
        """
        
        response = await self.openai_service.generate_completion(prompt)
        return response.strip()
    
    async def _generate_seo_metadata(self, scholarship: Scholarship, content: str) -> Dict[str, Any]:
        """Generate SEO-optimized metadata"""
        
        # Generate SEO title
        title = f"{scholarship.title} - ${scholarship.amount:,} Scholarship Application Guide"
        if len(title) > 60:
            title = f"{scholarship.title} - Application Guide"
        
        # Generate meta description
        description = f"Apply for the ${scholarship.amount:,} {scholarship.title}. Complete eligibility requirements, application process, and winning strategies. Deadline: {scholarship.deadline.strftime('%B %d, %Y')}."
        if len(description) > 160:
            description = f"${scholarship.amount:,} {scholarship.title} application guide. Requirements, process, and strategies to win."
        
        # Extract keywords
        keywords = [
            scholarship.title.lower(),
            f"{scholarship.title.lower()} scholarship",
            f"${scholarship.amount} scholarship",
            scholarship.organization.lower(),
            "scholarship application",
            "eligibility requirements"
        ]
        
        # Generate structured data
        structured_data = {
            "@context": "https://schema.org/",
            "@type": "FinancialProduct",
            "name": scholarship.title,
            "description": scholarship.description,
            "provider": {
                "@type": "Organization",
                "name": scholarship.organization
            },
            "amount": {
                "@type": "MonetaryAmount",
                "currency": "USD",
                "value": scholarship.amount
            },
            "applicationDeadline": scholarship.deadline.isoformat()
        }
        
        return {
            "title": title,
            "meta_description": description,
            "keywords": keywords,
            "structured_data": structured_data,
            "canonical_url": f"/scholarships/{self._generate_slug(scholarship.title)}",
            "og_title": title,
            "og_description": description,
            "og_type": "article"
        }
    
    def _generate_slug(self, title: str) -> str:
        """Generate URL-friendly slug"""
        slug = re.sub(r'[^\w\s-]', '', title.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')
    
    def _assess_content_quality(self, content: str) -> Dict[str, float]:
        """Assess overall content quality"""
        return {
            "readability_score": self.qa.calculate_readability_score(content),
            "value_score": self.qa.assess_value_score(content),
            "word_count": len(content.split()),
            "overall_score": (self.qa.calculate_readability_score(content) * 0.3 + 
                            self.qa.assess_value_score(content) * 0.7) / 100
        }

class CategoryLandingPageGenerator:
    """Generate category-specific landing pages"""
    
    def __init__(self, openai_service: OpenAIService):
        self.openai_service = openai_service
    
    async def generate_category_page(self, category: str, scholarships: List[Scholarship]) -> Dict[str, Any]:
        """Generate category landing page (e.g., STEM scholarships)"""
        
        # Calculate category stats
        total_amount = sum(s.amount for s in scholarships)
        avg_amount = total_amount / len(scholarships) if scholarships else 0
        upcoming_deadlines = [s for s in scholarships if s.deadline > datetime.now()]
        
        prompt = f"""
        Create a comprehensive landing page for "{category}" scholarships.
        
        Category Stats:
        - Total scholarships available: {len(scholarships)}
        - Combined award value: ${total_amount:,}
        - Average award: ${avg_amount:,.0f}
        - Upcoming deadlines: {len(upcoming_deadlines)}
        
        Create content including:
        1. Category overview and importance
        2. Types of students who should apply
        3. Key benefits and career impact
        4. Application strategy for this category
        5. Success stories and inspiration
        6. Timeline and planning advice
        
        Write 800-1000 words that are helpful and motivating.
        Focus on actionable insights specific to {category} students.
        """
        
        content = await self.openai_service.generate_completion(prompt)
        
        # Generate scholarship highlights
        top_scholarships = sorted(scholarships, key=lambda s: s.amount, reverse=True)[:5]
        highlights = []
        
        for scholarship in top_scholarships:
            highlights.append({
                "title": scholarship.title,
                "amount": scholarship.amount,
                "deadline": scholarship.deadline.isoformat(),
                "organization": scholarship.organization,
                "slug": self._generate_slug(scholarship.title)
            })
        
        return {
            "category": category,
            "slug": self._generate_slug(f"{category}-scholarships"),
            "title": f"{category} Scholarships - Find Your Perfect Match",
            "meta_description": f"Discover {len(scholarships)} {category.lower()} scholarships worth ${total_amount:,}. Application guides, deadlines, and winning strategies.",
            "content": content,
            "highlights": highlights,
            "stats": {
                "total_scholarships": len(scholarships),
                "total_amount": total_amount,
                "average_amount": avg_amount,
                "upcoming_count": len(upcoming_deadlines)
            },
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def _generate_slug(self, title: str) -> str:
        """Generate URL-friendly slug"""
        slug = re.sub(r'[^\w\s-]', '', title.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')

class AutoPageMakerService:
    """Main service for automated SEO page generation"""
    
    def __init__(self, openai_service: OpenAIService):
        self.openai_service = openai_service
        self.scholarship_generator = ScholarshipPageGenerator(openai_service)
        self.category_generator = CategoryLandingPageGenerator(openai_service)
        self.generated_pages = []
        self.sitemap_entries = []
    
    async def generate_programmatic_pages(self, scholarships: List[Scholarship]) -> Dict[str, Any]:
        """Generate all programmatic pages for SEO"""
        try:
            logger.info(f"Starting programmatic page generation for {len(scholarships)} scholarships")
            
            results = {
                "individual_pages": [],
                "category_pages": [],
                "comparison_pages": [],
                "stats": {
                    "total_pages": 0,
                    "total_word_count": 0,
                    "average_quality_score": 0,
                    "generation_time": 0
                }
            }
            
            start_time = datetime.utcnow()
            
            # Generate individual scholarship pages
            for scholarship in scholarships[:50]:  # Start with 50 for demo
                try:
                    page_data = await self.scholarship_generator.generate_scholarship_page(scholarship)
                    results["individual_pages"].append(page_data)
                    self.sitemap_entries.append({
                        "url": f"/scholarships/{page_data['slug']}",
                        "lastmod": datetime.utcnow().isoformat(),
                        "priority": 0.8
                    })
                except Exception as e:
                    logger.warning(f"Failed to generate page for scholarship {scholarship.id}: {str(e)}")
                    continue
            
            # Generate category landing pages
            categories = ["STEM", "Women in Technology", "First-Generation College", "Community Service", "Academic Merit"]
            for category in categories:
                category_scholarships = [s for s in scholarships if self._matches_category(s, category)]
                if category_scholarships:
                    try:
                        page_data = await self.category_generator.generate_category_page(category, category_scholarships)
                        results["category_pages"].append(page_data)
                        self.sitemap_entries.append({
                            "url": f"/scholarships/{page_data['slug']}",
                            "lastmod": datetime.utcnow().isoformat(),
                            "priority": 0.9
                        })
                    except Exception as e:
                        logger.warning(f"Failed to generate category page for {category}: {str(e)}")
                        continue
            
            # Calculate final stats
            all_pages = results["individual_pages"] + results["category_pages"]
            results["stats"] = {
                "total_pages": len(all_pages),
                "total_word_count": sum(p.get("word_count", 0) for p in all_pages),
                "average_quality_score": sum(p.get("quality", {}).get("overall_score", 0) for p in all_pages) / len(all_pages) if all_pages else 0,
                "generation_time": (datetime.utcnow() - start_time).total_seconds()
            }
            
            # Generate sitemap
            await self._generate_sitemap()
            
            logger.info(f"Generated {results['stats']['total_pages']} pages in {results['stats']['generation_time']:.1f} seconds")
            return results
            
        except Exception as e:
            logger.error(f"Failed to generate programmatic pages: {str(e)}")
            raise
    
    def _matches_category(self, scholarship: Scholarship, category: str) -> bool:
        """Check if scholarship matches category"""
        title_lower = scholarship.title.lower()
        desc_lower = scholarship.description.lower()
        
        category_keywords = {
            "STEM": ["stem", "science", "technology", "engineering", "math", "computer", "data"],
            "Women in Technology": ["women", "female", "technology", "computer", "engineering"],
            "First-Generation College": ["first-generation", "first generation", "first-gen"],
            "Community Service": ["community", "service", "volunteer", "civic"],
            "Academic Merit": ["academic", "merit", "gpa", "achievement", "excellence"]
        }
        
        keywords = category_keywords.get(category, [])
        return any(keyword in title_lower or keyword in desc_lower for keyword in keywords)
    
    async def _generate_sitemap(self) -> str:
        """Generate XML sitemap for generated pages"""
        sitemap_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
        sitemap_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        
        for entry in self.sitemap_entries:
            sitemap_content += f'  <url>\n'
            sitemap_content += f'    <loc>https://scholarship-api.jamarrlmayes.replit.app{entry["url"]}</loc>\n'
            sitemap_content += f'    <lastmod>{entry["lastmod"]}</lastmod>\n'
            sitemap_content += f'    <priority>{entry["priority"]}</priority>\n'
            sitemap_content += f'  </url>\n'
        
        sitemap_content += '</urlset>'
        
        # Save sitemap
        with open("sitemap.xml", "w") as f:
            f.write(sitemap_content)
        
        return sitemap_content
    
    async def get_seo_performance_metrics(self) -> Dict[str, Any]:
        """Get SEO performance metrics for generated content"""
        # In production, this would integrate with Google Search Console
        return {
            "pages_generated": len(self.generated_pages),
            "pages_indexed": 0,  # Would be populated by GSC API
            "total_impressions": 0,
            "total_clicks": 0,
            "average_ctr": 0,
            "average_position": 0,
            "index_coverage": 0
        }