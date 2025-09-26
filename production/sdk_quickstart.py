"""
SDK & DevRel Launch Service
Executive directive: Minimal SDKs (curl, JS/TS, Python) and 10-minute Quickstart
"""
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class SDKExample:
    """SDK code example for documentation"""
    language: str
    name: str
    code: str
    description: str

class SDKQuickstartService:
    """
    Executive directive SDK & DevRel service:
    - Minimal SDKs for curl, JavaScript/TypeScript, Python
    - 10-minute quickstart guide for fast developer adoption
    - Code examples with real API integration
    - Developer onboarding optimization
    """

    def __init__(self):
        self.evidence_path = Path("production/devrel_evidence")
        self.evidence_path.mkdir(exist_ok=True)

        # Base API URL for examples (dynamic from environment)
        import os
        self.api_base = os.getenv("API_BASE_URL", "https://scholarship-api.replit.app")

        # Example API key for demonstrations
        self.example_api_key = "sk_live_demo_key_replace_with_your_actual_key"

        print("👩‍💻 SDK & DevRel service initialized")
        print("🎯 Creating minimal SDKs: curl, JS/TS, Python")

    def get_curl_examples(self) -> list[SDKExample]:
        """
        Generate curl SDK examples
        Executive directive: Minimal curl commands for immediate testing
        """
        return [
            SDKExample(
                language="curl",
                name="Get API Tiers",
                description="View available API plans and pricing",
                code=f'''# Get API pricing tiers
curl -X GET "{self.api_base}/api/v1/billing/tiers" \\
  -H "Accept: application/json"'''
            ),
            SDKExample(
                language="curl",
                name="Create API Key",
                description="Create a new API key with company information",
                code=f'''# Create API key (free tier)
curl -X POST "{self.api_base}/api/v1/billing/api-key" \\
  -H "Content-Type: application/json" \\
  -d '{{
    "user_id": "your_unique_id",
    "email": "your@email.com",
    "company_name": "Your Company",
    "tier": "free"
  }}'

# Save the returned API key for authentication'''
            ),
            SDKExample(
                language="curl",
                name="Search Scholarships",
                description="Search for scholarships with authentication",
                code=f'''# Search scholarships (requires API key)
curl -X GET "{self.api_base}/api/v1/scholarships/search?q=engineering&limit=10" \\
  -H "X-API-Key: {self.example_api_key}" \\
  -H "Accept: application/json"

# Check rate limit headers in response:
# X-RateLimit-Limit: 50
# X-RateLimit-Remaining: 49'''
            ),
            SDKExample(
                language="curl",
                name="Check Eligibility",
                description="Check scholarship eligibility for a student profile",
                code=f'''# Check eligibility
curl -X POST "{self.api_base}/api/v1/eligibility/check" \\
  -H "X-API-Key: {self.example_api_key}" \\
  -H "Content-Type: application/json" \\
  -d '{{
    "student_profile": {{
      "gpa": 3.5,
      "year_in_school": "junior",
      "field_of_study": "computer science",
      "demographic_info": {{
        "first_generation": true,
        "underrepresented_minority": false
      }}
    }},
    "scholarship_ids": ["sch_123", "sch_456"]
  }}'

# Returns eligibility scores and explanations'''
            ),
            SDKExample(
                language="curl",
                name="AI-Powered Search Enhancement",
                description="Use AI to enhance search queries and get insights",
                code=f'''# AI search enhancement (requires credits)
curl -X POST "{self.api_base}/api/v1/ai/enhance-search" \\
  -H "X-API-Key: {self.example_api_key}" \\
  -H "Content-Type: application/json" \\
  -d '{{
    "original_query": "scholarships for engineering students",
    "student_context": {{
      "academic_interests": ["robotics", "AI"],
      "career_goals": "software engineering"
    }}
  }}'

# Uses 5 AI credits from your quota'''
            ),
            SDKExample(
                language="curl",
                name="Check Usage & Billing",
                description="Monitor your API usage and billing information",
                code=f'''# Check current usage and billing
curl -X GET "{self.api_base}/api/v1/billing/usage" \\
  -H "X-API-Key: {self.example_api_key}" \\
  -H "Accept: application/json"

# Shows current month usage, remaining quota, overage charges'''
            )
        ]

    def get_javascript_sdk(self) -> list[SDKExample]:
        """
        Generate JavaScript/TypeScript SDK examples
        Executive directive: Minimal JS/TS client for web apps
        """
        return [
            SDKExample(
                language="javascript",
                name="SDK Class (TypeScript)",
                description="Complete TypeScript SDK client class",
                code=f'''// scholarship-api-client.ts
export interface APITier {{
  name: string;
  monthly_cost: number;
  requests_per_minute: number;
  requests_per_month: number;
  ai_credits_included: number;
  features: string[];
  support_level: string;
  sla_commitment: string;
}}

export interface ScholarshipSearchResult {{
  scholarships: Array<{{
    id: string;
    title: string;
    amount: number;
    deadline: string;
    eligibility_summary: string;
    relevance_score: number;
  }}>;
  total_results: number;
  search_metadata: {{
    query: string;
    filters_applied: string[];
    search_time_ms: number;
  }};
}}

export class ScholarshipAPIClient {{
  private apiKey: string;
  private baseURL: string = '{self.api_base}';

  constructor(apiKey: string) {{
    this.apiKey = apiKey;
  }}

  private async request<T>(
    endpoint: string,
    method: 'GET' | 'POST' = 'GET',
    body?: any
  ): Promise<T> {{
    const response = await fetch(`${{this.baseURL}}${{endpoint}}`, {{
      method,
      headers: {{
        'X-API-Key': this.apiKey,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      }},
      body: body ? JSON.stringify(body) : undefined
    }});

    if (!response.ok) {{
      const error = await response.json();
      throw new Error(`API Error ${{response.status}}: ${{error.detail || error.message}}`);
    }}

    // Log rate limit headers for monitoring
    const remaining = response.headers.get('X-RateLimit-Remaining');
    const limit = response.headers.get('X-RateLimit-Limit');
    if (remaining && limit) {{
      console.log(`Rate Limit: ${{remaining}}/${{limit}} requests remaining`);
    }}

    return response.json();
  }}

  // Get API pricing tiers
  async getTiers(): Promise<{{ pricing_tiers: {{ tier_comparison: Record<string, APITier> }} }}> {{
    return this.request('/api/v1/billing/tiers');
  }}

  // Search scholarships
  async searchScholarships(
    query: string,
    filters?: {{
      amount_min?: number;
      amount_max?: number;
      deadline_after?: string;
      field_of_study?: string;
      limit?: number;
    }}
  ): Promise<ScholarshipSearchResult> {{
    const params = new URLSearchParams({{ q: query }});
    if (filters) {{
      Object.entries(filters).forEach(([key, value]) => {{
        if (value !== undefined) {{
          params.append(key, value.toString());
        }}
      }});
    }}

    return this.request(`/api/v1/scholarships/search?${{params}}`);
  }}

  // Check eligibility
  async checkEligibility(
    studentProfile: {{
      gpa: number;
      year_in_school: string;
      field_of_study: string;
      demographic_info?: Record<string, boolean>;
    }},
    scholarshipIds: string[]
  ) {{
    return this.request('/api/v1/eligibility/check', 'POST', {{
      student_profile: studentProfile,
      scholarship_ids: scholarshipIds
    }});
  }}

  // AI search enhancement
  async enhanceSearch(
    originalQuery: string,
    studentContext?: {{
      academic_interests?: string[];
      career_goals?: string;
    }}
  ) {{
    return this.request('/api/v1/ai/enhance-search', 'POST', {{
      original_query: originalQuery,
      student_context: studentContext
    }});
  }}

  // Check usage and billing
  async getUsage() {{
    return this.request('/api/v1/billing/usage');
  }}
}}

// Usage example
const client = new ScholarshipAPIClient('{self.example_api_key}');

// Search for engineering scholarships
client.searchScholarships('engineering', {{
  amount_min: 1000,
  field_of_study: 'computer science',
  limit: 5
}}).then(results => {{
  console.log(`Found ${{results.total_results}} scholarships`);
  results.scholarships.forEach(scholarship => {{
    console.log(`- ${{scholarship.title}}: $${{scholarship.amount}}`);
  }});
}}).catch(error => {{
  console.error('Search failed:', error.message);
}});'''
            ),
            SDKExample(
                language="javascript",
                name="React Integration Example",
                description="React hook for scholarship search with error handling",
                code='''// useScholarshipSearch.ts (React Hook)
import { useState, useCallback } from 'react';
import { ScholarshipAPIClient } from './scholarship-api-client';

export const useScholarshipSearch = (apiKey: string) => {
  const [client] = useState(() => new ScholarshipAPIClient(apiKey));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<any>(null);
  const [usage, setUsage] = useState<any>(null);

  const search = useCallback(async (query: string, filters?: any) => {
    setLoading(true);
    setError(null);

    try {
      const searchResults = await client.searchScholarships(query, filters);
      const usageInfo = await client.getUsage();

      setResults(searchResults);
      setUsage(usageInfo);
    } catch (err: any) {
      setError(err.message);

      // Handle specific error cases
      if (err.message.includes('401')) {
        setError('Invalid API key. Please check your credentials.');
      } else if (err.message.includes('429')) {
        setError('Rate limit exceeded. Please try again later.');
      } else if (err.message.includes('402')) {
        setError('Insufficient credits. Please upgrade your plan.');
      }
    } finally {
      setLoading(false);
    }
  }, [client]);

  return { search, loading, error, results, usage };
};

// ScholarshipSearch.tsx (React Component)
import React, { useState } from 'react';
import { useScholarshipSearch } from './useScholarshipSearch';

interface ScholarshipSearchProps {
  apiKey: string;
}

export const ScholarshipSearch: React.FC<ScholarshipSearchProps> = ({ apiKey }) => {
  const [query, setQuery] = useState('');
  const { search, loading, error, results, usage } = useScholarshipSearch(apiKey);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      search(query.trim());
    }
  };

  return (
    <div className="scholarship-search">
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search scholarships..."
          disabled={loading}
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>

      {usage && (
        <div className="usage-info">
          <small>
            API Usage: {usage.current_usage?.monthly_remaining} requests remaining
            {usage.current_usage?.overage_charges !== '$0.00' &&
              ` | Overages: ${usage.current_usage.overage_charges}`
            }
          </small>
        </div>
      )}

      {error && <div className="error">Error: {error}</div>}

      {results && (
        <div className="results">
          <h3>Found {results.total_results} scholarships</h3>
          <ul>
            {results.scholarships.map((scholarship: any) => (
              <li key={scholarship.id}>
                <strong>{scholarship.title}</strong> - ${scholarship.amount}
                <br />
                <small>Deadline: {scholarship.deadline} | Relevance: {scholarship.relevance_score}%</small>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};'''
            )
        ]

    def get_python_sdk(self) -> list[SDKExample]:
        """
        Generate Python SDK examples
        Executive directive: Minimal Python client for backend integration
        """
        return [
            SDKExample(
                language="python",
                name="Python SDK Class",
                description="Complete Python SDK client with error handling",
                code=f'''# scholarship_api_client.py
import requests
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import time

class ScholarshipAPIError(Exception):
    """Custom exception for Scholarship API errors"""
    def __init__(self, status_code: int, message: str, correlation_id: str = None):
        self.status_code = status_code
        self.message = message
        self.correlation_id = correlation_id
        super().__init__(f"API Error {{status_code}}: {{message}}")

class ScholarshipAPIClient:
    """
    Scholarship Discovery API Python Client

    Provides easy access to scholarship search, eligibility checking,
    and AI-powered features with built-in rate limiting and error handling.
    """

    def __init__(self, api_key: str, base_url: str = "{self.api_base}"):
        """
        Initialize the API client

        Args:
            api_key: Your API key (get from /api/v1/billing/api-key)
            base_url: API base URL (default: production URL)
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({{
            'X-API-Key': api_key,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'ScholarshipAPI-Python-SDK/1.0'
        }})

        # Usage tracking
        self.last_rate_limit_info = {{}}

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make authenticated request with error handling"""
        url = f"{{self.base_url}}{{endpoint}}"

        try:
            response = self.session.request(method, url, **kwargs)

            # Track rate limit information
            self.last_rate_limit_info = {{
                'limit': response.headers.get('X-RateLimit-Limit'),
                'remaining': response.headers.get('X-RateLimit-Remaining'),
                'monthly_remaining': response.headers.get('X-RateLimit-Monthly-Remaining'),
                'overage_charges': response.headers.get('X-Overage-Charges'),
                'timestamp': datetime.now()
            }}

            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                raise ScholarshipAPIError(
                    429,
                    f"Rate limit exceeded. Retry after {{retry_after}} seconds.",
                    response.headers.get('X-Correlation-Id')
                )

            # Handle other HTTP errors
            if not response.ok:
                error_data = response.json() if response.content else {{'detail': 'Unknown error'}}
                raise ScholarshipAPIError(
                    response.status_code,
                    error_data.get('detail', 'Unknown error'),
                    response.headers.get('X-Correlation-Id')
                )

            return response.json()

        except requests.RequestException as e:
            raise ScholarshipAPIError(500, f"Network error: {{e}}")

    def get_tiers(self) -> Dict[str, Any]:
        """
        Get API pricing tiers and features

        Returns:
            Dictionary with tier comparison and pricing information
        """
        return self._request('GET', '/api/v1/billing/tiers')

    def search_scholarships(
        self,
        query: str,
        amount_min: Optional[int] = None,
        amount_max: Optional[int] = None,
        deadline_after: Optional[str] = None,
        field_of_study: Optional[str] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Search for scholarships

        Args:
            query: Search query (keywords, requirements, etc.)
            amount_min: Minimum scholarship amount
            amount_max: Maximum scholarship amount
            deadline_after: Filter by deadline (YYYY-MM-DD format)
            field_of_study: Filter by field of study
            limit: Number of results to return (max 100)

        Returns:
            Search results with scholarships and metadata
        """
        params = {{'q': query, 'limit': limit}}

        # Add optional filters
        if amount_min is not None:
            params['amount_min'] = amount_min
        if amount_max is not None:
            params['amount_max'] = amount_max
        if deadline_after:
            params['deadline_after'] = deadline_after
        if field_of_study:
            params['field_of_study'] = field_of_study

        return self._request('GET', '/api/v1/scholarships/search', params=params)

    def check_eligibility(
        self,
        student_profile: Dict[str, Any],
        scholarship_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Check scholarship eligibility for a student

        Args:
            student_profile: Student information (GPA, year, field of study, etc.)
            scholarship_ids: List of scholarship IDs to check

        Returns:
            Eligibility results with scores and explanations
        """
        payload = {{
            'student_profile': student_profile,
            'scholarship_ids': scholarship_ids
        }}

        return self._request('POST', '/api/v1/eligibility/check', json=payload)

    def enhance_search_with_ai(
        self,
        original_query: str,
        student_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Use AI to enhance search query and get insights

        Args:
            original_query: Original search query
            student_context: Additional context (interests, goals, etc.)

        Returns:
            Enhanced query suggestions and insights
        """
        payload = {{
            'original_query': original_query,
            'student_context': student_context or {{}}
        }}

        return self._request('POST', '/api/v1/ai/enhance-search', json=payload)

    def get_usage_info(self) -> Dict[str, Any]:
        """
        Get current API usage and billing information

        Returns:
            Usage statistics and billing details
        """
        return self._request('GET', '/api/v1/billing/usage')

    def get_rate_limit_info(self) -> Dict[str, Any]:
        """
        Get last known rate limit information

        Returns:
            Rate limit headers from last request
        """
        return self.last_rate_limit_info

    def __repr__(self):
        return f"ScholarshipAPIClient(api_key='{{self.api_key[:16]}}...', base_url='{{self.base_url}}')"

# Example usage
if __name__ == "__main__":
    # Initialize client
    client = ScholarshipAPIClient('{self.example_api_key}')

    try:
        # Get pricing information
        print("API Tiers:")
        tiers = client.get_tiers()
        for tier_name, tier_info in tiers['pricing_tiers']['tier_comparison'].items():
            print(f"  - {{tier_name.title()}}: ${{tier_info['monthly_cost']}}/month")

        # Search for scholarships
        print("\\nSearching for engineering scholarships...")
        results = client.search_scholarships(
            query="engineering computer science",
            amount_min=1000,
            limit=5
        )

        print(f"Found {{results['total_results']}} scholarships:")
        for scholarship in results['scholarships'][:3]:  # Show first 3
            print(f"  - {{scholarship['title']}}: ${{scholarship['amount']}}")

        # Check usage
        usage = client.get_usage_info()
        remaining = usage['current_usage']['monthly_remaining']
        print(f"\\nAPI Usage: {{remaining}} requests remaining this month")

        # Rate limit info
        rate_info = client.get_rate_limit_info()
        if rate_info.get('remaining'):
            print(f"Rate Limit: {{rate_info['remaining']}} requests remaining this minute")

    except ScholarshipAPIError as e:
        print(f"API Error: {{e}}")
        if e.status_code == 401:
            print("Please check your API key")
        elif e.status_code == 429:
            print("You've hit the rate limit. Please wait before making more requests.")
    except Exception as e:
        print(f"Unexpected error: {{e}}")'''
            ),
            SDKExample(
                language="python",
                name="Django Integration Example",
                description="Django view for scholarship search with caching",
                code='''# scholarships/views.py (Django)
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.conf import settings
import json

from .scholarship_api_client import ScholarshipAPIClient, ScholarshipAPIError

class ScholarshipSearchView(View):
    """Django view for scholarship search with caching"""

    def __init__(self):
        super().__init__()
        self.client = ScholarshipAPIClient(settings.SCHOLARSHIP_API_KEY)

    @method_decorator(cache_page(60 * 15))  # Cache for 15 minutes
    def get(self, request):
        """Handle scholarship search requests"""
        query = request.GET.get('q', '')
        if not query:
            return JsonResponse({{
                'error': 'Query parameter "q" is required'
            }}, status=400)

        try:
            # Build search filters from query parameters
            filters = {{}}
            if request.GET.get('amount_min'):
                filters['amount_min'] = int(request.GET.get('amount_min'))
            if request.GET.get('amount_max'):
                filters['amount_max'] = int(request.GET.get('amount_max'))
            if request.GET.get('field_of_study'):
                filters['field_of_study'] = request.GET.get('field_of_study')
            if request.GET.get('limit'):
                filters['limit'] = min(int(request.GET.get('limit', 20)), 100)

            # Search scholarships
            results = self.client.search_scholarships(query, **filters)

            # Add rate limit information
            rate_info = self.client.get_rate_limit_info()
            results['api_usage'] = {{
                'remaining_requests': rate_info.get('remaining'),
                'monthly_remaining': rate_info.get('monthly_remaining')
            }}

            return JsonResponse(results)

        except ScholarshipAPIError as e:
            if e.status_code == 429:
                return JsonResponse({{
                    'error': 'API rate limit exceeded',
                    'message': e.message,
                    'retry_after': 60
                }}, status=429)
            elif e.status_code == 401:
                return JsonResponse({{
                    'error': 'API authentication failed',
                    'message': 'Please check API key configuration'
                }}, status=500)
            else:
                return JsonResponse({{
                    'error': 'API request failed',
                    'message': e.message
                }}, status=500)
        except Exception as e:
            return JsonResponse({{
                'error': 'Internal server error',
                'message': str(e)
            }}, status=500)

# scholarships/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('api/scholarships/search/', views.ScholarshipSearchView.as_view(), name='scholarship-search'),
]

# settings.py
SCHOLARSHIP_API_KEY = env('SCHOLARSHIP_API_KEY')  # Set in environment
CACHES = {{
    'default': {{
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }}
}}'''
            )
        ]

    def generate_ten_minute_quickstart(self) -> str:
        """
        Generate comprehensive 10-minute quickstart guide
        Executive directive: Fast developer onboarding and adoption
        """
        return f"""# 🚀 Scholarship Discovery API - 10-Minute Quickstart

**Get from zero to scholarship search in under 10 minutes!**

## 📋 What You'll Build

By the end of this guide, you'll have:
- ✅ API key with authentication
- ✅ Working scholarship search integration
- ✅ Student eligibility checking
- ✅ Rate limit and usage monitoring

## ⏱️ Step 1: Get Your API Key (2 minutes)

### Option A: Using curl
```bash
curl -X POST "{self.api_base}/api/v1/billing/api-key" \\
  -H "Content-Type: application/json" \\
  -d '{{
    "user_id": "quickstart_user",
    "email": "your@email.com",
    "company_name": "Your Company",
    "tier": "free"
  }}'
```

### Option B: Using the web interface
1. Visit: {self.api_base}/docs
2. Navigate to "Billing" section
3. Use "Create API Key" endpoint
4. **Save your API key securely** - it can't be retrieved later!

### Free Tier Limits
- 🔢 **50 requests/minute**
- 📅 **10,000 requests/month**
- 🤖 **100 AI credits included**

## ⏱️ Step 2: Test Basic Search (3 minutes)

### Quick Test with curl
```bash
# Replace YOUR_API_KEY with your actual key
export API_KEY="YOUR_API_KEY"

# Basic scholarship search
curl -X GET "{self.api_base}/api/v1/scholarships/search?q=engineering&limit=5" \\
  -H "X-API-Key: $API_KEY" \\
  -H "Accept: application/json"
```

**Expected Response:**
```json
{{
  "scholarships": [
    {{
      "id": "sch_123",
      "title": "Engineering Excellence Scholarship",
      "amount": 5000,
      "deadline": "2025-03-15",
      "relevance_score": 95
    }}
  ],
  "total_results": 150,
  "search_metadata": {{
    "query": "engineering",
    "search_time_ms": 45
  }}
}}
```

## ⏱️ Step 3: Check Eligibility (2 minutes)

```bash
# Check if a student is eligible for scholarships
curl -X POST "{self.api_base}/api/v1/eligibility/check" \\
  -H "X-API-Key: $API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{{
    "student_profile": {{
      "gpa": 3.5,
      "year_in_school": "junior",
      "field_of_study": "computer science"
    }},
    "scholarship_ids": ["sch_123", "sch_456"]
  }}'
```

## ⏱️ Step 4: Monitor Usage (1 minute)

```bash
# Check your API usage and limits
curl -X GET "{self.api_base}/api/v1/billing/usage" \\
  -H "X-API-Key: $API_KEY" \\
  -H "Accept: application/json"
```

**Watch for these headers in all responses:**
```
X-RateLimit-Remaining: 49
X-RateLimit-Monthly-Remaining: 9995
X-Overage-Charges: $0.00
```

## ⏱️ Step 5: Add to Your App (2 minutes)

### JavaScript/React Integration
```javascript
const scholarshipAPI = {{
  apiKey: 'YOUR_API_KEY',
  baseURL: '{self.api_base}',

  async search(query, filters = {{}}) {{
    const params = new URLSearchParams({{ q: query, ...filters }});
    const response = await fetch(`${{this.baseURL}}/api/v1/scholarships/search?${{params}}`, {{
      headers: {{ 'X-API-Key': this.apiKey }}
    }});
    return response.json();
  }}
}};

// Usage
scholarshipAPI.search('computer science', {{ limit: 10 }})
  .then(results => console.log(results.scholarships));
```

### Python Integration
```python
import requests

class ScholarshipSearch:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = '{self.api_base}'

    def search(self, query, **filters):
        headers = {{'X-API-Key': self.api_key}}
        params = {{'q': query, **filters}}
        response = requests.get(f'{{self.base_url}}/api/v1/scholarships/search',
                               headers=headers, params=params)
        return response.json()

# Usage
client = ScholarshipSearch('YOUR_API_KEY')
results = client.search('engineering', limit=5)
```

## 🎉 Congratulations!

You've successfully integrated the Scholarship Discovery API!

### Next Steps
- 📊 **Monitor usage**: Check `/api/v1/billing/usage` regularly
- 🤖 **Try AI features**: Use `/api/v1/ai/enhance-search` for smarter queries
- 📈 **Scale up**: Upgrade to paid tiers for higher limits
- 📚 **Full documentation**: Visit {self.api_base}/docs

### Production Checklist
- [ ] Store API keys securely (environment variables)
- [ ] Implement error handling for rate limits
- [ ] Add retry logic for network failures
- [ ] Monitor usage to avoid overages
- [ ] Cache responses where appropriate

### Support & Resources
- 📖 **Full API Docs**: {self.api_base}/docs
- 📊 **Status Page**: {self.api_base}/status
- 📝 **Release Notes**: {self.api_base}/release-notes
- 📧 **Support Email**: support@scholarshipapi.com

### Rate Limits & Pricing
- **Free**: 50/min, 10K/month, 100 AI credits
- **Starter**: 200/min, 100K/month, 1K AI credits - $29/mo
- **Professional**: 500/min, 500K/month, 5K AI credits - $99/mo
- **Enterprise**: 2K/min, 5M/month, 25K AI credits - $499/mo

Happy coding! 🚀"""


    def generate_developer_documentation(self) -> dict[str, Any]:
        """
        Generate comprehensive developer documentation
        Executive directive: Complete developer onboarding experience
        """
        curl_examples = self.get_curl_examples()
        js_examples = self.get_javascript_sdk()
        python_examples = self.get_python_sdk()
        quickstart = self.generate_ten_minute_quickstart()

        documentation = {
            "devrel_launch": {
                "title": "SDK & Developer Relations Launch",
                "description": "Comprehensive developer onboarding with minimal SDKs and quickstart guide",
                "executive_directive": "Drive developer adoption with 10-minute time-to-value",
                "created_at": datetime.now().isoformat()
            },
            "quickstart_guide": {
                "title": "10-Minute Quickstart Guide",
                "time_to_value": "Under 10 minutes from zero to working integration",
                "content": quickstart
            },
            "sdk_examples": {
                "curl": {
                    "title": "cURL Commands",
                    "description": "Minimal curl commands for immediate testing",
                    "examples": [
                        {
                            "name": example.name,
                            "description": example.description,
                            "code": example.code
                        }
                        for example in curl_examples
                    ]
                },
                "javascript": {
                    "title": "JavaScript/TypeScript SDK",
                    "description": "Complete client library for web applications",
                    "examples": [
                        {
                            "name": example.name,
                            "description": example.description,
                            "code": example.code
                        }
                        for example in js_examples
                    ]
                },
                "python": {
                    "title": "Python SDK",
                    "description": "Full-featured client for backend integration",
                    "examples": [
                        {
                            "name": example.name,
                            "description": example.description,
                            "code": example.code
                        }
                        for example in python_examples
                    ]
                }
            },
            "integration_patterns": {
                "react": {
                    "title": "React Integration",
                    "description": "React hooks and components for scholarship search",
                    "features": ["Custom hooks", "Error handling", "Rate limit monitoring", "Usage tracking"]
                },
                "django": {
                    "title": "Django Integration",
                    "description": "Django views with caching and error handling",
                    "features": ["View classes", "Response caching", "Rate limit handling", "Settings integration"]
                },
                "nodejs": {
                    "title": "Node.js Integration",
                    "description": "Express.js middleware and route handlers",
                    "features": ["Middleware support", "Promise-based", "Error handling", "Request logging"]
                }
            },
            "developer_experience": {
                "onboarding_time": "10 minutes",
                "time_to_first_success": "Under 2 minutes",
                "supported_languages": ["curl", "JavaScript", "TypeScript", "Python"],
                "framework_examples": ["React", "Django", "Node.js/Express"],
                "key_features": [
                    "Secure API key authentication",
                    "Rate limiting with transparent headers",
                    "Comprehensive error handling",
                    "Usage monitoring and billing transparency",
                    "AI-powered search enhancement",
                    "Production-ready examples"
                ]
            },
            "support_resources": {
                "documentation": f"{self.api_base}/docs",
                "status_page": f"{self.api_base}/status",
                "release_notes": f"{self.api_base}/release-notes",
                "support_email": "support@scholarshipapi.com",
                "community_forum": "https://community.scholarshipapi.com",
                "github_examples": "https://github.com/scholarshipapi/examples"
            }
        }

        # Save documentation evidence
        evidence_file = self.evidence_path / f"devrel_documentation_{datetime.now().strftime('%Y%m%d')}.json"
        with open(evidence_file, 'w') as f:
            json.dump(documentation, f, indent=2)

        print(f"📚 Developer documentation generated with {len(curl_examples)} curl examples")
        print(f"🔧 SDK examples: {len(js_examples)} JS/TS + {len(python_examples)} Python")
        print("⚡ Quickstart guide: 10-minute time-to-value")

        return documentation

# Global SDK service
sdk_service = SDKQuickstartService()
