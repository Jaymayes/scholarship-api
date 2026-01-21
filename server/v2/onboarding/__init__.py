"""
Onboarding Orchestrator - First-Upload Flow
Server V2 Module for guest signup and document upload orchestration

Protocol: A8 Telemetry v3.5.1
Events: GuestCreated, DocumentUploaded, DocumentScored
"""
from .orchestrator import OnboardingOrchestrator
from .router import router

__all__ = ["OnboardingOrchestrator", "router"]
