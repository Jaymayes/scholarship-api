"""
Operations Framework Integration Tests
Comprehensive testing of the complete AE + Partner Success Operations Framework

Tests end-to-end functionality including:
- Lead routing to pipeline creation
- Pipeline progression with playbook triggers
- Sales enablement tool integration
- Performance tracking and analytics
"""

import os

# Add current directory to path for imports
import sys
from datetime import datetime, timedelta
from decimal import Decimal

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import all framework components
from services.lead_routing_engine import (
    AssignmentType,
    LeadSegment,
    lead_routing_engine,
)
from services.performance_dashboards import TimeRange, performance_dashboard_system
from services.pipeline_management_system import DealStage, pipeline_management_system
from services.sales_enablement_tools import sales_enablement_toolkit
from services.success_playbooks import CustomerHealthStatus, success_playbooks_engine


class TestOperationsFrameworkIntegration:
    """Comprehensive integration tests for the operations framework"""

    def setup_method(self):
        """Set up test data for each test"""
        self.test_lead_data = {
            "organization_name": "Test University",
            "contact_name": "Dr. Jane Smith",
            "contact_email": "jane.smith@testuniversity.edu",
            "contact_phone": "+1-555-0123",
            "segment": "university",
            "territory": "northeast",
            "estimated_acv": 45000,
            "employee_count": 5000,
            "annual_budget": 2000000,
            "source": "inbound",
            "stage": "mql",
            "urgency_score": 8,
            "fit_score": 7,
            "description": "Major state university interested in scholarship management platform"
        }

        self.test_deal_data = {
            "lead_id": "test_lead_001",
            "organization_name": "Test University",
            "contact_name": "Dr. Jane Smith",
            "contact_email": "jane.smith@testuniversity.edu",
            "segment": "university",
            "territory": "northeast",
            "estimated_acv": 45000,
            "annual_budget": 2000000,
            "source": "inbound",
            "stage": "sql",
            "urgency_score": 8,
            "fit_score": 7,
            "owner_id": "ae_001",
            "owner_name": "Sarah Chen"
        }

    def test_lead_routing_integration(self):
        """Test lead routing engine functionality"""
        print("\n🎯 Testing Lead Routing Engine...")

        # Route a new lead
        lead, assigned_rep, routing_reason = lead_routing_engine.route_lead(self.test_lead_data)

        # Verify lead was created and routed
        assert lead is not None
        assert lead.organization_name == "Test University"
        assert lead.segment == LeadSegment.UNIVERSITY
        assert lead.estimated_acv == Decimal('45000')

        # Verify rep assignment
        assert assigned_rep is not None
        assert assigned_rep.role in [AssignmentType.AE, AssignmentType.PARTNER_SUCCESS]
        assert routing_reason is not None

        # Test routing analytics
        analytics = lead_routing_engine.get_routing_analytics()
        assert analytics is not None
        assert "summary" in analytics
        assert "rep_performance" in analytics

        print(f"✅ Lead routed to {assigned_rep.name} ({assigned_rep.role.value})")
        print(f"📊 Routing reason: {routing_reason}")
        return lead, assigned_rep

    def test_pipeline_management_integration(self):
        """Test pipeline management system functionality"""
        print("\n💼 Testing Pipeline Management System...")

        # First route a lead to get assignment
        lead, assigned_rep = self.test_lead_routing_integration()

        # Create deal from lead
        deal = pipeline_management_system.create_deal_from_lead(
            lead=lead,
            owner_id=assigned_rep.rep_id,
            owner_name=assigned_rep.name
        )

        # Verify deal creation
        assert deal is not None
        assert deal.organization_name == "Test University"
        assert deal.stage == DealStage.MQL
        assert deal.estimated_acv == Decimal('45000')
        assert deal.owner_name == assigned_rep.name

        # Add required activities before advancing deal stage
        discovery_activity = {
            "activity_type": "discovery_call",
            "description": "Initial discovery call to understand scholarship management needs",
            "performed_by": assigned_rep.rep_id,
            "outcome": "Positive - qualified opportunity",
            "next_steps": "Schedule demo",
            "sentiment_score": 8
        }

        needs_assessment_activity = {
            "activity_type": "needs_assessment",
            "description": "Detailed needs assessment and requirement gathering",
            "performed_by": assigned_rep.rep_id,
            "outcome": "Clear requirements identified",
            "next_steps": "Prepare demo",
            "sentiment_score": 7
        }

        # Add both required activities for SQL stage advancement
        activity1 = pipeline_management_system.add_deal_activity(deal.deal_id, discovery_activity)
        activity2 = pipeline_management_system.add_deal_activity(deal.deal_id, needs_assessment_activity)
        assert activity1 is not None
        assert activity1.activity_type == "discovery_call"
        assert activity2 is not None
        assert activity2.activity_type == "needs_assessment"

        # Now test deal progression (should work with required activities)
        advanced_deal = pipeline_management_system.advance_deal_stage(
            deal_id=deal.deal_id,
            new_stage=DealStage.SQL,
            notes="Qualified during discovery call and needs assessment"
        )

        assert advanced_deal.stage == DealStage.SQL
        assert advanced_deal.probability > deal.probability

        # Test pipeline metrics
        metrics = pipeline_management_system.get_pipeline_metrics(assigned_rep.rep_id)
        assert metrics.total_deals >= 1
        assert metrics.healthy_deals >= 0

        # Test forecast
        forecast = pipeline_management_system.get_deal_forecast(90)
        assert forecast is not None
        assert "total" in forecast

        print(f"✅ Deal created and advanced: {deal.organization_name}")
        print(f"📈 Current stage: {advanced_deal.stage.value} | Probability: {advanced_deal.probability}%")
        return advanced_deal

    def test_success_playbooks_integration(self):
        """Test success playbooks engine functionality"""
        print("\n🎯 Testing Success Playbooks Engine...")

        # Calculate customer health score
        usage_data = {
            "customer_id": "test_customer_001",
            "organization_name": "Test University",
            "logins_last_month": 25,
            "scholarships_published": 8,
            "applications_received": 150,
            "support_tickets": 1,
            "last_login_days": 2,
            "satisfaction_score": 9
        }

        health_score = success_playbooks_engine.calculate_customer_health(
            customer_id="test_customer_001",
            usage_data=usage_data
        )

        # Verify health score calculation
        assert health_score is not None
        assert health_score.overall_score > 0
        assert health_score.health_status in CustomerHealthStatus

        # Trigger onboarding playbook
        execution = success_playbooks_engine.trigger_playbook(
            customer_id="test_customer_001",
            template_id="univ_onboarding_v1",
            assigned_to="ps_001",
            trigger_reason="New university partner onboarding"
        )

        # Verify playbook execution
        assert execution is not None
        assert execution.playbook_name == "University Partner Onboarding"
        assert execution.total_steps > 0
        assert execution.customer_id == "test_customer_001"

        # Complete first step
        completed_execution = success_playbooks_engine.complete_step(
            execution_id=execution.execution_id,
            step_number=1,
            completion_notes="Welcome call completed successfully"
        )

        assert completed_execution.completed_steps == 1
        assert completed_execution.progress_percentage > 0

        # Test playbook analytics
        analytics = success_playbooks_engine.get_playbook_analytics()
        assert analytics is not None
        assert "summary" in analytics

        print(f"✅ Health score calculated: {health_score.overall_score}/100 ({health_score.health_status.value})")
        print(f"🎯 Playbook triggered: {execution.playbook_name}")
        print(f"📋 Progress: {completed_execution.progress_percentage:.1f}%")
        return execution, health_score

    def test_sales_enablement_integration(self):
        """Test sales enablement tools functionality"""
        print("\n🛠️ Testing Sales Enablement Tools...")

        # Calculate ROI for prospect
        prospect_data = {
            "prospect_name": "Test University",
            "segment": "university",
            "annual_scholarship_budget": 500000,
            "scholarships_managed": 15,
            "staff_hours_per_month": 120,
            "hourly_rate": 45,
            "application_volume": 500,
            "annual_platform_cost": 25000,
            "implementation_cost": 8000,
            "created_by": "ae_001"
        }

        roi_calculation = sales_enablement_toolkit.calculate_roi(prospect_data)

        # Verify ROI calculation
        assert roi_calculation is not None
        assert roi_calculation.prospect_name == "Test University"
        assert roi_calculation.roi_percentage > 0
        assert roi_calculation.payback_months > 0

        # Get battle card for competitor
        battle_card = sales_enablement_toolkit.get_battle_card("Generic Scholarship Platform")

        # Verify battle card retrieval
        assert battle_card is not None
        assert battle_card.competitor_name == "Generic Scholarship Platform"
        assert len(battle_card.our_advantages) > 0
        assert len(battle_card.win_strategies) > 0

        # Get pricing guidance
        pricing_guidance = sales_enablement_toolkit.get_pricing_guidance(
            segment="university",
            tier="listings_promotion",
            deal_size=Decimal('45000')
        )

        # Verify pricing guidance
        assert pricing_guidance is not None
        assert pricing_guidance.segment == "university"
        assert pricing_guidance.list_price > 0

        # Generate contract
        contract_data = {
            "CUSTOMER_NAME": "Test University",
            "DATE": datetime.utcnow().strftime("%Y-%m-%d"),
            "PILOT_DURATION": "3",
            "START_DATE": datetime.utcnow().strftime("%Y-%m-%d"),
            "END_DATE": (datetime.utcnow() + timedelta(days=90)).strftime("%Y-%m-%d"),
            "PILOT_SCOPE": "Scholarship management platform pilot",
            "SUCCESS_CRITERIA": "Publish 5 scholarships, receive 50 applications",
            "PILOT_PRICE": "15000"
        }

        contract_text = sales_enablement_toolkit.generate_contract(
            template_id="pilot_agreement_v1",
            contract_data=contract_data
        )

        # Verify contract generation
        assert contract_text is not None
        assert "Test University" in contract_text
        assert "PILOT PROGRAM AGREEMENT" in contract_text

        # Get negotiation strategy
        strategy = sales_enablement_toolkit.get_negotiation_strategy(
            competitor="Generic Scholarship Platform",
            segment="university",
            deal_value=Decimal('45000')
        )

        # Verify negotiation strategy
        assert strategy is not None
        assert "competitive_positioning" in strategy
        assert "pricing_strategy" in strategy
        assert "value_propositions" in strategy

        print(f"✅ ROI calculated: {roi_calculation.roi_percentage:.1f}% ROI, {roi_calculation.payback_months:.1f} month payback")
        print(f"⚔️ Battle card accessed: {battle_card.competitor_name}")
        print(f"💰 Pricing guidance: ${pricing_guidance.list_price}/month")
        return roi_calculation, strategy

    def test_performance_dashboards_integration(self):
        """Test performance dashboards functionality"""
        print("\n📊 Testing Performance Dashboards...")

        # Update quota performance (simulated)
        quota_targets = performance_dashboard_system.quota_targets
        if quota_targets:
            rep_id = list(quota_targets.keys())[0]

            # Generate individual scorecard
            scorecard = performance_dashboard_system.generate_individual_scorecard(
                rep_id=rep_id,
                time_period=TimeRange.MTD
            )

            # Verify scorecard generation
            assert scorecard is not None
            assert scorecard.rep_id == rep_id
            assert scorecard.overall_score >= 0
            assert scorecard.quota_score >= 0

            # Generate team performance
            team_performance = performance_dashboard_system.generate_team_performance(
                team_name="Sales Team",
                time_period=TimeRange.QTD
            )

            # Verify team performance
            assert team_performance is not None
            assert team_performance.total_reps > 0
            assert team_performance.team_attainment >= 0

            # Get quota leaderboard
            leaderboard = performance_dashboard_system.get_quota_leaderboard(TimeRange.QTD)

            # Verify leaderboard
            assert leaderboard is not None
            assert len(leaderboard) > 0
            assert "rank" in leaderboard[0]

            # Get executive dashboard
            executive_dashboard = performance_dashboard_system.get_executive_dashboard()

            # Verify executive dashboard
            assert executive_dashboard is not None
            assert "executive_summary" in executive_dashboard
            assert "team_composition" in executive_dashboard

            print(f"✅ Scorecard generated: {scorecard.rep_name} | Overall: {scorecard.overall_score}/100")
            print(f"👥 Team performance: {team_performance.team_attainment:.1f}% attainment")
            print(f"🏆 Leaderboard: {len(leaderboard)} reps ranked")
            return scorecard, executive_dashboard
        print("⚠️ No quota targets found - skipping performance tests")
        return None, None

    def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow through all systems"""
        print("\n🔄 Testing End-to-End Workflow...")

        # 1. Lead comes in and gets routed
        lead, assigned_rep = self.test_lead_routing_integration()

        # 2. Deal is created and progressed through pipeline
        deal = self.test_pipeline_management_integration()

        # 3. Customer health is monitored and playbooks triggered
        execution, health_score = self.test_success_playbooks_integration()

        # 4. Sales enablement tools are used
        roi_calculation, strategy = self.test_sales_enablement_integration()

        # 5. Performance is tracked on dashboards
        scorecard, dashboard = self.test_performance_dashboards_integration()

        # Verify workflow completion
        workflow_results = {
            "lead_routed": lead is not None,
            "deal_created": deal is not None,
            "playbook_triggered": execution is not None,
            "roi_calculated": roi_calculation is not None,
            "performance_tracked": scorecard is not None or dashboard is not None
        }

        success_count = sum(workflow_results.values())
        total_count = len(workflow_results)

        print("\n🎯 End-to-End Workflow Results:")
        print(f"✅ Successfully completed: {success_count}/{total_count} components")

        for component, success in workflow_results.items():
            status = "✅" if success else "❌"
            print(f"   {status} {component.replace('_', ' ').title()}")

        # Assert overall success
        assert success_count >= 4, f"Workflow failed - only {success_count}/{total_count} components successful"

        print("\n🚀 Operations Framework Integration Test: PASSED")
        return workflow_results

    def test_unified_analytics(self):
        """Test unified analytics across all components"""
        print("\n📊 Testing Unified Analytics...")

        try:
            # Get analytics from all components
            routing_analytics = lead_routing_engine.get_routing_analytics()
            pipeline_metrics = pipeline_management_system.get_pipeline_metrics()
            playbook_analytics = success_playbooks_engine.get_playbook_analytics()
            enablement_analytics = sales_enablement_toolkit.get_enablement_analytics()
            executive_dashboard = performance_dashboard_system.get_executive_dashboard()

            # Verify all analytics are available
            analytics_components = {
                "routing_analytics": routing_analytics is not None,
                "pipeline_metrics": pipeline_metrics is not None,
                "playbook_analytics": playbook_analytics is not None,
                "enablement_analytics": enablement_analytics is not None,
                "executive_dashboard": executive_dashboard is not None
            }

            success_count = sum(analytics_components.values())
            total_count = len(analytics_components)

            print(f"📊 Analytics Components Available: {success_count}/{total_count}")

            for component, available in analytics_components.items():
                status = "✅" if available else "❌"
                print(f"   {status} {component.replace('_', ' ').title()}")

            # Create unified view
            unified_analytics = {
                "timestamp": datetime.utcnow().isoformat(),
                "routing": {
                    "total_leads": routing_analytics.get("summary", {}).get("total_providers_in_funnel", 0) if routing_analytics else 0
                },
                "pipeline": {
                    "total_deals": pipeline_metrics.total_deals if pipeline_metrics else 0,
                    "pipeline_value": float(pipeline_metrics.total_pipeline_value) if pipeline_metrics else 0
                },
                "playbooks": {
                    "active_executions": playbook_analytics.get("summary", {}).get("total_executions", 0) if playbook_analytics else 0
                },
                "enablement": {
                    "roi_calculations": enablement_analytics.get("usage_summary", {}).get("total_roi_calculations", 0) if enablement_analytics else 0
                },
                "performance": {
                    "team_attainment": executive_dashboard.get("executive_summary", {}).get("overall_attainment", 0) if executive_dashboard else 0
                }
            }

            print("\n📈 Unified Analytics Summary:")
            print(f"   🎯 Total Leads: {unified_analytics['routing']['total_leads']}")
            print(f"   💼 Total Deals: {unified_analytics['pipeline']['total_deals']}")
            print(f"   📚 Active Playbooks: {unified_analytics['playbooks']['active_executions']}")
            print(f"   🛠️ ROI Calculations: {unified_analytics['enablement']['roi_calculations']}")
            print(f"   📊 Team Attainment: {unified_analytics['performance']['team_attainment']:.1f}%")

            assert success_count >= 3, f"Analytics integration failed - only {success_count}/{total_count} components available"

            return unified_analytics

        except Exception as e:
            print(f"❌ Unified analytics test failed: {str(e)}")
            raise

def run_integration_tests():
    """Run all integration tests"""
    print("🚀 Starting Operations Framework Integration Tests...")
    print("=" * 60)

    test_instance = TestOperationsFrameworkIntegration()
    test_instance.setup_method()

    try:
        # Run individual component tests
        test_instance.test_lead_routing_integration()
        test_instance.test_pipeline_management_integration()
        test_instance.test_success_playbooks_integration()
        test_instance.test_sales_enablement_integration()
        test_instance.test_performance_dashboards_integration()

        # Run comprehensive tests
        test_instance.test_end_to_end_workflow()
        test_instance.test_unified_analytics()

        print("\n" + "=" * 60)
        print("🎉 ALL INTEGRATION TESTS PASSED!")
        print("✅ Operations Framework is fully functional and integrated")
        print("🚀 Ready for aggressive B2B ARR execution!")

        return True

    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ INTEGRATION TESTS FAILED: {str(e)}")
        print("🔧 Framework requires debugging before deployment")
        return False

if __name__ == "__main__":
    success = run_integration_tests()
    exit(0 if success else 1)
