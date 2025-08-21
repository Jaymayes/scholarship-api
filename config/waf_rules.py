"""
WAF Rules Configuration

Defines production-ready WAF rules for blocking common attacks:
- SQL injection patterns  
- XSS payloads
- Command injection attempts
- Authorization enforcement
- Rate limiting integration

These rules implement OWASP security guidelines and provide
comprehensive edge-level protection.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import re

class RuleAction(str, Enum):
    BLOCK = "block"
    LOG = "log" 
    RATE_LIMIT = "rate_limit"

class RuleSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class WAFRule:
    """WAF rule definition"""
    id: str
    name: str
    description: str
    pattern: str
    action: RuleAction
    severity: RuleSeverity
    enabled: bool = True
    rate_limit_window: int = 3600  # seconds
    rate_limit_max: int = 5

class WAFRulesConfig:
    """
    Production WAF rules configuration
    
    Implements OWASP security controls with specific focus on:
    - SQL injection prevention
    - Authorization enforcement 
    - Attack pattern detection
    - Rate limiting for malicious traffic
    """
    
    def __init__(self):
        self.rules = self._initialize_rules()
        
    def _initialize_rules(self) -> Dict[str, WAFRule]:
        """Initialize production WAF rules"""
        
        rules = {}
        
        # SQL INJECTION RULES (CRITICAL)
        rules["SQLI_001"] = WAFRule(
            id="SQLI_001",
            name="SQL Injection - Union Select",
            description="Detects UNION SELECT injection attempts",
            pattern=r"\b(union\s+(all\s+)?select)\b",
            action=RuleAction.BLOCK,
            severity=RuleSeverity.CRITICAL
        )
        
        rules["SQLI_002"] = WAFRule(
            id="SQLI_002", 
            name="SQL Injection - Boolean Logic",
            description="Detects OR/AND boolean logic injection",
            pattern=r"\b(or|and)\s+['\"]?\w+['\"]?\s*=\s*['\"]?\w+['\"]?",
            action=RuleAction.BLOCK,
            severity=RuleSeverity.CRITICAL
        )
        
        rules["SQLI_003"] = WAFRule(
            id="SQLI_003",
            name="SQL Injection - Comments", 
            description="Detects SQL comment injection (--,#,/**/)",
            pattern=r"(--|\#|\/\*|\*\/)",
            action=RuleAction.BLOCK,
            severity=RuleSeverity.HIGH
        )
        
        rules["SQLI_004"] = WAFRule(
            id="SQLI_004",
            name="SQL Injection - Information Schema",
            description="Detects information_schema attacks",
            pattern=r"\b(information_schema|sys\.|mysql\.|pg_)\w*",
            action=RuleAction.BLOCK,
            severity=RuleSeverity.CRITICAL
        )
        
        rules["SQLI_005"] = WAFRule(
            id="SQLI_005",
            name="SQL Injection - Time-based",
            description="Detects time-based blind SQL injection",
            pattern=r"\b(waitfor|delay|benchmark|sleep)\s*\(",
            action=RuleAction.BLOCK,
            severity=RuleSeverity.HIGH
        )
        
        # AUTHORIZATION ENFORCEMENT RULES (CRITICAL)
        rules["AUTH_001"] = WAFRule(
            id="AUTH_001",
            name="Missing Authorization Header",
            description="Requires Bearer token on protected endpoints",
            pattern=r"^/api/v1/(?!health|metrics)",
            action=RuleAction.BLOCK,
            severity=RuleSeverity.CRITICAL
        )
        
        rules["AUTH_002"] = WAFRule(
            id="AUTH_002",
            name="Malformed Authorization Header", 
            description="Validates Bearer token format",
            pattern=r"^Bearer\s+[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+$",
            action=RuleAction.BLOCK,
            severity=RuleSeverity.HIGH
        )
        
        # XSS PREVENTION RULES (HIGH)
        rules["XSS_001"] = WAFRule(
            id="XSS_001", 
            name="XSS - Script Tags",
            description="Detects script tag injection",
            pattern=r"<\s*script\b[^<]*(?:(?!<\/\s*script\s*>)<[^<]*)*<\/\s*script\s*>",
            action=RuleAction.BLOCK,
            severity=RuleSeverity.HIGH
        )
        
        rules["XSS_002"] = WAFRule(
            id="XSS_002",
            name="XSS - JavaScript Protocol",
            description="Detects javascript: protocol injection", 
            pattern=r"javascript\s*:",
            action=RuleAction.BLOCK,
            severity=RuleSeverity.HIGH
        )
        
        rules["XSS_003"] = WAFRule(
            id="XSS_003",
            name="XSS - Event Handlers",
            description="Detects HTML event handler injection",
            pattern=r"on\w+\s*=",
            action=RuleAction.BLOCK,
            severity=RuleSeverity.MEDIUM
        )
        
        # COMMAND INJECTION RULES (HIGH)
        rules["CMD_001"] = WAFRule(
            id="CMD_001",
            name="Command Injection - System Commands",
            description="Detects system command injection attempts",
            pattern=r"\b(wget|curl|nc|netcat|telnet|ssh|ftp|cat|ls|pwd)\b",
            action=RuleAction.BLOCK,
            severity=RuleSeverity.HIGH
        )
        
        rules["CMD_002"] = WAFRule(
            id="CMD_002",
            name="Command Injection - Shell Operators",
            description="Detects shell command chaining",
            pattern=r"(\|(pipe)|;|&&|\|\||\$\(|\`)",
            action=RuleAction.BLOCK,
            severity=RuleSeverity.HIGH
        )
        
        # PATH TRAVERSAL RULES (MEDIUM)
        rules["PATH_001"] = WAFRule(
            id="PATH_001",
            name="Path Traversal - Directory Traversal",
            description="Detects directory traversal attempts",
            pattern=r"(\.\./|\.\.\\)",
            action=RuleAction.BLOCK,
            severity=RuleSeverity.MEDIUM
        )
        
        rules["PATH_002"] = WAFRule(
            id="PATH_002", 
            name="Path Traversal - URL Encoded",
            description="Detects URL-encoded path traversal",
            pattern=r"(\%2e\%2e\%2f|\%2e\%2e\%5c|\%252e\%252e\%252f)",
            action=RuleAction.BLOCK,
            severity=RuleSeverity.MEDIUM
        )
        
        # RATE LIMITING RULES
        rules["RATE_001"] = WAFRule(
            id="RATE_001",
            name="API Rate Limiting",
            description="General API rate limiting",
            pattern=r"^/api/",
            action=RuleAction.RATE_LIMIT,
            severity=RuleSeverity.LOW,
            rate_limit_window=60,
            rate_limit_max=100
        )
        
        rules["RATE_002"] = WAFRule(
            id="RATE_002",
            name="Search Rate Limiting",
            description="Search endpoint specific rate limiting", 
            pattern=r"^/api/v1/(search|scholarships)",
            action=RuleAction.RATE_LIMIT,
            severity=RuleSeverity.LOW,
            rate_limit_window=60,
            rate_limit_max=30
        )
        
        return rules
    
    def get_active_rules(self) -> Dict[str, WAFRule]:
        """Get only enabled rules"""
        return {k: v for k, v in self.rules.items() if v.enabled}
    
    def get_rules_by_severity(self, severity: RuleSeverity) -> Dict[str, WAFRule]:
        """Get rules by severity level"""
        return {k: v for k, v in self.rules.items() if v.severity == severity and v.enabled}
    
    def get_blocking_rules(self) -> Dict[str, WAFRule]:
        """Get rules that block requests"""
        return {k: v for k, v in self.rules.items() if v.action == RuleAction.BLOCK and v.enabled}
    
    def enable_rule(self, rule_id: str) -> bool:
        """Enable a specific rule"""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = True
            return True
        return False
    
    def disable_rule(self, rule_id: str) -> bool:
        """Disable a specific rule"""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = False
            return True
        return False
    
    def get_rule_stats(self) -> Dict[str, Any]:
        """Get WAF rules statistics"""
        total_rules = len(self.rules)
        enabled_rules = len(self.get_active_rules())
        critical_rules = len(self.get_rules_by_severity(RuleSeverity.CRITICAL))
        blocking_rules = len(self.get_blocking_rules())
        
        return {
            "total_rules": total_rules,
            "enabled_rules": enabled_rules,
            "critical_rules": critical_rules,
            "blocking_rules": blocking_rules,
            "rules_by_severity": {
                "critical": len(self.get_rules_by_severity(RuleSeverity.CRITICAL)),
                "high": len(self.get_rules_by_severity(RuleSeverity.HIGH)),
                "medium": len(self.get_rules_by_severity(RuleSeverity.MEDIUM)),
                "low": len(self.get_rules_by_severity(RuleSeverity.LOW))
            }
        }

# Global WAF rules configuration
waf_rules = WAFRulesConfig()