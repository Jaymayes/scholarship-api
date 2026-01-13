"""
Payments Router - Stripe Checkout Integration
Operation Vital Signs: Install the Cash Register

Provides centralized payment endpoints for A5 (student_pilot) and A6 (provider_register)
"""

import logging
import os
import json
from datetime import datetime
from typing import Optional, Any, Dict
from fastapi import APIRouter, HTTPException, Request, Header
from pydantic import BaseModel
import stripe

from services.stripe_client import configure_stripe, get_publishable_key, get_stripe_secret_key, StripeConfigurationError
from services.revenue_guardrails import (
    check_charge_allowed, record_charge, record_refund,
    get_limits_status, get_stripe_mode, is_stripe_live_mode
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/payment", tags=["Payments"])


class CreateCheckoutSessionRequest(BaseModel):
    """Request body for creating a Stripe checkout session"""
    price_id: str
    success_url: str
    cancel_url: str
    customer_email: Optional[str] = None
    mode: str = "payment"
    metadata: Optional[Dict[str, str]] = None


class CheckoutSessionResponse(BaseModel):
    """Response with checkout session URL"""
    url: str
    session_id: str


class PublishableKeyResponse(BaseModel):
    """Response with Stripe publishable key"""
    publishable_key: str


@router.post("/create-checkout-session", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    request_data: CreateCheckoutSessionRequest,
    request: Request
) -> CheckoutSessionResponse:
    """
    Create a Stripe Checkout Session
    
    Called by A5 (student_pilot) and A6 (provider_register) to initiate payments.
    
    **Request Body:**
    ```json
    {
        "price_id": "price_1ABC...",
        "success_url": "https://student-pilot.../success?session_id={CHECKOUT_SESSION_ID}",
        "cancel_url": "https://student-pilot.../cancel",
        "customer_email": "user@example.com",
        "mode": "payment",
        "metadata": {"user_id": "123", "app": "student_pilot"}
    }
    ```
    
    **Response:**
    ```json
    {
        "url": "https://checkout.stripe.com/...",
        "session_id": "cs_..."
    }
    ```
    
    **Modes:**
    - `payment`: One-time payment (credits purchase)
    - `subscription`: Recurring subscription (provider plans)
    """
    try:
        await configure_stripe()
    except StripeConfigurationError as e:
        logger.error(f"Stripe not configured: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "error": "stripe_not_configured",
                "message": str(e),
                "action": "Configure Stripe integration in Replit to enable payments"
            }
        )
    
    try:
        create_params: Dict[str, Any] = {
            "line_items": [{"price": request_data.price_id, "quantity": 1}],
            "mode": request_data.mode,
            "success_url": request_data.success_url,
            "cancel_url": request_data.cancel_url,
        }
        
        if request_data.customer_email:
            create_params["customer_email"] = request_data.customer_email
        
        if request_data.metadata:
            create_params["metadata"] = request_data.metadata
        
        session = stripe.checkout.Session.create(**create_params)
        
        session_url = session.url
        session_id = session.id
        
        if not session_url or not session_id:
            raise HTTPException(
                status_code=500,
                detail="Failed to create checkout session - missing URL or ID"
            )
        
        logger.info(f"Checkout session created: {session_id} for price {request_data.price_id}")
        
        return CheckoutSessionResponse(
            url=session_url,
            session_id=session_id
        )
        
    except HTTPException:
        raise
    except stripe.StripeError as e:
        error_msg = str(e)
        logger.error(f"Stripe error creating checkout session: {error_msg}")
        
        if "No API key provided" in error_msg or "Invalid API Key" in error_msg:
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "stripe_credentials_invalid",
                    "message": "Stripe API key is missing or invalid",
                    "action": "Reconfigure Stripe integration in Replit"
                }
            )
        
        if "No such price" in error_msg:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid price_id: {request_data.price_id}"
            )
        
        raise HTTPException(
            status_code=500,
            detail=f"Stripe error: {error_msg}"
        )
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed to create checkout session: {error_msg}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create checkout session"
        )


