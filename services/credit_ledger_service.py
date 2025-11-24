"""
Credit Ledger Service
Implements transactional credit ledger operations with claim-first idempotency pattern
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

from models.database import CreditBalanceDB, CreditLedgerDB, IdempotencyKeyDB

logger = logging.getLogger(__name__)

class CreditLedgerService:
    """Service for managing credit ledger operations with idempotency"""
    
    def __init__(self):
        pass
    
    def credit_user(
        self,
        db: Session,
        user_id: str,
        amount: float,
        reason: Optional[str],
        idempotency_key: str,
        created_by_role: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Credit user account with idempotent transaction handling
        
        Returns:
            dict with keys: id, user_id, delta, balance, reason, created_at
        """
        if amount <= 0:
            raise HTTPException(status_code=422, detail="Amount must be greater than 0")
        
        # Check for existing idempotency key (claim-first pattern)
        existing_key = db.query(IdempotencyKeyDB).filter(
            IdempotencyKeyDB.key == idempotency_key
        ).first()
        
        if existing_key:
            if existing_key.status == "COMPLETED":
                # Return persisted result from ledger (idempotent replay)
                ledger_entry = db.query(CreditLedgerDB).filter(
                    CreditLedgerDB.id == existing_key.result_id
                ).first()
                
                # Defensive: Handle missing ledger row (e.g., admin cleanup)
                if not ledger_entry:
                    logger.error(f"Ledger row missing for completed idempotency key: {idempotency_key}")
                    raise HTTPException(
                        status_code=409,
                        detail="Transaction completed but ledger row missing. Contact support."
                    )
                
                return {
                    "id": ledger_entry.id,
                    "user_id": user_id,
                    "delta": ledger_entry.delta,
                    "balance": ledger_entry.balance_after,  # Use persisted balance
                    "reason": ledger_entry.reason,
                    "created_at": ledger_entry.created_at.isoformat()
                }
            elif existing_key.status == "PROCESSING":
                # Request is in-flight
                raise HTTPException(
                    status_code=409,
                    detail="Duplicate idempotency key in-flight",
                    headers={"Retry-After": "1"}
                )
        
        try:
            # Start transaction - claim the idempotency key
            idempotency_record = IdempotencyKeyDB(
                key=idempotency_key,
                status="PROCESSING",
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(hours=24)
            )
            db.add(idempotency_record)
            db.flush()  # Flush to catch duplicate key errors
            
            # Row-level lock balance (SELECT FOR UPDATE) - prevents race conditions
            balance = db.query(CreditBalanceDB).filter(
                CreditBalanceDB.user_id == user_id
            ).with_for_update().first()
            
            if balance:
                balance.balance += amount
                balance.updated_at = datetime.utcnow()
                balance_after = balance.balance
            else:
                # New user - create balance record
                balance = CreditBalanceDB(
                    user_id=user_id,
                    balance=amount,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(balance)
                db.flush()  # Get ID before using in ledger
                balance_after = amount
            
            # Create ledger entry with balance_after for idempotent replay
            ledger_entry = CreditLedgerDB(
                user_id=user_id,
                delta=amount,
                reason=reason,
                balance_after=balance_after,  # Store balance at this point in time
                transaction_metadata=metadata,
                created_by_role=created_by_role,
                created_at=datetime.utcnow()
            )
            db.add(ledger_entry)
            db.flush()  # Get the ID
            
            # Mark idempotency key as completed BEFORE commit
            idempotency_record.status = "COMPLETED"
            idempotency_record.result_id = ledger_entry.id
            db.flush()  # Ensure status update is part of this transaction
            
            # Commit transaction (now includes the status update)
            db.commit()
            
            # Refresh to get final state
            db.refresh(balance)
            
            logger.info(f"Credited {amount} to user {user_id}, new balance: {balance.balance}")
            
            return {
                "id": ledger_entry.id,
                "user_id": user_id,
                "delta": amount,
                "balance": balance.balance,
                "reason": reason,
                "created_at": ledger_entry.created_at.isoformat()
            }
            
        except IntegrityError as e:
            db.rollback()
            # Don't mutate existing keys - just raise the error
            # Concurrent requests will see existing COMPLETED/PROCESSING status
            logger.error(f"Integrity error during credit: {str(e)}")
            raise HTTPException(status_code=409, detail="Duplicate idempotency key collision")
        except Exception as e:
            db.rollback()
            logger.error(f"Error during credit: {str(e)}")
            raise
    
    def debit_user(
        self,
        db: Session,
        user_id: str,
        amount: float,
        purpose: str,
        idempotency_key: str,
        created_by_role: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Debit user account with idempotent transaction handling
        
        Returns:
            dict with keys: id, user_id, delta, balance, purpose, created_at
        """
        if amount <= 0:
            raise HTTPException(status_code=422, detail="Amount must be greater than 0")
        
        # Check for existing idempotency key (claim-first pattern)
        existing_key = db.query(IdempotencyKeyDB).filter(
            IdempotencyKeyDB.key == idempotency_key
        ).first()
        
        if existing_key:
            if existing_key.status == "COMPLETED":
                # Return persisted result from ledger (idempotent replay)
                ledger_entry = db.query(CreditLedgerDB).filter(
                    CreditLedgerDB.id == existing_key.result_id
                ).first()
                
                # Defensive: Handle missing ledger row (e.g., admin cleanup)
                if not ledger_entry:
                    logger.error(f"Ledger row missing for completed idempotency key: {idempotency_key}")
                    raise HTTPException(
                        status_code=409,
                        detail="Transaction completed but ledger row missing. Contact support."
                    )
                
                return {
                    "id": ledger_entry.id,
                    "user_id": user_id,
                    "delta": ledger_entry.delta,
                    "balance": ledger_entry.balance_after,  # Use persisted balance
                    "purpose": ledger_entry.purpose,
                    "created_at": ledger_entry.created_at.isoformat()
                }
            elif existing_key.status == "PROCESSING":
                # Request is in-flight
                raise HTTPException(
                    status_code=409,
                    detail="Duplicate idempotency key in-flight",
                    headers={"Retry-After": "1"}
                )
        
        try:
            # Start transaction - claim the idempotency key
            idempotency_record = IdempotencyKeyDB(
                key=idempotency_key,
                status="PROCESSING",
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(hours=24)
            )
            db.add(idempotency_record)
            db.flush()  # Flush to catch duplicate key errors
            
            # Row-level lock balance (SELECT FOR UPDATE) - prevents race conditions per master prompt
            balance = db.query(CreditBalanceDB).filter(
                CreditBalanceDB.user_id == user_id
            ).with_for_update().first()
            
            if not balance or balance.balance < amount:
                db.rollback()
                raise HTTPException(
                    status_code=409,
                    detail=f"Insufficient balance: requested {amount}, available {balance.balance if balance else 0}"
                )
            
            # Update balance atomically with ledger insert
            balance.balance -= amount
            balance.updated_at = datetime.utcnow()
            balance_after = balance.balance
            
            # Create ledger entry with balance_after for idempotent replay (negative delta for debit)
            ledger_entry = CreditLedgerDB(
                user_id=user_id,
                delta=-amount,
                purpose=purpose,
                balance_after=balance_after,  # Store balance at this point in time
                transaction_metadata=metadata,
                created_by_role=created_by_role,
                created_at=datetime.utcnow()
            )
            db.add(ledger_entry)
            db.flush()  # Get the ID
            
            # Mark idempotency key as completed BEFORE commit
            idempotency_record.status = "COMPLETED"
            idempotency_record.result_id = ledger_entry.id
            db.flush()  # Ensure status update is part of this transaction
            
            # Commit transaction (now includes the status update)
            db.commit()
            
            # Refresh to get final state
            db.refresh(balance)
            
            logger.info(f"Debited {amount} from user {user_id}, new balance: {balance.balance}")
            
            return {
                "id": ledger_entry.id,
                "user_id": user_id,
                "delta": -amount,
                "balance": balance.balance,
                "purpose": purpose,
                "created_at": ledger_entry.created_at.isoformat()
            }
            
        except IntegrityError as e:
            db.rollback()
            # Don't mutate existing keys - just raise the error
            # Concurrent requests will see existing COMPLETED/PROCESSING status
            logger.error(f"Integrity error during debit: {str(e)}")
            raise HTTPException(status_code=409, detail="Duplicate idempotency key collision")
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error during debit: {str(e)}")
            raise
    
    def get_balance(
        self,
        db: Session,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get user credit balance
        
        Returns:
            dict with keys: user_id, balance, updated_at
        """
        balance = db.query(CreditBalanceDB).filter(
            CreditBalanceDB.user_id == user_id
        ).first()
        
        if not balance:
            # User has no balance record yet, return 0
            return {
                "user_id": user_id,
                "balance": 0.0,
                "updated_at": datetime.utcnow().isoformat()
            }
        
        return {
            "user_id": user_id,
            "balance": balance.balance,
            "updated_at": balance.updated_at.isoformat()
        }

# Singleton instance
credit_ledger_service = CreditLedgerService()
