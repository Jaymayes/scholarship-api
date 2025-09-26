#!/usr/bin/env python3
"""
Fix database foreign key constraints by ensuring user_profiles table exists
and has the required test users
"""


from sqlalchemy import text

from models.database import engine


def fix_database_constraints():
    """Create necessary database tables and seed test data"""

    with engine.connect() as conn:
        try:
            # Create user_profiles table if it doesn't exist
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS user_profiles (
                    id VARCHAR(50) PRIMARY KEY,
                    gpa FLOAT,
                    grade_level VARCHAR(50),
                    field_of_study VARCHAR(100),
                    citizenship VARCHAR(50),
                    state_of_residence VARCHAR(50),
                    age INTEGER,
                    financial_need BOOLEAN,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))

            # Insert test admin user profile if it doesn't exist
            conn.execute(text("""
                INSERT INTO user_profiles (id, gpa, grade_level, field_of_study, citizenship, state_of_residence, age, financial_need)
                VALUES ('admin', 4.0, 'graduate', 'computer_science', 'US', 'CA', 25, false)
                ON CONFLICT (id) DO NOTHING
            """))

            # Insert a few more test user profiles
            test_users = [
                ('test_user_1', 3.5, 'undergraduate', 'engineering', 'US', 'NY', 20, True),
                ('test_user_2', 3.8, 'graduate', 'medicine', 'US', 'TX', 24, False),
                ('test_user_3', 3.2, 'undergraduate', 'business', 'US', 'FL', 21, True)
            ]

            for user_id, gpa, grade_level, field_of_study, citizenship, state, age, financial_need in test_users:
                conn.execute(text("""
                    INSERT INTO user_profiles (id, gpa, grade_level, field_of_study, citizenship, state_of_residence, age, financial_need)
                    VALUES (:id, :gpa, :grade_level, :field_of_study, :citizenship, :state, :age, :financial_need)
                    ON CONFLICT (id) DO NOTHING
                """), {
                    'id': user_id,
                    'gpa': gpa,
                    'grade_level': grade_level,
                    'field_of_study': field_of_study,
                    'citizenship': citizenship,
                    'state': state,
                    'age': age,
                    'financial_need': financial_need
                })

            conn.commit()
            print("✅ Database constraints fixed successfully!")
            print("✅ Test user profiles created")

        except Exception as e:
            print(f"❌ Error fixing database constraints: {e}")
            conn.rollback()

if __name__ == "__main__":
    fix_database_constraints()