@router.get("/publishable-key", response_model=PublishableKeyResponse)
async def get_stripe_publishable_key() -> PublishableKeyResponse:
    """
    Get Stripe publishable key for frontend integration
    
    **Response:**
    ```json
    {
        "publishable_key": "pk_test_..."
    }
    ```
    """
    try:
        key = await get_publishable_key()
        return PublishableKeyResponse(publishable_key=key)
    except StripeConfigurationError as e:
        logger.error(f"Stripe not configured: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "error": "stripe_not_configured",
                "message": str(e),
                "action": "Configure Stripe integration in Replit to enable payments"
            }
        )
    except Exception as e:
        logger.error(f"Failed to get publishable key: {e}")
        raise HTTPException(
            status_code=503,
            detail="Payment service temporarily unavailable"
        )


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(..., alias="stripe-signature")
) -> Dict[str, bool]:
    """
    Stripe webhook endpoint for payment events
    
    Handles:
    - checkout.session.completed: Grant credits or activate subscription
    - invoice.paid: Subscription renewal
    - customer.subscription.deleted: Subscription cancellation
    
    **Security:**
    - Validates webhook signature using STRIPE_WEBHOOK_SECRET
    - Only processes events from Stripe
    """
    try:
        payload = await request.body()
        payload_str = payload.decode("utf-8")
        
        webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET")
        
        if not webhook_secret:
            logger.error("STRIPE_WEBHOOK_SECRET not configured - rejecting webhook")
            raise HTTPException(
                status_code=503,
                detail="Webhook signature verification unavailable - STRIPE_WEBHOOK_SECRET not configured"
            )
        
        try:
            event = stripe.Webhook.construct_event(
                payload_str,
                stripe_signature,
                webhook_secret
            )
        except stripe.SignatureVerificationError as e:
            logger.error(f"Webhook signature verification failed: {e}")
            raise HTTPException(status_code=400, detail="Invalid signature")
        
        event_type = event.type
        event_data = event.data.object
        
        logger.info(f"Stripe webhook received: event_type={event_type}, signature_verified=true")
        
        if event_type == "checkout.session.completed":
            await handle_checkout_completed(event_data)
        
        elif event_type == "invoice.paid":
            await handle_invoice_paid(event_data)
        
        elif event_type == "customer.subscription.deleted":
            await handle_subscription_cancelled(event_data)
        
        return {"received": True}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


