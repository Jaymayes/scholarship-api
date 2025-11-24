"""
Migration: Add Credit Ledger Tables
Creates tables for credit_balances, credit_ledger, and idempotency_keys

Run this migration with: python -m migrations.add_credit_ledger_tables
"""

import logging
from models.database import engine, CreditBalanceDB, CreditLedgerDB, IdempotencyKeyDB, Base
from sqlalchemy import inspect

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Create credit ledger tables if they don't exist"""
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    tables_to_create = []
    
    # Check which tables need to be created
    if "credit_balances" not in existing_tables:
        tables_to_create.append("credit_balances")
    
    if "credit_ledger" not in existing_tables:
        tables_to_create.append("credit_ledger")
    
    if "idempotency_keys" not in existing_tables:
        tables_to_create.append("idempotency_keys")
    
    if not tables_to_create:
        logger.info("✅ All credit ledger tables already exist")
        return
    
    logger.info(f"Creating tables: {', '.join(tables_to_create)}")
    
    # Create only the credit ledger tables
    for table in [CreditBalanceDB.__table__, CreditLedgerDB.__table__, IdempotencyKeyDB.__table__]:
        if table.name in tables_to_create:
            logger.info(f"Creating table: {table.name}")
            table.create(engine, checkfirst=True)
    
    logger.info("✅ Credit ledger migration completed successfully")

if __name__ == "__main__":
    run_migration()
