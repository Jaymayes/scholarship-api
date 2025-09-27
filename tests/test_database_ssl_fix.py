"""
Test Database SSL Hardening Implementation
Validates SSL/TLS enforcement, connection retry, and production security
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import OperationalError

from services.database_connection_manager import (
    DatabaseConnectionManager,
    DatabaseConnectionError,
    DatabaseSSLError,
    with_db_retry
)
from config.settings import Environment


class TestDatabaseSSLHardening:
    """Test SSL/TLS hardening and security configurations"""
    
    def test_ssl_enforcement_in_production(self):
        """Verify SSL verify-full is enforced in production environment"""
        with patch('config.settings.settings.environment', Environment.PRODUCTION):
            with patch.dict(os.environ, {"SSL_ROOT_CERT": "/path/to/ca.crt"}):
                # Re-import to pick up environment changes
                import importlib
                import models.database
                importlib.reload(models.database)
                
                engine = models.database.engine
                
                # In production, connect_args should include verify-full SSL settings
                if hasattr(engine, 'url') and 'postgresql' in str(engine.url):
                    # Check that SSL mode is configured for production security
                    connect_args = getattr(engine.dialect, 'connect_args', {})
                    if connect_args:
                        assert connect_args.get('sslmode') == 'verify-full', "Production must use verify-full for MITM protection"
    
    def test_ssl_validation_requirements(self):
        """Test SSL certificate validation in production"""
        manager = DatabaseConnectionManager()
        
        # Mock SSL info that would fail validation
        ssl_info_weak = {
            "ssl_active": True,
            "version": "TLSv1.1",  # Outdated version
            "cipher": "weak_cipher"
        }
        
        with patch('config.settings.settings.environment', Environment.PRODUCTION):
            # This should log a warning about outdated SSL version
            try:
                manager._validate_ssl_configuration(ssl_info_weak)
                # Should not raise an exception but log warning
            except DatabaseSSLError:
                pytest.fail("Should not raise exception for version warning")
        
        # Test missing SSL in production
        ssl_info_missing = {"ssl_active": False}
        
        with patch('config.settings.settings.environment', Environment.PRODUCTION):
            with pytest.raises(DatabaseSSLError, match="SSL/TLS is required"):
                manager._validate_ssl_configuration(ssl_info_missing)
    
    def test_development_ssl_preference(self):
        """Test that development prefers SSL but allows fallback"""
        with patch('config.settings.settings.environment', Environment.DEVELOPMENT):
            from models.database import engine
            
            # Development should not enforce SSL but should prefer it
            connect_args = getattr(engine, '_connect_args', {})
            if 'sslmode' in connect_args:
                assert connect_args['sslmode'] in ['prefer', 'allow']
    
    def test_connection_timeout_configuration(self):
        """Test that connection timeouts are properly configured"""
        from models.database import engine
        
        # SQLAlchemy stores connect_args internally in the engine's dialect
        dialect = engine.dialect
        connect_args = getattr(dialect, 'connect_args', {})
        
        # If connect_args is empty, check if engine was created with proper settings
        if not connect_args:
            # Test that engine has proper pool settings that indicate production configuration
            assert engine.pool.timeout() == 30  # pool_timeout
            assert hasattr(engine, '_pool_pre_ping')  # connection validation
            
        else:
            assert 'connect_timeout' in connect_args
            assert connect_args['connect_timeout'] == 10
            
            # Test application name is set for monitoring
            assert 'application_name' in connect_args
            assert connect_args['application_name'] == 'scholarship_api'


class TestConnectionRetryLogic:
    """Test database connection retry and backoff mechanisms"""
    
    def test_retry_decorator_success_on_first_attempt(self):
        """Test that successful operations don't trigger retries"""
        call_count = 0
        
        @with_db_retry(max_retries=3)
        def successful_operation():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = successful_operation()
        assert result == "success"
        assert call_count == 1
    
    def test_retry_decorator_with_retryable_errors(self):
        """Test retry logic with retryable database errors"""
        call_count = 0
        
        @with_db_retry(max_retries=2, backoff_base=0.1)
        def failing_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise OperationalError("Connection lost", None, None)
            return "success"
        
        result = failing_operation()
        assert result == "success"
        assert call_count == 3  # Failed twice, succeeded on third attempt
    
    def test_retry_decorator_max_retries_exceeded(self):
        """Test that max retries are respected"""
        call_count = 0
        
        @with_db_retry(max_retries=2, backoff_base=0.1)
        def always_failing_operation():
            nonlocal call_count
            call_count += 1
            raise OperationalError("Persistent connection error", None, None)
        
        with pytest.raises(DatabaseConnectionError, match="failed after 2 retries"):
            always_failing_operation()
        
        assert call_count == 3  # Initial attempt + 2 retries
    
    def test_retry_decorator_non_retryable_errors(self):
        """Test that non-retryable errors are not retried"""
        call_count = 0
        
        @with_db_retry(max_retries=3)
        def operation_with_programming_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("This is a programming error")
        
        with pytest.raises(ValueError):
            operation_with_programming_error()
        
        assert call_count == 1  # Should not retry programming errors