async def handle_checkout_completed(session: Any) -> None:
    """
    Handle successful checkout completion
    
    - For payment mode: Grant credits to user via external billing service
    - For subscription mode: Activate provider subscription
    - Emit revenue event to A8 Command Center
    """
    import httpx
    
    if isinstance(session, dict):
        session_id = session.get("id", "unknown")
        metadata = session.get("metadata", {})
        mode = session.get("mode", "payment")
        amount_total = session.get("amount_total", 0)
        currency = session.get("currency", "usd")
    else:
        session_id = getattr(session, "id", "unknown")
        metadata = getattr(session, "metadata", {}) or {}
        mode = getattr(session, "mode", "payment")
        amount_total = getattr(session, "amount_total", 0)
        currency = getattr(session, "currency", "usd")
    
    logger.info(f"Checkout completed: {session_id}, amount={amount_total} {currency}")
    
    if mode == "payment":
        user_id = metadata.get("user_id", "unknown")
        app = metadata.get("app", "scholarship_api")
        logger.info(f"Credit purchase completed. User: {user_id}, App: {app}")
        record_charge(user_id, amount_total)
    elif mode == "subscription":
        provider_id = metadata.get("provider_id", "unknown")
        logger.info(f"Subscription activated. Provider: {provider_id}")
        record_charge(provider_id, amount_total)
    
    a8_url = os.environ.get("A8_EVENTS_URL", "https://auto-com-center-jamarrlmayes.replit.app/events")
    a8_key = os.environ.get("A8_KEY") or ""
    event_id = f"rev_{session_id}_{int(datetime.utcnow().timestamp())}"
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            revenue_event = {
                "event_name": "payment_succeeded",
                "source": "https://scholarship-api-jamarrlmayes.replit.app",
                "source_app_id": "A2",
                "app_id": "scholarship_api",
                "metric": "REVENUE",
                "status": "pass",
                "amount_cents": amount_total,
                "currency": currency,
                "session_id": session_id,
                "signature_verified": True,
                "ts": int(datetime.utcnow().timestamp() * 1000),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
            headers = {
                "Content-Type": "application/json",
                "x-scholar-protocol": "v3.5.1",
                "x-app-label": "A2",
                "x-event-id": event_id,
                "X-Protocol-Version": "v3.5.1",
                "X-Idempotency-Key": event_id
            }
            if a8_key:
                headers["Authorization"] = f"Bearer {a8_key}"
            
            response = await client.post(
                a8_url, 
                json=revenue_event,
                headers=headers
            )
            
            if response.status_code in (200, 201, 202):
                logger.info(f"Revenue event emitted to A8: {amount_total} cents, session={session_id}")
            else:
                logger.warning(f"A8 ingest returned {response.status_code}: {response.text}")
                
    except Exception as e:
        logger.warning(f"Failed to emit revenue event to A8 (non-blocking): {e}")


async def handle_invoice_paid(invoice: Any) -> None:
    """Handle subscription renewal"""
    if isinstance(invoice, dict):
        subscription_id = invoice.get("subscription", "unknown")
    else:
        subscription_id = getattr(invoice, "subscription", "unknown")
    logger.info(f"Subscription invoice paid: {subscription_id}")


async def handle_subscription_cancelled(subscription: Any) -> None:
    """Handle subscription cancellation"""
    if isinstance(subscription, dict):
        subscription_id = subscription.get("id", "unknown")
    else:
        subscription_id = getattr(subscription, "id", "unknown")
    logger.info(f"Subscription cancelled: {subscription_id}")


class TestCheckoutRequest(BaseModel):
    """Simplified request for revenue validation testing"""
    amount: int = 100
    currency: str = "usd"
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


@router.post("/create-test-session")
async def create_test_session(
    request_data: TestCheckoutRequest,
    request: Request
) -> Dict[str, Any]:
    """
    Create a test checkout session for revenue validation
    
    This is a simplified endpoint for the validation sequence (G1-G3).
    Creates a Stripe Checkout session with amount in cents.
    
    **Request Body:**
    ```json
    {"amount": 100, "currency": "usd"}
    ```
    
    **Response:**
    ```json
    {
        "checkout_url": "https://checkout.stripe.com/...",
        "session_id": "cs_test_...",
        "amount_cents": 100,
        "test_mode": true
    }
    ```
    """
    try:
        await configure_stripe()
    except StripeConfigurationError as e:
        logger.error(f"Stripe not configured: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "error": "stripe_not_configured",
                "message": str(e),
                "action": "Configure Stripe integration in Replit"
            }
        )
    
    app_base_url = os.environ.get("REPLIT_DEV_DOMAIN", "scholarship-api-jamarrlmayes.replit.app")
    if not app_base_url.startswith("http"):
        app_base_url = f"https://{app_base_url}"
    
    success_url = request_data.success_url or f"{app_base_url}/payment-success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = request_data.cancel_url or f"{app_base_url}/payment-cancel"
    
    try:
        session = stripe.checkout.Session.create(
            line_items=[{
                "price_data": {
                    "currency": request_data.currency,
                    "product_data": {
                        "name": "Revenue Validation Test",
                        "description": f"G1-G3 validation: ${request_data.amount / 100:.2f} test purchase"
                    },
                    "unit_amount": request_data.amount
                },
                "quantity": 1
            }],
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "validation_test": "true",
                "app": "scholarship_api",
                "amount_cents": str(request_data.amount)
            }
        )
        
        logger.info(f"Test checkout session created: {session.id} for ${request_data.amount / 100:.2f}")
        
        return {
            "checkout_url": session.url,
            "session_id": session.id,
            "amount_cents": request_data.amount,
            "test_mode": True,
            "message": "Complete checkout to trigger webhook and record revenue"
        }
        
    except stripe.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(status_code=500, detail=f"Stripe error: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to create test session: {e}")
        raise HTTPException(status_code=500, detail="Failed to create test session")


@router.get("/status")
async def payment_status() -> Dict[str, Any]:
    """
    Check payment service status
    
    **Response:**
    ```json
    {
        "status": "operational",
        "stripe_configured": true,
        "webhook_secret_configured": true,
        "mode": "TEST|LIVE",
        "guardrails": {...}
    }
    ```
    """
    stripe_configured = False
    try:
        secret_key = await get_stripe_secret_key()
        stripe_configured = bool(secret_key)
    except Exception:
        pass
    
    webhook_configured = bool(os.environ.get("STRIPE_WEBHOOK_SECRET"))
    
    return {
        "status": "operational" if stripe_configured else "degraded",
        "stripe_configured": stripe_configured,
        "webhook_secret_configured": webhook_configured,
        "mode": get_stripe_mode(),
        "guardrails": get_limits_status(),
        "message": "Payment endpoints ready" if stripe_configured else "Stripe credentials pending"
    }


@router.get("/guardrails")
async def get_guardrails_status() -> Dict[str, Any]:
    """
    Get revenue guardrails status - CFO-20260114-STRIPE-LIVE-25
    
    Shows current spending limits and utilization.
    """
    return {
        "status": "active",
        "mode": get_stripe_mode(),
        "limits": get_limits_status(),
        "cfo_authorization": "CFO-20260114-STRIPE-LIVE-25",
        "provider_payouts": "simulation_only_until_phase3"
    }
