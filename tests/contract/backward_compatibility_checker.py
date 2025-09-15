"""
Priority 2 Day 1: Backward Compatibility Checker
Compares current OpenAPI spec to last release and flags breaking changes
CI Gate: Fail on mismatch or unapproved breaking changes
"""

import json
import sys
from typing import Dict, Any, List, Tuple, Set
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

class ChangeType(Enum):
    BREAKING = "breaking"
    NON_BREAKING = "non-breaking"
    ADDITION = "addition"

@dataclass
class APIChange:
    change_type: ChangeType
    category: str
    path: str
    method: str
    description: str
    severity: str  # "critical", "major", "minor"
    details: Dict[str, Any]

class BackwardCompatibilityChecker:
    """Analyzes OpenAPI specs for breaking changes"""
    
    def __init__(self, current_spec_path: str, previous_spec_path: str):
        self.current_spec = self._load_spec(current_spec_path)
        self.previous_spec = self._load_spec(previous_spec_path)
        self.changes: List[APIChange] = []
        
    def _load_spec(self, spec_path: str) -> Dict[str, Any]:
        """Load OpenAPI specification from JSON file"""
        try:
            with open(spec_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: Spec file {spec_path} not found, treating as empty spec")
            return {"paths": {}, "components": {"schemas": {}}}
        except json.JSONDecodeError as e:
            print(f"Error parsing {spec_path}: {e}")
            sys.exit(1)
    
    def analyze_changes(self) -> List[APIChange]:
        """Perform comprehensive backward compatibility analysis"""
        self.changes = []
        
        # Analyze API version changes
        self._check_version_changes()
        
        # Analyze endpoint changes
        self._check_endpoint_changes()
        
        # Analyze schema changes
        self._check_schema_changes()
        
        # Analyze security changes
        self._check_security_changes()
        
        return self.changes
    
    def _check_version_changes(self):
        """Check for API version changes"""
        current_version = self.current_spec.get("info", {}).get("version")
        previous_version = self.previous_spec.get("info", {}).get("version")
        
        if current_version != previous_version:
            # Semantic version analysis
            change_type = self._analyze_version_change(previous_version, current_version)
            self.changes.append(APIChange(
                change_type=change_type,
                category="version",
                path="/info/version",
                method="",
                description=f"API version changed from {previous_version} to {current_version}",
                severity="major" if change_type == ChangeType.BREAKING else "minor",
                details={"old_version": previous_version, "new_version": current_version}
            ))
    
    def _analyze_version_change(self, old_version: str, new_version: str) -> ChangeType:
        """Analyze semantic version changes"""
        if not old_version or not new_version:
            return ChangeType.NON_BREAKING
            
        try:
            old_parts = [int(x) for x in old_version.split('.')]
            new_parts = [int(x) for x in new_version.split('.')]
            
            # Pad versions to same length
            max_len = max(len(old_parts), len(new_parts))
            old_parts.extend([0] * (max_len - len(old_parts)))
            new_parts.extend([0] * (max_len - len(new_parts)))
            
            # Major version change is potentially breaking
            if new_parts[0] > old_parts[0]:
                return ChangeType.BREAKING
            elif new_parts[1] > old_parts[1] or new_parts[2] > old_parts[2]:
                return ChangeType.NON_BREAKING
            else:
                return ChangeType.NON_BREAKING
                
        except (ValueError, IndexError):
            return ChangeType.NON_BREAKING
    
    def _check_endpoint_changes(self):
        """Check for endpoint-level changes"""
        current_paths = self.current_spec.get("paths", {})
        previous_paths = self.previous_spec.get("paths", {})
        
        # Check for removed endpoints (BREAKING)
        for path in previous_paths:
            if path not in current_paths:
                # Endpoint completely removed
                for method in previous_paths[path]:
                    if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                        self.changes.append(APIChange(
                            change_type=ChangeType.BREAKING,
                            category="endpoint_removed",
                            path=path,
                            method=method.upper(),
                            description=f"Endpoint {method.upper()} {path} was removed",
                            severity="critical",
                            details={"removed_endpoint": f"{method.upper()} {path}"}
                        ))
        
        # Check for method removals and modifications
        for path in current_paths:
            if path in previous_paths:
                self._check_method_changes(path, previous_paths[path], current_paths[path])
        
        # Check for new endpoints (ADDITION)
        for path in current_paths:
            if path not in previous_paths:
                for method in current_paths[path]:
                    if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                        self.changes.append(APIChange(
                            change_type=ChangeType.ADDITION,
                            category="endpoint_added",
                            path=path,
                            method=method.upper(),
                            description=f"New endpoint {method.upper()} {path} added",
                            severity="minor",
                            details={"new_endpoint": f"{method.upper()} {path}"}
                        ))
    
    def _check_method_changes(self, path: str, previous_methods: Dict, current_methods: Dict):
        """Check for changes within a specific path"""
        
        # Check for removed methods (BREAKING)
        for method in previous_methods:
            if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                if method not in current_methods:
                    self.changes.append(APIChange(
                        change_type=ChangeType.BREAKING,
                        category="method_removed",
                        path=path,
                        method=method.upper(),
                        description=f"Method {method.upper()} removed from {path}",
                        severity="critical",
                        details={"removed_method": method.upper()}
                    ))
        
        # Check for method modifications
        for method in current_methods:
            if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'] and method in previous_methods:
                self._check_operation_changes(path, method, previous_methods[method], current_methods[method])
    
    def _check_operation_changes(self, path: str, method: str, previous_op: Dict, current_op: Dict):
        """Check for changes within a specific operation"""
        
        # Check parameter changes
        self._check_parameter_changes(path, method, previous_op, current_op)
        
        # Check request body changes
        self._check_request_body_changes(path, method, previous_op, current_op)
        
        # Check response changes
        self._check_response_changes(path, method, previous_op, current_op)
    
    def _check_parameter_changes(self, path: str, method: str, previous_op: Dict, current_op: Dict):
        """Check for parameter changes"""
        previous_params = {p.get("name"): p for p in previous_op.get("parameters", [])}
        current_params = {p.get("name"): p for p in current_op.get("parameters", [])}
        
        # Check for removed required parameters (BREAKING)
        for param_name, param_info in previous_params.items():
            if param_name not in current_params and param_info.get("required", False):
                self.changes.append(APIChange(
                    change_type=ChangeType.BREAKING,
                    category="required_parameter_removed",
                    path=path,
                    method=method.upper(),
                    description=f"Required parameter '{param_name}' removed from {method.upper()} {path}",
                    severity="critical",
                    details={"removed_parameter": param_name, "was_required": True}
                ))
        
        # Check for new required parameters (BREAKING)
        for param_name, param_info in current_params.items():
            if param_name not in previous_params and param_info.get("required", False):
                self.changes.append(APIChange(
                    change_type=ChangeType.BREAKING,
                    category="required_parameter_added",
                    path=path,
                    method=method.upper(),
                    description=f"New required parameter '{param_name}' added to {method.upper()} {path}",
                    severity="major",
                    details={"new_parameter": param_name, "is_required": True}
                ))
        
        # Check for parameter type changes
        for param_name in set(previous_params.keys()) & set(current_params.keys()):
            prev_type = previous_params[param_name].get("schema", {}).get("type")
            curr_type = current_params[param_name].get("schema", {}).get("type")
            
            if prev_type != curr_type and prev_type and curr_type:
                self.changes.append(APIChange(
                    change_type=ChangeType.BREAKING,
                    category="parameter_type_changed",
                    path=path,
                    method=method.upper(),
                    description=f"Parameter '{param_name}' type changed from {prev_type} to {curr_type}",
                    severity="major",
                    details={"parameter": param_name, "old_type": prev_type, "new_type": curr_type}
                ))
    
    def _check_request_body_changes(self, path: str, method: str, previous_op: Dict, current_op: Dict):
        """Check for request body changes"""
        previous_body = previous_op.get("requestBody", {})
        current_body = current_op.get("requestBody", {})
        
        # Request body added (could be breaking for some methods)
        if not previous_body and current_body:
            severity = "major" if method.upper() in ['GET', 'DELETE'] else "minor"
            self.changes.append(APIChange(
                change_type=ChangeType.BREAKING if severity == "major" else ChangeType.NON_BREAKING,
                category="request_body_added",
                path=path,
                method=method.upper(),
                description=f"Request body added to {method.upper()} {path}",
                severity=severity,
                details={"body_added": True}
            ))
        
        # Request body removed (usually breaking)
        if previous_body and not current_body:
            self.changes.append(APIChange(
                change_type=ChangeType.BREAKING,
                category="request_body_removed",
                path=path,
                method=method.upper(),
                description=f"Request body removed from {method.upper()} {path}",
                severity="major",
                details={"body_removed": True}
            ))
    
    def _check_response_changes(self, path: str, method: str, previous_op: Dict, current_op: Dict):
        """Check for response changes"""
        previous_responses = previous_op.get("responses", {})
        current_responses = current_op.get("responses", {})
        
        # Check for removed success responses (BREAKING)
        success_codes = ["200", "201", "204"]
        for code in success_codes:
            if code in previous_responses and code not in current_responses:
                self.changes.append(APIChange(
                    change_type=ChangeType.BREAKING,
                    category="success_response_removed",
                    path=path,
                    method=method.upper(),
                    description=f"Success response {code} removed from {method.upper()} {path}",
                    severity="critical",
                    details={"removed_response_code": code}
                ))
        
        # Check for new error responses (NON-BREAKING, informational)
        error_codes = ["400", "401", "403", "404", "429", "500"]
        for code in error_codes:
            if code not in previous_responses and code in current_responses:
                self.changes.append(APIChange(
                    change_type=ChangeType.NON_BREAKING,
                    category="error_response_added",
                    path=path,
                    method=method.upper(),
                    description=f"New error response {code} added to {method.upper()} {path}",
                    severity="minor",
                    details={"new_error_code": code}
                ))
    
    def _check_schema_changes(self):
        """Check for schema/model changes"""
        current_schemas = self.current_spec.get("components", {}).get("schemas", {})
        previous_schemas = self.previous_spec.get("components", {}).get("schemas", {})
        
        # Check for removed schemas (potentially breaking)
        for schema_name in previous_schemas:
            if schema_name not in current_schemas:
                self.changes.append(APIChange(
                    change_type=ChangeType.BREAKING,
                    category="schema_removed",
                    path=f"/components/schemas/{schema_name}",
                    method="",
                    description=f"Schema '{schema_name}' was removed",
                    severity="major",
                    details={"removed_schema": schema_name}
                ))
        
        # Check for schema property changes
        for schema_name in set(previous_schemas.keys()) & set(current_schemas.keys()):
            self._check_schema_property_changes(schema_name, previous_schemas[schema_name], current_schemas[schema_name])
    
    def _check_schema_property_changes(self, schema_name: str, previous_schema: Dict, current_schema: Dict):
        """Check for property changes within a schema"""
        previous_props = previous_schema.get("properties", {})
        current_props = current_schema.get("properties", {})
        previous_required = set(previous_schema.get("required", []))
        current_required = set(current_schema.get("required", []))
        
        # Check for removed required properties (BREAKING)
        for prop_name in previous_props:
            if prop_name not in current_props and prop_name in previous_required:
                self.changes.append(APIChange(
                    change_type=ChangeType.BREAKING,
                    category="required_property_removed",
                    path=f"/components/schemas/{schema_name}",
                    method="",
                    description=f"Required property '{prop_name}' removed from schema '{schema_name}'",
                    severity="critical",
                    details={"schema": schema_name, "removed_property": prop_name, "was_required": True}
                ))
        
        # Check for new required properties (BREAKING)
        for prop_name in current_required - previous_required:
            if prop_name in previous_props:  # Property existed but wasn't required
                self.changes.append(APIChange(
                    change_type=ChangeType.BREAKING,
                    category="property_made_required",
                    path=f"/components/schemas/{schema_name}",
                    method="",
                    description=f"Property '{prop_name}' made required in schema '{schema_name}'",
                    severity="major",
                    details={"schema": schema_name, "property": prop_name, "made_required": True}
                ))
    
    def _check_security_changes(self):
        """Check for security requirement changes"""
        current_security = self.current_spec.get("security", [])
        previous_security = self.previous_spec.get("security", [])
        
        if current_security != previous_security:
            # Security requirements changed - potentially breaking
            self.changes.append(APIChange(
                change_type=ChangeType.BREAKING,
                category="security_requirements_changed",
                path="/security",
                method="",
                description="Global security requirements changed",
                severity="major",
                details={"previous_security": previous_security, "current_security": current_security}
            ))
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive compatibility report"""
        breaking_changes = [c for c in self.changes if c.change_type == ChangeType.BREAKING]
        non_breaking_changes = [c for c in self.changes if c.change_type == ChangeType.NON_BREAKING]
        additions = [c for c in self.changes if c.change_type == ChangeType.ADDITION]
        
        severity_counts = {}
        for change in self.changes:
            severity_counts[change.severity] = severity_counts.get(change.severity, 0) + 1
        
        return {
            "compatible": len(breaking_changes) == 0,
            "total_changes": len(self.changes),
            "breaking_changes": len(breaking_changes),
            "non_breaking_changes": len(non_breaking_changes),
            "additions": len(additions),
            "severity_counts": severity_counts,
            "changes": [
                {
                    "type": change.change_type.value,
                    "category": change.category,
                    "path": change.path,
                    "method": change.method,
                    "description": change.description,
                    "severity": change.severity,
                    "details": change.details
                }
                for change in self.changes
            ]
        }
    
    def check_compatibility(self) -> Tuple[bool, List[str]]:
        """Check if changes are backward compatible"""
        self.analyze_changes()
        
        breaking_changes = [c for c in self.changes if c.change_type == ChangeType.BREAKING]
        
        if not breaking_changes:
            return True, []
        
        error_messages = []
        for change in breaking_changes:
            error_messages.append(f"BREAKING: {change.description} [{change.severity}]")
        
        return False, error_messages

def main():
    """CLI interface for backward compatibility checking"""
    if len(sys.argv) < 3:
        print("Usage: python backward_compatibility_checker.py <current_spec.json> <previous_spec.json>")
        sys.exit(1)
    
    current_spec_path = sys.argv[1]
    previous_spec_path = sys.argv[2]
    
    checker = BackwardCompatibilityChecker(current_spec_path, previous_spec_path)
    is_compatible, errors = checker.check_compatibility()
    
    # Generate detailed report
    report = checker.generate_report()
    
    # Save report
    output_path = "tests/contract/compatibility_report.json"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Print results
    print(f"🔍 Backward Compatibility Analysis Complete")
    print(f"📊 Total Changes: {report['total_changes']}")
    print(f"✅ Compatible: {report['compatible']}")
    
    if report['breaking_changes'] > 0:
        print(f"❌ Breaking Changes: {report['breaking_changes']}")
        print("🚨 BREAKING CHANGES DETECTED:")
        for error in errors:
            print(f"   • {error}")
    
    if report['additions'] > 0:
        print(f"➕ New Features: {report['additions']}")
    
    if report['non_breaking_changes'] > 0:
        print(f"🔄 Non-Breaking Changes: {report['non_breaking_changes']}")
    
    print(f"📄 Detailed report saved to: {output_path}")
    
    # Exit with error code if breaking changes detected
    sys.exit(0 if is_compatible else 1)

if __name__ == "__main__":
    main()