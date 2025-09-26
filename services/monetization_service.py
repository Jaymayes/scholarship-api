# AI Scholarship Playbook - Monetization Service
# Credit system implementation with transparent pricing and guardrails

import asyncio
from datetime import datetime, timedelta

from models.monetization import (
    CREDIT_PACKAGES,
    FEATURE_CREDIT_COSTS,
    STARTER_CREDIT_GRANT,
    CreditAttachmentMetrics,
    CreditBalance,
    CreditPricing,
    CreditTransaction,
    CreditTransactionType,
    CreditUsageEvent,
    SpendGuardrail,
    UserCreditSummary,
)
from utils.logger import get_logger

logger = get_logger(__name__)

class CreditInsufficientError(Exception):
    """Raised when user has insufficient credits for operation"""
    def __init__(self, required: float, available: float):
        self.required = required
        self.available = available
        super().__init__(f"Insufficient credits: {required} required, {available} available")

class SpendLimitExceededError(Exception):
    """Raised when operation would exceed spending limits"""
    def __init__(self, limit_type: str, limit: float, current: float):
        self.limit_type = limit_type
        self.limit = limit
        self.current = current
        super().__init__(f"{limit_type} limit exceeded: {current} + operation > {limit}")

class MonetizationService:
    """Service for managing credit system and B2C monetization"""

    def __init__(self):
        self.pricing = CreditPricing()
        self.credit_balances: dict[str, CreditBalance] = {}
        self.transactions: list[CreditTransaction] = []
        self.guardrails: dict[str, SpendGuardrail] = {}

    async def initialize_user_credits(self, user_id: str) -> CreditBalance:
        """Initialize new user with starter credit grant"""
        try:
            # Check if user already has credits
            if user_id in self.credit_balances:
                return self.credit_balances[user_id]

            # Grant starter credits
            balance = CreditBalance(
                user_id=user_id,
                total_credits=STARTER_CREDIT_GRANT,
                available_credits=STARTER_CREDIT_GRANT,
                last_updated=datetime.utcnow()
            )

            # Record starter grant transaction
            transaction = CreditTransaction(
                user_id=user_id,
                transaction_type=CreditTransactionType.STARTER_GRANT,
                amount=STARTER_CREDIT_GRANT,
                description=f"Welcome bonus: {STARTER_CREDIT_GRANT} free credits",
                feature_used="onboarding_bonus"
            )

            # Store balance and transaction
            self.credit_balances[user_id] = balance
            self.transactions.append(transaction)

            # Initialize spending guardrails
            self.guardrails[user_id] = SpendGuardrail(user_id=user_id)

            logger.info(f"Initialized user {user_id} with {STARTER_CREDIT_GRANT} starter credits")
            return balance

        except Exception as e:
            logger.error(f"Failed to initialize credits for user {user_id}: {str(e)}")
            raise

    async def purchase_credits(
        self,
        user_id: str,
        package_id: str,
        payment_method_id: str
    ) -> tuple[CreditTransaction, CreditBalance]:
        """Process credit purchase with payment integration"""
        try:
            # Find credit package
            package = next((p for p in CREDIT_PACKAGES if p.package_id == package_id), None)
            if not package:
                raise ValueError(f"Invalid package ID: {package_id}")

            # Process payment (would integrate with Stripe in production)
            payment_success = await self._process_payment(
                user_id, package.price_usd, payment_method_id
            )

            if not payment_success:
                raise ValueError("Payment processing failed")

            # Calculate total credits (base + bonus)
            total_credits = package.credits + package.bonus_credits

            # Get current balance
            balance = self.credit_balances.get(user_id)
            if not balance:
                balance = await self.initialize_user_credits(user_id)

            # Update balance
            balance.total_credits += total_credits
            balance.available_credits += total_credits
            balance.last_updated = datetime.utcnow()

            # Record purchase transaction
            transaction = CreditTransaction(
                user_id=user_id,
                transaction_type=CreditTransactionType.PURCHASE,
                amount=total_credits,
                description=f"Purchased {package.name} ({package.credits}+{package.bonus_credits} credits)",
                cost_basis=package.price_usd,
                metadata={
                    "package_id": package_id,
                    "base_credits": package.credits,
                    "bonus_credits": package.bonus_credits,
                    "price_usd": package.price_usd,
                    "payment_method_id": payment_method_id
                }
            )

            self.transactions.append(transaction)
            logger.info(f"User {user_id} purchased {total_credits} credits for ${package.price_usd}")

            return transaction, balance

        except Exception as e:
            logger.error(f"Credit purchase failed for user {user_id}: {str(e)}")
            raise

    async def consume_credits(
        self,
        user_id: str,
        feature: str,
        token_count: int,
        operation_id: str
    ) -> CreditUsageEvent:
        """Consume credits for AI feature usage with guardrails"""
        try:
            # Calculate credit cost
            credits_needed = self._calculate_credit_cost(feature, token_count)

            # Check if user has sufficient credits
            balance = self.credit_balances.get(user_id)
            if not balance:
                balance = await self.initialize_user_credits(user_id)

            if balance.available_credits < credits_needed:
                raise CreditInsufficientError(credits_needed, balance.available_credits)

            # Check spending limits
            await self._check_spending_limits(user_id, credits_needed)

            # Reserve credits for operation
            balance.available_credits -= credits_needed
            balance.reserved_credits += credits_needed

            # Create usage event
            event = CreditUsageEvent(
                user_id=user_id,
                feature=feature,
                credits_consumed=credits_needed,
                token_count=token_count,
                operation_id=operation_id,
                success=True
            )

            logger.info(f"Reserved {credits_needed} credits for user {user_id} feature {feature}")
            return event

        except Exception as e:
            logger.error(f"Credit consumption failed for user {user_id}: {str(e)}")
            # Create failed event
            event = CreditUsageEvent(
                user_id=user_id,
                feature=feature,
                credits_consumed=0,
                token_count=token_count,
                operation_id=operation_id,
                success=False
            )
            raise

    async def confirm_credit_consumption(
        self,
        user_id: str,
        operation_id: str,
        actual_token_count: int
    ) -> CreditTransaction:
        """Confirm credit consumption after successful operation"""
        try:
            balance = self.credit_balances[user_id]

            # Find the reserved amount (simplified - would track by operation_id)
            reserved_amount = balance.reserved_credits

            # Recalculate based on actual usage
            actual_cost = self._calculate_credit_cost_from_tokens(actual_token_count)

            # Adjust for actual vs reserved
            if actual_cost <= reserved_amount:
                # Use actual cost, return difference
                balance.reserved_credits = 0
                balance.total_credits -= actual_cost
                refund_amount = reserved_amount - actual_cost
                balance.available_credits += refund_amount
            else:
                # Actual cost higher than reserved (rare case)
                additional_needed = actual_cost - reserved_amount
                if balance.available_credits >= additional_needed:
                    balance.available_credits -= additional_needed
                    balance.reserved_credits = 0
                    balance.total_credits -= actual_cost
                else:
                    raise CreditInsufficientError(additional_needed, balance.available_credits)

            balance.last_updated = datetime.utcnow()

            # Record consumption transaction
            transaction = CreditTransaction(
                user_id=user_id,
                transaction_type=CreditTransactionType.CONSUMPTION,
                amount=actual_cost,
                description=f"AI feature usage: {actual_token_count} tokens",
                token_count=actual_token_count,
                cost_basis=actual_token_count * self.pricing.base_cost_per_1k_tokens / 1000,
                metadata={"operation_id": operation_id}
            )

            self.transactions.append(transaction)

            logger.info(f"Confirmed {actual_cost} credit consumption for user {user_id}")
            return transaction

        except Exception as e:
            logger.error(f"Failed to confirm credit consumption: {str(e)}")
            # Return reserved credits on failure
            balance = self.credit_balances.get(user_id)
            if balance:
                balance.available_credits += balance.reserved_credits
                balance.reserved_credits = 0
            raise

    async def get_user_credit_summary(self, user_id: str) -> UserCreditSummary:
        """Get comprehensive credit overview for user"""
        try:
            balance = self.credit_balances.get(user_id)
            if not balance:
                balance = await self.initialize_user_credits(user_id)

            # Get recent transactions
            user_transactions = [
                t for t in self.transactions
                if t.user_id == user_id
            ][-10:]  # Last 10 transactions

            # Calculate usage metrics
            now = datetime.utcnow()
            monthly_transactions = [
                t for t in user_transactions
                if t.timestamp > now - timedelta(days=30)
                and t.transaction_type == CreditTransactionType.CONSUMPTION
            ]
            daily_transactions = [
                t for t in monthly_transactions
                if t.timestamp > now - timedelta(days=1)
            ]

            monthly_usage = sum(t.amount for t in monthly_transactions)
            daily_usage = sum(t.amount for t in daily_transactions)

            # Get guardrails
            guardrails = self.guardrails.get(user_id, SpendGuardrail(user_id=user_id))

            # Estimate monthly spend
            if monthly_usage > 0:
                estimated_monthly = monthly_usage * 1.2  # 20% buffer
            else:
                estimated_monthly = 25.0  # Conservative estimate

            # Calculate savings vs pay-per-use
            savings = self._calculate_savings_vs_payperuse(user_transactions)

            return UserCreditSummary(
                user_id=user_id,
                current_balance=balance,
                recent_transactions=user_transactions,
                monthly_usage=monthly_usage,
                daily_usage=daily_usage,
                guardrails=guardrails,
                estimated_monthly_spend=estimated_monthly,
                savings_vs_pay_per_use=savings
            )

        except Exception as e:
            logger.error(f"Failed to get credit summary for user {user_id}: {str(e)}")
            raise

    async def get_monetization_metrics(self) -> CreditAttachmentMetrics:
        """Calculate B2C monetization KPIs"""
        try:
            total_users = len(self.credit_balances)

            # Users who purchased credits
            purchasers = set()
            total_revenue = 0.0

            for transaction in self.transactions:
                if transaction.transaction_type == CreditTransactionType.PURCHASE:
                    purchasers.add(transaction.user_id)
                    total_revenue += transaction.cost_basis or 0

            paying_users = len(purchasers)

            # Calculate metrics
            credit_attach_rate = paying_users / max(total_users, 1)
            pay_conversion_rate = paying_users / max(total_users, 1)
            arppu = total_revenue / max(paying_users, 1)

            # Calculate unit cost to serve (simplified)
            total_token_cost = sum(
                t.cost_basis or 0 for t in self.transactions
                if t.transaction_type == CreditTransactionType.CONSUMPTION
            )
            unit_cost_to_serve = total_token_cost / max(total_users, 1)

            return CreditAttachmentMetrics(
                credit_attach_rate=credit_attach_rate,
                pay_conversion_rate=pay_conversion_rate,
                arppu=arppu,
                unit_cost_to_serve=unit_cost_to_serve
            )

        except Exception as e:
            logger.error(f"Failed to calculate monetization metrics: {str(e)}")
            raise

    def _calculate_credit_cost(self, feature: str, token_count: int) -> float:
        """Calculate credit cost for feature usage"""
        # Base cost from feature mapping
        base_cost = FEATURE_CREDIT_COSTS.get(feature, 1.0)

        # Token-based adjustment
        token_cost = (token_count / 1000) * self.pricing.credit_per_1k_tokens

        # Use higher of base cost or token cost
        return max(base_cost, token_cost)

    def _calculate_credit_cost_from_tokens(self, token_count: int) -> float:
        """Calculate credit cost purely from token count"""
        return (token_count / 1000) * self.pricing.credit_per_1k_tokens

    async def _check_spending_limits(self, user_id: str, credits_needed: float):
        """Check if operation would exceed spending limits"""
        guardrails = self.guardrails.get(user_id)
        if not guardrails:
            return  # No limits set

        now = datetime.utcnow()

        # Check daily limit
        if guardrails.daily_limit:
            daily_usage = sum(
                t.amount for t in self.transactions
                if (t.user_id == user_id and
                    t.transaction_type == CreditTransactionType.CONSUMPTION and
                    t.timestamp > now - timedelta(days=1))
            )
            if daily_usage + credits_needed > guardrails.daily_limit:
                raise SpendLimitExceededError("Daily", guardrails.daily_limit, daily_usage)

        # Check monthly limit
        if guardrails.monthly_limit:
            monthly_usage = sum(
                t.amount for t in self.transactions
                if (t.user_id == user_id and
                    t.transaction_type == CreditTransactionType.CONSUMPTION and
                    t.timestamp > now - timedelta(days=30))
            )
            if monthly_usage + credits_needed > guardrails.monthly_limit:
                raise SpendLimitExceededError("Monthly", guardrails.monthly_limit, monthly_usage)

    async def _process_payment(
        self,
        user_id: str,
        amount_usd: float,
        payment_method_id: str
    ) -> bool:
        """Process payment via Stripe (stubbed for MVP)"""
        # In production, this would integrate with Stripe
        logger.info(f"Processing ${amount_usd} payment for user {user_id}")
        await asyncio.sleep(0.1)  # Simulate payment processing
        return True  # Assume success for MVP

    def _calculate_savings_vs_payperuse(self, transactions: list[CreditTransaction]) -> float:
        """Calculate user savings vs hypothetical pay-per-use pricing"""
        # This would calculate savings from credit packages vs individual pricing
        return 15.50  # Placeholder calculation
