"""
File writer tool for saving reports, logs, and structured outputs.

This tool provides file writing capabilities with support for multiple formats.
"""

import os
import json
from pathlib import Path
from typing import Optional

from .base_tool import BaseTool
from models.data_models import ToolResult
from structured_logging import StructuredLogger


class FileWriterTool(BaseTool):
    """
    File writer with multiple format support.
    
    Features:
    - Multiple output formats (txt, json, md)
    - Automatic directory creation
    - Safe file path validation
    - Overwrite protection option
    """
    
    def __init__(
        self,
        logger: Optional[StructuredLogger] = None,
        output_dir: str = "./outputs"
    ):
        """
        Initialize file writer with output directory.
        
        Args:
            logger: Structured logger for observability
            output_dir: Base directory for output files (default: ./outputs)
        """
        super().__init__(logger)
        self.output_dir = Path(output_dir)
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def validate_input(self, **kwargs) -> bool:
        """
        Validate file writer input parameters.
        
        Args:
            filename: Output filename (required)
            content: Content to write (required)
            format: File format (optional, default: txt)
            
        Returns:
            True if inputs are valid
        """
        if "filename" not in kwargs or "content" not in kwargs:
            return False
        
        filename = kwargs["filename"]
        if not isinstance(filename, str) or len(filename.strip()) == 0:
            return False
        
        # Check for path traversal attempts
        if ".." in filename or filename.startswith("/") or filename.startswith("\\"):
            return False
        
        content = kwargs["content"]
        if not isinstance(content, str):
            return False
        
        if "format" in kwargs:
            file_format = kwargs["format"]
            valid_formats = {"txt", "json", "md"}
            if file_format not in valid_formats:
                return False
        
        return True
    
    def execute(
        self,
        filename: str,
        content: str,
        format: str = "txt",
        overwrite: bool = True
    ) -> ToolResult:
        """
        Write content to file.
        
        Args:
            filename: Output filename
            content: Content to write
            format: File format (txt, json, md)
            overwrite: Whether to overwrite existing files (default: True)
            
        Returns:
            ToolResult with file path
        """
        # Ensure filename has correct extension
        if not filename.endswith(f".{format}"):
            filename = f"{filename}.{format}"
        
        # Construct full file path
        file_path = self.output_dir / filename
        
        # Check if file exists and overwrite is False
        if file_path.exists() and not overwrite:
            return ToolResult(
                success=False,
                data=None,
                error=f"File already exists: {file_path}",
                metadata={"file_path": str(file_path)}
            )
        
        try:
            # Format-specific handling
            if format == "json":
                # Validate JSON
                try:
                    json_data = json.loads(content)
                    # Pretty print JSON
                    content = json.dumps(json_data, indent=2)
                except json.JSONDecodeError as e:
                    return ToolResult(
                        success=False,
                        data=None,
                        error=f"Invalid JSON content: {str(e)}",
                        metadata={"filename": filename}
                    )
            
            # Write file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            file_size = file_path.stat().st_size
            
            if self.logger:
                self.logger.log_info(
                    f"File written: {filename}",
                    {
                        "filename": filename,
                        "format": format,
                        "size": file_size,
                        "path": str(file_path)
                    }
                )
            
            return ToolResult(
                success=True,
                data={
                    "filename": filename,
                    "path": str(file_path),
                    "size": file_size,
                    "format": format
                },
                metadata={
                    "absolute_path": str(file_path.absolute())
                }
            )
        
        except Exception as e:
            return self.handle_error(
                e,
                context={"filename": filename, "format": format}
            )
