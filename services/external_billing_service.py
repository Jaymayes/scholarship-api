"""
External Billing Service
Handles credit grants and fee payments from external billing apps
"""

import hashlib
import hmac
import time
from datetime import datetime

from config.settings import get_settings
from models.external_billing import (
    CreditGrantRequest,
    ExternalCreditGrant,
    ExternalProviderFeePayment,
    ProviderFeePaymentRequest,
)
from models.monetization import CreditTransaction, CreditTransactionType
from utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class SignatureValidationError(Exception):
    """Raised when HMAC signature validation fails"""
    pass


class IdempotencyError(Exception):
    """Raised when duplicate transaction detected"""
    pass


class ExternalBillingService:
    """Service for processing external billing callbacks"""
    
    def __init__(self):
        self.credit_grants: dict[str, ExternalCreditGrant] = {}
        self.provider_payments: dict[str, ExternalProviderFeePayment] = {}
        self.processed_tx_ids: set[str] = set()
        self.analytics_events: list[dict] = []
        
    def validate_signature(self, payload: dict, signature: str, timestamp: int) -> None:
        """
        Validate HMAC signature and timestamp
        
        Args:
            payload: Request payload
            signature: HMAC signature from request
            timestamp: Unix timestamp from request
            
        Raises:
            SignatureValidationError: If signature invalid or timestamp expired
        """
        current_time = int(time.time())
        
        if abs(current_time - timestamp) > 300:
            raise SignatureValidationError("Request timestamp expired (>5 minutes old)")
        
        secret = getattr(settings, 'external_billing_secret', 'dev-secret-key-change-in-production').encode()
        
        payload_str = f"{payload.get('user_id', payload.get('provider_id'))}"
        payload_str += f"|{payload.get('credits', payload.get('amount_usd'))}"
        payload_str += f"|{payload.get('external_tx_id')}"
        payload_str += f"|{timestamp}"
        
        expected_signature = hmac.new(
            secret,
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected_signature):
            raise SignatureValidationError("Invalid HMAC signature")
            
        logger.info(f"Signature validated for tx {payload.get('external_tx_id')}")
    
    def check_idempotency(self, external_tx_id: str) -> None:
        """
        Check if transaction already processed
        
        Args:
            external_tx_id: External transaction ID
            
        Raises:
            IdempotencyError: If transaction already processed
        """
        if external_tx_id in self.processed_tx_ids:
            raise IdempotencyError(f"Transaction {external_tx_id} already processed")
    
    async def grant_credits(
        self,
        request: CreditGrantRequest,
        credit_balances: dict
    ) -> tuple[ExternalCreditGrant, float]:
        """
        Grant credits from external billing app
        
        Args:
            request: Credit grant request
            credit_balances: User credit balances (from monetization service)
            
        Returns:
            Tuple of (grant record, new balance)
        """
        try:
            self.validate_signature(
                request.model_dump(exclude={'signature'}),
                request.signature,
                request.timestamp
            )
            
            self.check_idempotency(request.external_tx_id)
            
            grant = ExternalCreditGrant(
                user_id=request.user_id,
                credits=request.credits,
                amount_usd=request.amount_usd,
                external_tx_id=request.external_tx_id,
                source_app=request.source_app,
                metadata=request.metadata
            )
            
            balance = credit_balances.get(request.user_id)
            if balance:
                balance.total_credits += request.credits
                balance.available_credits += request.credits
                balance.last_updated = datetime.utcnow()
                new_balance = balance.available_credits
            else:
                from models.monetization import CreditBalance
                balance = CreditBalance(
                    user_id=request.user_id,
                    total_credits=request.credits,
                    available_credits=request.credits,
                    last_updated=datetime.utcnow()
                )
                credit_balances[request.user_id] = balance
                new_balance = request.credits
            
            self.credit_grants[grant.id] = grant
            self.processed_tx_ids.add(request.external_tx_id)
            
            self.analytics_events.append({
                "event_type": "PaymentCompletedExternal",
                "user_id": request.user_id,
                "timestamp": datetime.utcnow(),
                "metadata": {
                    "amount_usd": request.amount_usd,
                    "credits": request.credits,
                    "source_app": request.source_app,
                    "external_tx_id": request.external_tx_id
                }
            })
            
            self.analytics_events.append({
                "event_type": "CreditBalanceUpdated",
                "user_id": request.user_id,
                "timestamp": datetime.utcnow(),
                "metadata": {
                    "delta": request.credits,
                    "reason": "external_grant",
                    "new_balance": new_balance
                }
            })
            
            logger.info(
                f"Granted {request.credits} credits to user {request.user_id} "
                f"from {request.source_app} (tx: {request.external_tx_id})"
            )
            
            return grant, new_balance
            
        except SignatureValidationError as e:
            logger.error(f"Signature validation failed: {str(e)}")
            raise
        except IdempotencyError as e:
            logger.warning(f"Duplicate transaction detected: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Failed to grant credits: {str(e)}")
            raise
    
    async def record_provider_fee_payment(
        self,
        request: ProviderFeePaymentRequest
    ) -> ExternalProviderFeePayment:
        """
        Record provider fee payment from external billing
        
        Args:
            request: Provider fee payment request
            
        Returns:
            Provider fee payment record
        """
        try:
            self.validate_signature(
                request.model_dump(exclude={'signature'}),
                request.signature,
                request.timestamp
            )
            
            self.check_idempotency(request.external_tx_id)
            
            payment = ExternalProviderFeePayment(
                provider_id=request.provider_id,
                amount_usd=request.amount_usd,
                period_start=request.period_start,
                period_end=request.period_end,
                external_tx_id=request.external_tx_id,
                metadata=request.metadata
            )
            
            self.provider_payments[payment.id] = payment
            self.processed_tx_ids.add(request.external_tx_id)
            
            self.analytics_events.append({
                "event_type": "ProviderFeePaidExternal",
                "provider_id": request.provider_id,
                "timestamp": datetime.utcnow(),
                "metadata": {
                    "amount_usd": request.amount_usd,
                    "period_start": request.period_start.isoformat(),
                    "period_end": request.period_end.isoformat(),
                    "external_tx_id": request.external_tx_id
                }
            })
            
            logger.info(
                f"Recorded ${request.amount_usd} fee payment for provider {request.provider_id} "
                f"(tx: {request.external_tx_id})"
            )
            
            return payment
            
        except SignatureValidationError as e:
            logger.error(f"Signature validation failed: {str(e)}")
            raise
        except IdempotencyError as e:
            logger.warning(f"Duplicate transaction detected: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Failed to record provider fee: {str(e)}")
            raise
    
    async def get_grant_by_external_id(self, external_tx_id: str) -> ExternalCreditGrant | None:
        """Get credit grant by external transaction ID"""
        for grant in self.credit_grants.values():
            if grant.external_tx_id == external_tx_id:
                return grant
        return None
    
    async def get_provider_payment_by_external_id(self, external_tx_id: str) -> ExternalProviderFeePayment | None:
        """Get provider payment by external transaction ID"""
        for payment in self.provider_payments.values():
            if payment.external_tx_id == external_tx_id:
                return payment
        return None
