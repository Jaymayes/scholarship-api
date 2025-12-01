"""
Legal Pages Router for Scholar AI Advisor - scholarship_api

Implements:
- GET /privacy - Privacy Policy
- GET /terms - Terms of Service
- GET /accessibility - Accessibility Statement

Per Unified Business + Legal Pages specification.
"""

from datetime import date
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["Legal"])

BRAND_NAME = "Scholar AI Advisor"
COMPANY_LEGAL_NAME = "Referral Service LLC"
MAIN_SITE_URL = "https://scholaraiadvisor.com"
CONTACT_EMAIL = "support@referralsvc.com"
CONTACT_PHONE = "602-796-0177"
CONTACT_ADDRESS = "16031 N 171st Ln, Surprise, AZ 85388, USA"
COPYRIGHT_LINE = "© 2025 Referral Service LLC. All rights reserved."
JURISDICTION = "State of Arizona, USA"
EFFECTIVE_DATE = date.today().isoformat()

APP_NAME = "scholarship_api"
APP_BASE_URL = "https://scholarship-api-jamarrlmayes.replit.app"

def get_base_html(title: str, content: str, canonical_path: str) -> str:
    """Generate base HTML template with SEO, JSON-LD, and footer"""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | {BRAND_NAME} – {APP_NAME}</title>
    <meta name="description" content="{title} for {BRAND_NAME}, the AI-powered scholarship discovery platform by {COMPANY_LEGAL_NAME}.">
    <link rel="canonical" href="{APP_BASE_URL}{canonical_path}">
    <meta property="og:title" content="{title} | {BRAND_NAME}">
    <meta property="og:description" content="{title} for {BRAND_NAME}, the AI-powered scholarship discovery platform.">
    <meta property="og:url" content="{APP_BASE_URL}{canonical_path}">
    <meta property="og:type" content="website">
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f8f9fa;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }}
        a {{ color: #0066cc; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        a:focus {{ outline: 2px solid #0066cc; outline-offset: 2px; }}
        .skip-link {{
            position: absolute;
            top: -40px;
            left: 0;
            background: #0066cc;
            color: white;
            padding: 8px 16px;
            z-index: 100;
        }}
        .skip-link:focus {{ top: 0; }}
        header {{
            background: linear-gradient(135deg, #1a365d 0%, #2c5282 100%);
            color: white;
            padding: 2rem 1rem;
            text-align: center;
        }}
        header h1 {{ font-size: 1.75rem; margin-bottom: 0.5rem; }}
        header p {{ opacity: 0.9; font-size: 0.95rem; }}
        nav {{
            background: #2c5282;
            padding: 0.75rem 1rem;
        }}
        nav ul {{
            list-style: none;
            display: flex;
            justify-content: center;
            gap: 1.5rem;
            flex-wrap: wrap;
        }}
        nav a {{ color: white; font-size: 0.9rem; }}
        nav a:hover {{ opacity: 0.8; }}
        main {{
            flex: 1;
            max-width: 800px;
            margin: 2rem auto;
            padding: 2rem;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        main h2 {{ color: #1a365d; margin: 1.5rem 0 0.75rem; font-size: 1.25rem; }}
        main h2:first-child {{ margin-top: 0; }}
        main p, main ul {{ margin-bottom: 1rem; }}
        main ul {{ padding-left: 1.5rem; }}
        main li {{ margin-bottom: 0.5rem; }}
        .effective-date {{
            background: #e2e8f0;
            padding: 0.75rem 1rem;
            border-radius: 4px;
            margin-bottom: 1.5rem;
            font-size: 0.9rem;
        }}
        footer {{
            background: #1a365d;
            color: white;
            padding: 2rem 1rem;
            margin-top: auto;
        }}
        .footer-content {{
            max-width: 800px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
        }}
        .footer-section h3 {{
            font-size: 0.9rem;
            margin-bottom: 0.75rem;
            opacity: 0.9;
        }}
        .footer-section p, .footer-section a {{
            font-size: 0.85rem;
            color: rgba(255,255,255,0.8);
            display: block;
            margin-bottom: 0.35rem;
        }}
        .footer-section a:hover {{ color: white; }}
        .footer-bottom {{
            max-width: 800px;
            margin: 1.5rem auto 0;
            padding-top: 1rem;
            border-top: 1px solid rgba(255,255,255,0.2);
            text-align: center;
            font-size: 0.8rem;
            opacity: 0.7;
        }}
        @media (max-width: 600px) {{
            main {{ margin: 1rem; padding: 1.25rem; }}
            header h1 {{ font-size: 1.5rem; }}
        }}
    </style>
    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "Organization",
        "@id": "{APP_BASE_URL}/#organization",
        "name": "{COMPANY_LEGAL_NAME}",
        "alternateName": "{BRAND_NAME}",
        "url": "{APP_BASE_URL}",
        "logo": "{MAIN_SITE_URL}/logo.png",
        "sameAs": [
            "{MAIN_SITE_URL}",
            "{APP_BASE_URL}"
        ],
        "contactPoint": {{
            "@type": "ContactPoint",
            "telephone": "{CONTACT_PHONE}",
            "email": "{CONTACT_EMAIL}",
            "contactType": "customer service",
            "availableLanguage": ["English"]
        }},
        "address": {{
            "@type": "PostalAddress",
            "streetAddress": "16031 N 171st Ln",
            "addressLocality": "Surprise",
            "addressRegion": "AZ",
            "postalCode": "85388",
            "addressCountry": "US"
        }},
        "parentOrganization": {{
            "@type": "Organization",
            "name": "{COMPANY_LEGAL_NAME}",
            "url": "{MAIN_SITE_URL}"
        }}
    }}
    </script>
    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "WebPage",
        "@id": "{APP_BASE_URL}{canonical_path}#webpage",
        "url": "{APP_BASE_URL}{canonical_path}",
        "name": "{title} | {BRAND_NAME}",
        "isPartOf": {{
            "@id": "{APP_BASE_URL}/#website"
        }},
        "about": {{
            "@id": "{APP_BASE_URL}/#organization"
        }},
        "inLanguage": "en-US"
    }}
    </script>
</head>
<body>
    <a href="#main-content" class="skip-link">Skip to main content</a>
    <header role="banner">
        <h1>{BRAND_NAME}</h1>
        <p>Central Aggregator API - {APP_NAME}</p>
    </header>
    <nav role="navigation" aria-label="Legal pages navigation">
        <ul>
            <li><a href="/privacy">Privacy Policy</a></li>
            <li><a href="/terms">Terms of Service</a></li>
            <li><a href="/accessibility">Accessibility</a></li>
            <li><a href="/docs">API Documentation</a></li>
        </ul>
    </nav>
    <main id="main-content" role="main">
        {content}
    </main>
    <footer role="contentinfo">
        <div class="footer-content">
            <div class="footer-section">
                <h3>Company</h3>
                <a href="{MAIN_SITE_URL}">{BRAND_NAME}</a>
                <p>{COMPANY_LEGAL_NAME}</p>
                <p>{CONTACT_ADDRESS}</p>
            </div>
            <div class="footer-section">
                <h3>Contact</h3>
                <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a>
                <a href="tel:{CONTACT_PHONE}">{CONTACT_PHONE}</a>
            </div>
            <div class="footer-section">
                <h3>Legal</h3>
                <a href="/privacy">Privacy Policy</a>
                <a href="/terms">Terms of Service</a>
                <a href="/accessibility">Accessibility Statement</a>
            </div>
        </div>
        <div class="footer-bottom">
            <p>{COPYRIGHT_LINE}</p>
        </div>
    </footer>
</body>
</html>"""


@router.get("/privacy", response_class=HTMLResponse, include_in_schema=True)
async def privacy_policy():
    """Privacy Policy page"""
    content = f"""
        <div class="effective-date">
            <strong>Effective Date:</strong> {EFFECTIVE_DATE}
        </div>
        
        <h2>Who We Are</h2>
        <p><strong>{BRAND_NAME}</strong> is provided by <strong>{COMPANY_LEGAL_NAME}</strong> ("we," "us," "our") operating at <a href="{MAIN_SITE_URL}">{MAIN_SITE_URL}</a> and this app at <a href="{APP_BASE_URL}">{APP_BASE_URL}</a>.</p>
        
        <h2>What We Do</h2>
        <p>We help students and providers discover, manage, and apply for scholarships using AI-enabled tools.</p>
        
        <h2>Information We Collect</h2>
        <ul>
            <li><strong>Account and profile data</strong> that users provide (name, email, school/academic info needed for scholarship matching).</li>
            <li><strong>Usage and device data</strong> (log files, cookies, analytics).</li>
            <li><strong>Payment and transaction data</strong> when credits or services are purchased; payments are processed by third-party processors.</li>
            <li><strong>Provider data</strong> submitted to list or manage scholarships.</li>
        </ul>
        
        <h2>How We Use Data</h2>
        <p>To deliver and improve services, personalize recommendations, provide customer support, process transactions, detect/prevent fraud/abuse, maintain security, and comply with law.</p>
        
        <h2>Legal Bases/Consent</h2>
        <p>We rely on user consent and legitimate interests; users may withdraw consent where applicable.</p>
        
        <h2>Cookies/Tracking</h2>
        <p>We use essential cookies and analytics. Users can control cookies via browser settings.</p>
        
        <h2>Data Sharing</h2>
        <p>Service providers (hosting, analytics, payments, email/SMS), compliance with legal requests, mergers/acquisitions. <strong>We do not sell personal information.</strong></p>
        
        <h2>FERPA/COPPA and Student Privacy</h2>
        <p>We design for student privacy. We do not knowingly collect personal information from children under 13. Education records are handled in accordance with applicable law and only with appropriate authorization.</p>
        
        <h2>Data Retention</h2>
        <p>Kept only as long as necessary for the purposes above and to meet legal obligations.</p>
        
        <h2>Security</h2>
        <p>Administrative, technical, and physical safeguards; no system is 100% secure.</p>
        
        <h2>International Transfers</h2>
        <p>Where data crosses borders, we use appropriate safeguards as required by law.</p>
        
        <h2>Your Rights</h2>
        <p>Access, correction, deletion, portability, restriction/objection (as applicable). Contact us at <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a>.</p>
        
        <h2>Communications</h2>
        <p>Users can opt out of non-essential emails/SMS; transactional messages may still occur.</p>
        
        <h2>Third-Party Links</h2>
        <p>We are not responsible for third-party sites' privacy practices.</p>
        
        <h2>Changes</h2>
        <p>We will update this policy as needed and post the new Effective Date.</p>
        
        <h2>Contact</h2>
        <p>{COMPANY_LEGAL_NAME}<br>
        {CONTACT_ADDRESS}<br>
        Email: <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a><br>
        Phone: <a href="tel:{CONTACT_PHONE}">{CONTACT_PHONE}</a></p>
        
        <h2>API-Specific Privacy Note</h2>
        <p>As this is the Central Aggregator API ({APP_NAME}), credentials and authentication tokens are used exclusively for API access, telemetry aggregation, and ecosystem security. We do not store plaintext passwords or share authentication credentials with third parties.</p>
    """
    return HTMLResponse(content=get_base_html("Privacy Policy", content, "/privacy"))


@router.get("/terms", response_class=HTMLResponse, include_in_schema=True)
async def terms_of_service():
    """Terms of Service page"""
    content = f"""
        <div class="effective-date">
            <strong>Effective Date:</strong> {EFFECTIVE_DATE}
        </div>
        
        <h2>Agreement</h2>
        <p>These Terms govern your use of <strong>{BRAND_NAME}</strong> at <a href="{MAIN_SITE_URL}">{MAIN_SITE_URL}</a> and this app at <a href="{APP_BASE_URL}">{APP_BASE_URL}</a>. By using the services, you agree to these Terms.</p>
        
        <h2>Eligibility and Accounts</h2>
        <p>You are responsible for your credentials and keeping your account secure. You must be of legal age to form a binding contract or have appropriate consent.</p>
        
        <h2>Services and AI Assistance</h2>
        <p>Our tools provide scholarship discovery, matching, content drafting, and workflow support. AI outputs may contain errors; review and verify before submitting applications. Do not use the services to cheat or commit academic misconduct.</p>
        
        <h2>User Content and Licenses</h2>
        <p>You retain your content. You grant us a limited license to host/process your content solely to provide the services.</p>
        
        <h2>Providers</h2>
        <p>Providers submitting scholarships represent they have rights to publish the content and consent to display it. Platform fees may apply.</p>
        
        <h2>Payments and Refunds</h2>
        <p>Prices, credits, and fees are shown at purchase. Taxes may apply. All sales are subject to our refund policy: refund requests must be submitted within 30 days of purchase via email to <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a>. Refunds are processed within 5-10 business days.</p>
        
        <h2>Prohibited Uses</h2>
        <p>Abuse, reverse engineering, unauthorized scraping, security testing without permission, violating law, infringing IP, or harassing others.</p>
        
        <h2>Intellectual Property</h2>
        <p><strong>{BRAND_NAME}</strong> and its software, trademarks, and content are owned by <strong>{COMPANY_LEGAL_NAME}</strong> or licensors.</p>
        
        <h2>Disclaimers</h2>
        <p>Services are provided "as is" and "as available." We disclaim warranties to the fullest extent permitted by law, including implied warranties of merchantability, fitness for a particular purpose, and non-infringement.</p>
        
        <h2>Limitation of Liability</h2>
        <p>To the maximum extent permitted by applicable law, {COMPANY_LEGAL_NAME} and its officers, directors, employees, and agents shall not be liable for any indirect, incidental, special, consequential, or punitive damages, including loss of profits, data, or goodwill, arising out of or related to your use of or inability to use the services. Our aggregate liability for all claims arising out of or relating to these Terms or the services shall not exceed the amounts you paid to us in the twelve (12) months prior to the claim.</p>
        
        <h2>Indemnification</h2>
        <p>You agree to defend, indemnify, and hold harmless {COMPANY_LEGAL_NAME} and its officers, directors, employees, and agents from and against any claims, liabilities, damages, losses, and expenses, including reasonable attorneys' fees, arising out of or in any way connected with your access to or use of the services, your violation of these Terms, or your violation of any rights of another.</p>
        
        <h2>Termination</h2>
        <p>We may suspend or terminate your access to the services at any time, with or without cause, and with or without notice. Upon termination, your right to use the services will immediately cease. You may stop using the services at any time.</p>
        
        <h2>Dispute Resolution</h2>
        <p><strong>Informal Resolution:</strong> Before filing any claim, you agree to try to resolve the dispute informally by contacting us at <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a>. We will try to resolve the dispute informally within 60 days.</p>
        <p><strong>Binding Arbitration:</strong> If we cannot resolve the dispute informally, any dispute arising out of or relating to these Terms or the services shall be resolved by binding arbitration administered by JAMS in accordance with its Streamlined Arbitration Rules. The arbitration shall be conducted in Maricopa County, Arizona, unless the parties agree otherwise. The arbitrator's decision shall be final and binding. Judgment on the award may be entered in any court of competent jurisdiction.</p>
        <p><strong>Class Action Waiver:</strong> You agree that any dispute resolution proceedings will be conducted only on an individual basis and not in a class, consolidated, or representative action.</p>
        <p><strong>Small Claims Exception:</strong> Notwithstanding the foregoing, either party may bring an individual action in small claims court.</p>
        
        <h2>Governing Law and Venue</h2>
        <p>These Terms shall be governed by and construed in accordance with the laws of the {JURISDICTION}, without regard to its conflict of law provisions. For any matters not subject to arbitration, you consent to the exclusive jurisdiction and venue of the state and federal courts located in Maricopa County, Arizona.</p>
        
        <h2>Severability</h2>
        <p>If any provision of these Terms is held to be invalid or unenforceable, such provision shall be struck and the remaining provisions shall be enforced to the fullest extent under law.</p>
        
        <h2>Entire Agreement</h2>
        <p>These Terms constitute the entire agreement between you and {COMPANY_LEGAL_NAME} regarding the services and supersede all prior agreements and understandings.</p>
        
        <h2>Changes</h2>
        <p>We may update these Terms at any time by posting the revised Terms on this page. Your continued use of the services after such changes constitutes your acceptance of the new Terms.</p>
        
        <h2>Contact</h2>
        <p>{COMPANY_LEGAL_NAME}<br>
        {CONTACT_ADDRESS}<br>
        Email: <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a><br>
        Phone: <a href="tel:{CONTACT_PHONE}">{CONTACT_PHONE}</a></p>
    """
    return HTMLResponse(content=get_base_html("Terms of Service", content, "/terms"))


@router.get("/accessibility", response_class=HTMLResponse, include_in_schema=True)
async def accessibility_statement():
    """Accessibility Statement page"""
    content = f"""
        <div class="effective-date">
            <strong>Effective Date:</strong> {EFFECTIVE_DATE}
        </div>
        
        <h2>Our Commitment</h2>
        <p><strong>{COMPANY_LEGAL_NAME}</strong> is committed to digital accessibility for all users. Our goal is WCAG 2.1 AA conformance across <a href="{MAIN_SITE_URL}">{MAIN_SITE_URL}</a> and this app at <a href="{APP_BASE_URL}">{APP_BASE_URL}</a>.</p>
        
        <h2>Measures We Take</h2>
        <ul>
            <li>Semantic HTML for proper document structure</li>
            <li>Keyboard navigation support throughout the interface</li>
            <li>Sufficient color contrast (minimum 4.5:1 ratio)</li>
            <li>Descriptive links and alternative text for images</li>
            <li>Focus management and visible focus indicators</li>
            <li>Captions and transcripts where applicable</li>
            <li>Regular accessibility audits and testing</li>
            <li>Screen reader compatibility testing</li>
            <li>Responsive design for mobile accessibility</li>
        </ul>
        
        <h2>Known Limitations</h2>
        <p>If any part of the service is not fully accessible, we will work to remediate promptly. We are continuously working to improve the accessibility of our services.</p>
        
        <h2>Feedback and Accommodation Requests</h2>
        <p>If you encounter accessibility barriers or need an accommodation, please contact us:</p>
        <ul>
            <li>Email: <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a></li>
            <li>Phone: <a href="tel:{CONTACT_PHONE}">{CONTACT_PHONE}</a></li>
        </ul>
        <p>Please include the page URL and a description of the issue.</p>
        
        <h2>Response Time Commitment</h2>
        <p>We are committed to responding to accessibility feedback within <strong>2 business days</strong>. For urgent accessibility issues that prevent access to critical features, we will prioritize a response within <strong>24 hours</strong>.</p>
        
        <h2>Alternative Formats</h2>
        <p>We can provide information in alternative formats upon request, including:</p>
        <ul>
            <li>Large print documents</li>
            <li>Plain text versions of content</li>
            <li>Audio descriptions (where feasible)</li>
            <li>Screen reader-optimized formats</li>
        </ul>
        <p>To request an alternative format, please contact us at <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a> with details of your needs.</p>
        
        <h2>Assessment and Testing</h2>
        <p>We use both automated and manual testing methods to assess accessibility, including:</p>
        <ul>
            <li>Automated accessibility scanning tools</li>
            <li>Manual keyboard navigation testing</li>
            <li>Screen reader testing (NVDA, VoiceOver)</li>
            <li>Color contrast analysis</li>
            <li>User feedback and testing sessions</li>
        </ul>
        <p>Our team receives ongoing training on accessibility best practices and WCAG guidelines.</p>
        
        <h2>Third-Party Content</h2>
        <p>While we strive to ensure accessibility of all content, some third-party content or embedded features may not be fully accessible. We work with third-party providers to improve accessibility where possible.</p>
        
        <h2>Continuous Improvement</h2>
        <p>We review this statement and our accessibility practices regularly. We update the Effective Date when changes occur and publish updates about our accessibility initiatives.</p>
        
        <h2>Formal Complaints</h2>
        <p>If you are not satisfied with our response to an accessibility concern, you may file a formal complaint by emailing <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a> with "Accessibility Complaint" in the subject line. We will respond to formal complaints within 5 business days.</p>
        
        <h2>Contact</h2>
        <p>{COMPANY_LEGAL_NAME}<br>
        {CONTACT_ADDRESS}<br>
        Email: <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a><br>
        Phone: <a href="tel:{CONTACT_PHONE}">{CONTACT_PHONE}</a></p>
    """
    return HTMLResponse(content=get_base_html("Accessibility Statement", content, "/accessibility"))


def get_report_footer() -> str:
    """
    Returns the standard report footer for all generated reports.
    Use this in PDFs, HTML reports, emails, and any user-facing documents.
    """
    return f"This report was generated by {APP_NAME} — {APP_BASE_URL} | {BRAND_NAME} by {COMPANY_LEGAL_NAME} | {CONTACT_EMAIL} | {CONTACT_PHONE}"


def get_report_footer_html() -> str:
    """Returns HTML-formatted report footer for web reports"""
    return f"""
    <div style="margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #e2e8f0; font-size: 10px; color: #64748b; text-align: center;">
        This report was generated by <strong>{APP_NAME}</strong> — <a href="{APP_BASE_URL}">{APP_BASE_URL}</a> | 
        {BRAND_NAME} by {COMPANY_LEGAL_NAME} | 
        <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a> | 
        <a href="tel:{CONTACT_PHONE}">{CONTACT_PHONE}</a>
    </div>
    """


LEGAL_INFO = {
    "brand_name": BRAND_NAME,
    "company_legal_name": COMPANY_LEGAL_NAME,
    "main_site_url": MAIN_SITE_URL,
    "contact_email": CONTACT_EMAIL,
    "contact_phone": CONTACT_PHONE,
    "contact_address": CONTACT_ADDRESS,
    "copyright_line": COPYRIGHT_LINE,
    "jurisdiction": JURISDICTION,
    "effective_date": EFFECTIVE_DATE,
    "app_name": APP_NAME,
    "app_base_url": APP_BASE_URL,
}
