#!/usr/bin/env python3
"""
Focused QA Tests based on LSP Diagnostics Analysis
Senior QA Engineer - Detailed Issue Analysis
"""

import json
import requests
import traceback
from datetime import datetime, timedelta
from typing import Optional, List

class FocusedQAAnalysis:
    """Focused QA analysis based on static code analysis"""
    
    def __init__(self):
        self.issues = []
        self.base_url = "http://localhost:5000"
    
    def log_issue(self, issue_id: str, location: str, description: str, 
                  steps_to_reproduce: str, observed_output: str, 
                  expected_output: str, severity: str):
        """Log identified issues"""
        issue = {
            "issue_id": issue_id,
            "location": location,
            "description": description,
            "steps_to_reproduce": steps_to_reproduce,
            "observed_output": observed_output,
            "expected_output": expected_output,
            "severity": severity
        }
        self.issues.append(issue)
        print(f"🐛 ISSUE {issue_id}: {description} [{severity}]")
    
    def test_lsp_diagnostics_issues(self):
        """Test issues identified by LSP diagnostics"""
        print("\n🔍 Analyzing LSP Diagnostic Issues...")
        
        # Import modules to trigger validation
        try:
            from data.scholarships import MOCK_SCHOLARSHIPS
            from models.scholarship import EligibilityCriteria
            
            # Test: Check if EligibilityCriteria missing parameters affect functionality
            incomplete_criteria = EligibilityCriteria()  # Using defaults
            
            # According to LSP, these should have missing parameters
            print(f"✓ EligibilityCriteria created with defaults: {incomplete_criteria}")
            
        except Exception as e:
            self.log_issue(
                "LSP001",
                "data/scholarships.py:18-340",
                "EligibilityCriteria constructor issues prevent scholarship creation",
                "Import MOCK_SCHOLARSHIPS and create EligibilityCriteria",
                f"Exception: {e}",
                "Should create scholarships without issues",
                "High"
            )
    
    def test_api_response_consistency(self):
        """Test API response consistency and data integrity"""
        print("\n🔍 Testing API Response Consistency...")
        
        try:
            # Test 1: Search endpoint consistency
            response1 = requests.get(f"{self.base_url}/api/v1/scholarships?limit=5")
            response2 = requests.get(f"{self.base_url}/api/v1/scholarships?limit=5&offset=0")
            
            if response1.status_code == 200 and response2.status_code == 200:
                data1 = response1.json()
                data2 = response2.json()
                
                if data1["scholarships"] != data2["scholarships"]:
                    self.log_issue(
                        "API006",
                        "routers/scholarships.py:21-77",
                        "Search results inconsistent between equivalent requests",
                        "Compare GET /scholarships?limit=5 vs GET /scholarships?limit=5&offset=0",
                        f"Different results returned",
                        "Same results should be returned",
                        "Medium"
                    )
            
            # Test 2: Scholarship detail consistency
            scholarship_list = requests.get(f"{self.base_url}/api/v1/scholarships?limit=1")
            if scholarship_list.status_code == 200:
                first_scholarship = scholarship_list.json()["scholarships"][0]
                scholarship_id = first_scholarship["id"]
                
                scholarship_detail = requests.get(f"{self.base_url}/api/v1/scholarships/{scholarship_id}")
                if scholarship_detail.status_code == 200:
                    detail_data = scholarship_detail.json()
                    
                    # Check if basic fields match
                    if (first_scholarship["name"] != detail_data["name"] or
                        first_scholarship["amount"] != detail_data["amount"]):
                        self.log_issue(
                            "API007",
                            "routers/scholarships.py:137-166",
                            "Scholarship list and detail views return inconsistent data",
                            f"Compare list view vs detail view for scholarship {scholarship_id}",
                            "Name or amount fields don't match",
                            "All common fields should match between views",
                            "High"
                        )
            
        except Exception as e:
            self.log_issue(
                "API008",
                "routers/scholarships.py",
                "API consistency testing failed due to connection issues",
                "Test API response consistency",
                f"Exception: {e}",
                "API should be accessible for testing",
                "Critical"
            )
    
    def test_eligibility_logic_edge_cases(self):
        """Test eligibility logic for edge cases and potential bugs"""
        print("\n🔍 Testing Eligibility Logic Edge Cases...")
        
        try:
            from services.eligibility_service import eligibility_service
            from models.user import UserProfile
            
            # Test 1: User with all None values
            empty_user = UserProfile(id="empty_user")
            result = eligibility_service.check_eligibility(empty_user, "sch_001")
            
            if result.match_score == 1.0:
                self.log_issue(
                    "ELG004",
                    "services/eligibility_service.py:55-157",
                    "Empty user profile gets perfect match score",
                    "Check eligibility with UserProfile having all None values",
                    f"Match score: {result.match_score}",
                    "Should have reduced match score due to missing information",
                    "Medium"
                )
            
            # Test 2: User with extreme values
            extreme_user = UserProfile(
                id="extreme",
                gpa=4.0,
                age=0,  # Invalid age
                grade_level="kindergarten"  # Invalid grade level
            )
            result = eligibility_service.check_eligibility(extreme_user, "sch_001")
            
            if result.eligible:
                self.log_issue(
                    "ELG005",
                    "services/eligibility_service.py:120-133",
                    "Eligibility check accepts invalid age values",
                    "Check eligibility with age=0",
                    f"Eligible: {result.eligible}",
                    "Should reject users with invalid age",
                    "Medium"
                )
            
            # Test 3: Multiple eligibility checks with same user
            user = UserProfile(id="test_user", gpa=3.5)
            results = []
            for _ in range(5):
                result = eligibility_service.check_eligibility(user, "sch_001")
                results.append(result.match_score)
            
            if len(set(results)) > 1:
                self.log_issue(
                    "ELG006",
                    "services/eligibility_service.py:12-25",
                    "Eligibility check returns inconsistent results for same input",
                    "Run same eligibility check multiple times",
                    f"Different scores: {results}",
                    "Should return consistent results",
                    "High"
                )
                
        except Exception as e:
            self.log_issue(
                "ELG007",
                "services/eligibility_service.py",
                "Eligibility service testing failed",
                "Test eligibility service edge cases",
                f"Exception: {e}",
                "Should handle edge cases gracefully",
                "High"
            )
    
    def test_search_filtering_accuracy(self):
        """Test search filtering accuracy and edge cases"""
        print("\n🔍 Testing Search Filtering Accuracy...")
        
        try:
            # Test 1: Empty keyword should return all results
            response = requests.get(f"{self.base_url}/api/v1/scholarships?keyword=")
            if response.status_code == 200:
                empty_keyword_results = response.json()["total_count"]
                
                response_all = requests.get(f"{self.base_url}/api/v1/scholarships")
                if response_all.status_code == 200:
                    all_results = response_all.json()["total_count"]
                    
                    if empty_keyword_results != all_results:
                        self.log_issue(
                            "SRC003",
                            "services/scholarship_service.py:37-44",
                            "Empty keyword filter returns different count than no filter",
                            "Compare ?keyword= vs no keyword parameter",
                            f"Empty: {empty_keyword_results}, All: {all_results}",
                            "Should return same count",
                            "Medium"
                        )
            
            # Test 2: Case sensitivity in keyword search
            response_lower = requests.get(f"{self.base_url}/api/v1/scholarships?keyword=engineering")
            response_upper = requests.get(f"{self.base_url}/api/v1/scholarships?keyword=ENGINEERING")
            
            if (response_lower.status_code == 200 and response_upper.status_code == 200):
                lower_count = response_lower.json()["total_count"]
                upper_count = response_upper.json()["total_count"]
                
                if lower_count != upper_count:
                    self.log_issue(
                        "SRC004",
                        "services/scholarship_service.py:37-44",
                        "Keyword search is case sensitive",
                        "Search for 'engineering' vs 'ENGINEERING'",
                        f"Lower: {lower_count}, Upper: {upper_count}",
                        "Should return same results regardless of case",
                        "Medium"
                    )
            
            # Test 3: Special characters in keyword
            special_chars = ["<script>", "'; DROP TABLE", "null", "undefined"]
            for char in special_chars:
                response = requests.get(f"{self.base_url}/api/v1/scholarships", 
                                      params={"keyword": char})
                if response.status_code != 200:
                    self.log_issue(
                        "SRC005",
                        "services/scholarship_service.py:37-44",
                        f"Special character '{char}' in keyword causes server error",
                        f"Search with keyword='{char}'",
                        f"Status: {response.status_code}",
                        "Should handle special characters gracefully",
                        "High"
                    )
                    
        except Exception as e:
            self.log_issue(
                "SRC006",
                "services/scholarship_service.py",
                "Search filtering testing failed",
                "Test search filtering functionality",
                f"Exception: {e}",
                "Should handle search requests properly",
                "High"
            )
    
    def test_analytics_data_integrity(self):
        """Test analytics data integrity and accuracy"""
        print("\n🔍 Testing Analytics Data Integrity...")
        
        try:
            # Test 1: Analytics summary before and after interaction
            initial_analytics = requests.get(f"{self.base_url}/api/v1/analytics/summary")
            if initial_analytics.status_code == 200:
                initial_data = initial_analytics.json()
                initial_interactions = initial_data["total_interactions"]
                
                # Perform an action that should be logged
                requests.get(f"{self.base_url}/api/v1/scholarships/sch_001?user_id=test_analytics")
                
                # Check if analytics updated
                final_analytics = requests.get(f"{self.base_url}/api/v1/analytics/summary")
                if final_analytics.status_code == 200:
                    final_data = final_analytics.json()
                    final_interactions = final_data["total_interactions"]
                    
                    if final_interactions <= initial_interactions:
                        self.log_issue(
                            "ANL003",
                            "services/analytics_service.py:16-22",
                            "Analytics not properly tracking interactions",
                            "Check analytics before/after scholarship view",
                            f"Before: {initial_interactions}, After: {final_interactions}",
                            "Should increment interaction count",
                            "Medium"
                        )
            
            # Test 2: User analytics for invalid time periods
            invalid_periods = [-1, 0, 999999]
            for period in invalid_periods:
                response = requests.get(f"{self.base_url}/api/v1/analytics/summary?days={period}")
                if response.status_code != 422 and period <= 0:
                    self.log_issue(
                        "ANL004",
                        "routers/analytics.py:10-25",
                        f"Analytics accepts invalid time period: {period}",
                        f"GET /analytics/summary?days={period}",
                        f"Status: {response.status_code}",
                        "Should reject invalid time periods",
                        "Medium"
                    )
                    
        except Exception as e:
            self.log_issue(
                "ANL005",
                "services/analytics_service.py",
                "Analytics testing failed",
                "Test analytics functionality",
                f"Exception: {e}",
                "Should handle analytics requests properly",
                "Medium"
            )
    
    def test_data_model_constraints(self):
        """Test data model constraints and validation"""
        print("\n🔍 Testing Data Model Constraints...")
        
        try:
            from models.scholarship import SearchFilters, FieldOfStudy
            from models.user import UserProfile
            
            # Test 1: SearchFilters boundary values
            try:
                # Test maximum limit
                filters = SearchFilters(limit=101)  # Above max of 100
                self.log_issue(
                    "MDL004",
                    "models/scholarship.py:86",
                    "SearchFilters accepts limit above maximum of 100",
                    "Create SearchFilters with limit=101",
                    "No validation error raised",
                    "Should enforce maximum limit of 100",
                    "Medium"
                )
            except Exception:
                pass  # Expected behavior
            
            # Test 2: UserProfile with invalid field combinations
            try:
                profile = UserProfile(
                    id="test",
                    gpa=4.0,
                    grade_level="graduate",
                    age=15  # Too young for graduate level
                )
                
                # This might be a business logic issue rather than validation
                if profile.age < 18 and profile.grade_level == "graduate":
                    self.log_issue(
                        "MDL005",
                        "models/user.py:6-16",
                        "UserProfile allows inconsistent age/grade_level combinations",
                        "Create UserProfile with age=15 and grade_level='graduate'",
                        "Profile created without validation error",
                        "Should validate logical consistency between fields",
                        "Low"
                    )
            except Exception:
                pass
                
        except Exception as e:
            self.log_issue(
                "MDL006",
                "models/",
                "Data model testing failed",
                "Test data model constraints",
                f"Exception: {e}",
                "Should validate model constraints properly",
                "Medium"
            )
    
    def test_error_handling_consistency(self):
        """Test error handling consistency across the API"""
        print("\n🔍 Testing Error Handling Consistency...")
        
        try:
            # Test 1: 404 errors format consistency
            not_found_endpoints = [
                "/api/v1/scholarships/nonexistent",
                "/api/v1/analytics/user/nonexistent"
            ]
            
            error_formats = []
            for endpoint in not_found_endpoints:
                response = requests.get(f"{self.base_url}{endpoint}")
                if response.status_code == 404:
                    try:
                        error_data = response.json()
                        error_formats.append(list(error_data.keys()))
                    except:
                        error_formats.append("non-json")
            
            # Check if error formats are consistent
            if len(set(map(str, error_formats))) > 1:
                self.log_issue(
                    "ERR001",
                    "routers/scholarships.py, routers/analytics.py",
                    "Inconsistent 404 error response formats",
                    "Test various 404 endpoints for format consistency",
                    f"Different formats: {error_formats}",
                    "Should have consistent error response format",
                    "Low"
                )
            
            # Test 2: Server error handling
            # This would require intentionally causing server errors
            
        except Exception as e:
            self.log_issue(
                "ERR002",
                "routers/",
                "Error handling testing failed",
                "Test error handling consistency",
                f"Exception: {e}",
                "Should handle errors consistently",
                "Medium"
            )
    
    def run_focused_analysis(self):
        """Run focused QA analysis"""
        print("🎯 Starting Focused QA Analysis...")
        print("=" * 60)
        
        try:
            self.test_lsp_diagnostics_issues()
            self.test_api_response_consistency()
            self.test_eligibility_logic_edge_cases()
            self.test_search_filtering_accuracy()
            self.test_analytics_data_integrity()
            self.test_data_model_constraints()
            self.test_error_handling_consistency()
        except Exception as e:
            print(f"❌ Focused analysis error: {e}")
            traceback.print_exc()
        
        return self.generate_report()
    
    def generate_report(self):
        """Generate detailed QA report"""
        print("\n" + "=" * 60)
        print("📊 FOCUSED QA ANALYSIS REPORT")
        print("=" * 60)
        
        if not self.issues:
            print("✅ No additional issues identified in focused analysis!")
            return
        
        # Group by severity
        critical = [i for i in self.issues if i["severity"] == "Critical"]
        high = [i for i in self.issues if i["severity"] == "High"]
        medium = [i for i in self.issues if i["severity"] == "Medium"]
        low = [i for i in self.issues if i["severity"] == "Low"]
        
        print(f"📈 FOCUSED ANALYSIS SUMMARY:")
        print(f"   Critical: {len(critical)}")
        print(f"   High:     {len(high)}")
        print(f"   Medium:   {len(medium)}")
        print(f"   Low:      {len(low)}")
        print(f"   Total:    {len(self.issues)}")
        print()
        
        # Detailed issues
        for issue in self.issues:
            print(f"🐛 {issue['issue_id']} - {issue['severity'].upper()}")
            print(f"   Location: {issue['location']}")
            print(f"   Description: {issue['description']}")
            print(f"   Steps: {issue['steps_to_reproduce']}")
            print(f"   Observed: {issue['observed_output']}")
            print(f"   Expected: {issue['expected_output']}")
            print()
        
        return self.issues


if __name__ == "__main__":
    qa_analysis = FocusedQAAnalysis()
    issues = qa_analysis.run_focused_analysis()
    
    # Save focused report
    with open("qa_focused_report.json", "w") as f:
        json.dump({
            "timestamp": datetime.utcnow().isoformat(),
            "analysis_type": "focused",
            "total_issues": len(issues),
            "issues": issues
        }, f, indent=2)
    
    print(f"📋 Focused analysis report saved to qa_focused_report.json")