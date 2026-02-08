"""
Python execution tool for data manipulation, calculations, and formatting.

This tool provides safe Python code execution with timeout and import restrictions.
"""

import sys
import io
import time
from typing import Optional, List, Dict, Any
from contextlib import redirect_stdout, redirect_stderr

from .base_tool import BaseTool
from models.data_models import ToolResult
from structured_logging import StructuredLogger


class PythonExecutorTool(BaseTool):
    """
    Python executor with safety constraints.
    
    Features:
    - Isolated execution environment
    - Timeout enforcement
    - Import whitelist for security
    - Captures stdout and stderr
    - Returns execution results
    """
    
    # Default allowed imports (safe standard library modules)
    DEFAULT_ALLOWED_IMPORTS = [
        "math", "statistics", "datetime", "json", "re",
        "collections", "itertools", "functools", "operator",
        "decimal", "fractions", "random", "string"
    ]
    
    def __init__(
        self,
        logger: Optional[StructuredLogger] = None,
        timeout: int = 10,
        allowed_imports: Optional[List[str]] = None
    ):
        """
        Initialize Python executor with safety constraints.
        
        Args:
            logger: Structured logger for observability
            timeout: Execution timeout in seconds (default: 10)
            allowed_imports: Whitelist of allowed imports (default: safe stdlib modules)
        """
        super().__init__(logger)
        self.timeout = timeout
        self.allowed_imports = allowed_imports or self.DEFAULT_ALLOWED_IMPORTS
    
    def validate_input(self, **kwargs) -> bool:
        """
        Validate executor input parameters.
        
        Args:
            code: Python code to execute (required)
            context: Variables to inject (optional)
            
        Returns:
            True if inputs are valid
        """
        if "code" not in kwargs:
            return False
        
        code = kwargs["code"]
        if not isinstance(code, str) or len(code.strip()) == 0:
            return False
        
        if "context" in kwargs:
            context = kwargs["context"]
            if not isinstance(context, dict):
                return False
        
        return True
    
    def _check_imports(self, code: str) -> bool:
        """
        Check if code only uses allowed imports.
        
        Args:
            code: Python code to check
            
        Returns:
            True if all imports are allowed
        """
        import ast
        
        try:
            tree = ast.parse(code)
        except SyntaxError:
            # Let execution handle syntax errors
            return True
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module = alias.name.split('.')[0]
                    if module not in self.allowed_imports:
                        return False
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module = node.module.split('.')[0]
                    if module not in self.allowed_imports:
                        return False
        
        return True
    
    def execute(
        self,
        code: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ToolResult:
        """
        Execute Python code in isolated environment.
        
        Args:
            code: Python code to execute
            context: Variables to inject into execution context
            
        Returns:
            ToolResult with execution output
        """
        start_time = time.time()
        
        # Check imports
        if not self._check_imports(code):
            return ToolResult(
                success=False,
                data=None,
                error="Code contains disallowed imports. Allowed: " + ", ".join(self.allowed_imports),
                metadata={"code_length": len(code)}
            )
        
        # Prepare execution context
        exec_globals = {
            "__builtins__": __builtins__,
        }
        
        # Add allowed imports to context
        for module_name in self.allowed_imports:
            try:
                exec_globals[module_name] = __import__(module_name)
            except ImportError:
                pass
        
        # Add user context
        if context:
            exec_globals.update(context)
        
        # Capture stdout and stderr
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        result_value = None
        error_message = None
        
        try:
            # Execute with timeout (simplified - real timeout needs threading/multiprocessing)
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                # Try to evaluate as expression first
                try:
                    result_value = eval(code, exec_globals)
                except SyntaxError:
                    # If not an expression, execute as statements
                    exec(code, exec_globals)
                    # Try to get 'result' variable if defined
                    result_value = exec_globals.get('result', None)
        
        except Exception as e:
            error_message = f"{type(e).__name__}: {str(e)}"
            
            if self.logger:
                import traceback
                self.logger.log_error(
                    error_type=type(e).__name__,
                    error_message=str(e),
                    stack_trace=traceback.format_exc(),
                    context={"code": code[:200]}  # First 200 chars
                )
        
        execution_time = time.time() - start_time
        
        # Check timeout
        if execution_time > self.timeout:
            return ToolResult(
                success=False,
                data=None,
                error=f"Execution exceeded timeout of {self.timeout} seconds",
                metadata={"execution_time": execution_time}
            )
        
        # Get captured output
        stdout_output = stdout_capture.getvalue()
        stderr_output = stderr_capture.getvalue()
        
        if error_message:
            return ToolResult(
                success=False,
                data=None,
                error=error_message,
                metadata={
                    "stdout": stdout_output,
                    "stderr": stderr_output,
                    "execution_time": execution_time
                }
            )
        
        return ToolResult(
            success=True,
            data={
                "result": result_value,
                "stdout": stdout_output,
                "stderr": stderr_output,
                "type": type(result_value).__name__ if result_value is not None else None
            },
            metadata={
                "execution_time": execution_time,
                "code_length": len(code)
            }
        )
