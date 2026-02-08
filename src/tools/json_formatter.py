"""
JSON formatter tool for formatting and validating JSON data.

This tool provides JSON formatting and schema validation capabilities.
"""

import json
from typing import Optional, Dict, Any

from .base_tool import BaseTool
from models.data_models import ToolResult
from structured_logging import StructuredLogger


class JSONFormatterTool(BaseTool):
    """
    JSON formatter with schema validation.
    
    Features:
    - JSON formatting and pretty printing
    - Schema validation (basic)
    - Error detection and reporting
    - Minification option
    """
    
    def __init__(self, logger: Optional[StructuredLogger] = None):
        """
        Initialize JSON formatter.
        
        Args:
            logger: Structured logger for observability
        """
        super().__init__(logger)
    
    def validate_input(self, **kwargs) -> bool:
        """
        Validate JSON formatter input parameters.
        
        Args:
            data: Data to format (required)
            schema: Optional JSON schema for validation
            
        Returns:
            True if inputs are valid
        """
        if "data" not in kwargs:
            return False
        
        # Data can be any type (will be converted to JSON)
        
        if "schema" in kwargs:
            schema = kwargs["schema"]
            if not isinstance(schema, dict):
                return False
        
        return True
    
    def _validate_against_schema(
        self,
        data: Any,
        schema: Dict[str, Any]
    ) -> tuple[bool, Optional[str]]:
        """
        Basic schema validation.
        
        This is a simplified validation. For production, use jsonschema library.
        
        Args:
            data: Data to validate
            schema: JSON schema
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check type
        if "type" in schema:
            expected_type = schema["type"]
            
            type_map = {
                "object": dict,
                "array": list,
                "string": str,
                "number": (int, float),
                "integer": int,
                "boolean": bool,
                "null": type(None)
            }
            
            expected_python_type = type_map.get(expected_type)
            if expected_python_type and not isinstance(data, expected_python_type):
                return False, f"Expected type {expected_type}, got {type(data).__name__}"
        
        # Check required fields for objects
        if isinstance(data, dict) and "required" in schema:
            for field in schema["required"]:
                if field not in data:
                    return False, f"Required field missing: {field}"
        
        # Check properties for objects
        if isinstance(data, dict) and "properties" in schema:
            for key, value in data.items():
                if key in schema["properties"]:
                    prop_schema = schema["properties"][key]
                    is_valid, error = self._validate_against_schema(value, prop_schema)
                    if not is_valid:
                        return False, f"Property '{key}': {error}"
        
        # Check items for arrays
        if isinstance(data, list) and "items" in schema:
            item_schema = schema["items"]
            for i, item in enumerate(data):
                is_valid, error = self._validate_against_schema(item, item_schema)
                if not is_valid:
                    return False, f"Item {i}: {error}"
        
        return True, None
    
    def execute(
        self,
        data: Any,
        schema: Optional[Dict[str, Any]] = None,
        indent: int = 2,
        minify: bool = False
    ) -> ToolResult:
        """
        Format data as JSON and optionally validate against schema.
        
        Args:
            data: Data to format
            schema: Optional JSON schema for validation
            indent: Indentation spaces (default: 2)
            minify: Whether to minify JSON (default: False)
            
        Returns:
            ToolResult with formatted JSON string
        """
        try:
            # Validate against schema if provided
            if schema:
                is_valid, error_message = self._validate_against_schema(data, schema)
                if not is_valid:
                    return ToolResult(
                        success=False,
                        data=None,
                        error=f"Schema validation failed: {error_message}",
                        metadata={"validation_error": error_message}
                    )
            
            # Format JSON
            if minify:
                json_string = json.dumps(data, separators=(',', ':'))
            else:
                json_string = json.dumps(data, indent=indent, ensure_ascii=False)
            
            if self.logger:
                self.logger.log_info(
                    "JSON formatted successfully",
                    {
                        "size": len(json_string),
                        "minified": minify,
                        "validated": schema is not None
                    }
                )
            
            return ToolResult(
                success=True,
                data={
                    "json": json_string,
                    "size": len(json_string),
                    "minified": minify,
                    "validated": schema is not None
                },
                metadata={
                    "indent": indent if not minify else 0
                }
            )
        
        except TypeError as e:
            # Data is not JSON serializable
            return ToolResult(
                success=False,
                data=None,
                error=f"Data is not JSON serializable: {str(e)}",
                metadata={"data_type": type(data).__name__}
            )
        
        except Exception as e:
            return self.handle_error(e, context={"data_type": type(data).__name__})