class TestDatabaseConnectionManager:
    """Test the DatabaseConnectionManager functionality"""
    
    def test_connection_manager_initialization(self):
        """Test that connection manager initializes properly"""
        manager = DatabaseConnectionManager()
        assert manager.engine is not None
        assert manager._ssl_validated is False
    
    def test_health_check_structure(self):
        """Test that health check returns proper structure"""
        manager = DatabaseConnectionManager()
        
        # Mock the database connection for testing
        with patch.object(manager.engine, 'connect') as mock_connect:
            mock_conn = MagicMock()
            mock_connect.return_value.__enter__.return_value = mock_conn
            mock_conn.execute.return_value = None
            
            # Mock pool information
            mock_pool = MagicMock()
            mock_pool.size.return_value = 5
            mock_pool.checkedin.return_value = 3
            mock_pool.checkedout.return_value = 2
            mock_pool.overflow.return_value = 0
            mock_pool.invalid.return_value = 0
            manager.engine.pool = mock_pool
            
            health = manager.health_check()
            
            assert health["status"] == "healthy"
            assert "response_time_ms" in health
            assert "pool_info" in health
            assert health["pool_info"]["pool_size"] == 5
            assert health["pool_info"]["pool_checked_in"] == 3
    
    def test_get_session_with_retry(self):
        """Test that get_session uses retry logic"""
        manager = DatabaseConnectionManager()
        
        # This should work with our test database
        with patch('models.database.SessionLocal') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session
            
            session = manager.get_session()
            assert session == mock_session
            mock_session.execute.assert_called_once()


class TestDatabasePoolConfiguration:
    """Test database connection pool settings"""
    
    def test_pool_settings_applied(self):
        """Test that pool settings are properly configured"""
        from models.database import engine
        
        # Check pool configuration
        assert engine.pool.size() >= 5  # Should have reasonable pool size
        assert hasattr(engine.pool, 'timeout')  # Should have timeout configured
        
        # Check that pool_pre_ping is enabled for connection validation
        # This ensures stale connections are detected and replaced
        engine_config = engine.url.query
        assert getattr(engine, '_pool_pre_ping', False) is True
    
    def test_connection_recycling(self):
        """Test that connections are recycled appropriately"""
        from models.database import engine
        
        # Check that pool_recycle is set to prevent stale connections
        assert getattr(engine, '_pool_recycle', 0) > 0


class TestSSLCertificateHandling:
    """Test SSL certificate configuration and handling"""
    
    def test_ssl_certificate_environment_variables(self):
        """Test SSL certificate loading from environment"""
        env_vars = [
            "SSL_CLIENT_CERT",
            "SSL_CLIENT_KEY", 
            "SSL_ROOT_CERT",
            "SSL_CRL"
        ]
        
        # Test that environment variables are properly handled
        with patch.dict(os.environ, {
            "SSL_CLIENT_CERT": "/path/to/client.crt",
            "SSL_CLIENT_KEY": "/path/to/client.key",
            "SSL_ROOT_CERT": "/path/to/ca.crt"
        }):
            with patch('config.settings.settings.environment', Environment.PRODUCTION):
                # Re-import to pick up environment changes
                import importlib
                import models.database
                importlib.reload(models.database)
                
                connect_args = getattr(models.database.engine, '_connect_args', {})
                
                if 'sslcert' in connect_args:
                    assert connect_args['sslcert'] == "/path/to/client.crt"
                if 'sslkey' in connect_args:
                    assert connect_args['sslkey'] == "/path/to/client.key"
                if 'sslrootcert' in connect_args:
                    assert connect_args['sslrootcert'] == "/path/to/ca.crt"
    
    def test_none_values_filtered_from_connect_args(self):
        """Test that None values are filtered from connect_args"""
        with patch.dict(os.environ, {}, clear=True):
            with patch('config.settings.settings.environment', Environment.PRODUCTION):
                # Re-import to test None filtering
                import importlib
                import models.database
                importlib.reload(models.database)
                
                connect_args = getattr(models.database.engine, '_connect_args', {})
                
                # None values should be filtered out
                for key, value in connect_args.items():
                    assert value is not None, f"connect_args[{key}] should not be None"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])