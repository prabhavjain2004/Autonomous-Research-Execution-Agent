"""
Unit tests for additional tools: Python executor, file writer, JSON formatter.

Tests safe code execution, file writing with different formats,
and JSON formatting with validation.
"""

import pytest
import tempfile
import shutil
import json
from pathlib import Path

from tools.python_executor import PythonExecutorTool
from tools.file_writer import FileWriterTool
from tools.json_formatter import JSONFormatterTool


class TestPythonExecutorTool:
    """Tests for PythonExecutorTool."""
    
    @pytest.fixture
    def executor(self):
        """Create Python executor instance."""
        return PythonExecutorTool(timeout=5)
    
    def test_initialization(self):
        """Test Python executor initialization."""
        tool = PythonExecutorTool(timeout=10, allowed_imports=["math", "json"])
        assert tool.timeout == 10
        assert "math" in tool.allowed_imports
        assert "json" in tool.allowed_imports
    
    def test_validate_input_success(self, executor):
        """Test input validation with valid inputs."""
        assert executor.validate_input(code="print('hello')") is True
        assert executor.validate_input(code="x = 1 + 1", context={}) is True
    
    def test_validate_input_missing_code(self, executor):
        """Test input validation fails without code."""
        assert executor.validate_input(context={}) is False
    
    def test_validate_input_empty_code(self, executor):
        """Test input validation fails with empty code."""
        assert executor.validate_input(code="") is False
        assert executor.validate_input(code="   ") is False
    
    def test_validate_input_invalid_context(self, executor):
        """Test input validation fails with invalid context."""
        assert executor.validate_input(code="x = 1", context="not a dict") is False
    
    def test_execute_simple_expression(self, executor):
        """Test executing simple expression."""
        result = executor.execute(code="2 + 2")
        
        assert result.success is True
        assert result.data["result"] == 4
        assert result.data["type"] == "int"
    
    def test_execute_with_print(self, executor):
        """Test executing code with print statements."""
        result = executor.execute(code="print('Hello, World!')")
        
        assert result.success is True
        assert "Hello, World!" in result.data["stdout"]
    
    def test_execute_with_context(self, executor):
        """Test executing code with injected context."""
        result = executor.execute(
            code="x + y",
            context={"x": 10, "y": 20}
        )
        
        assert result.success is True
        assert result.data["result"] == 30
    
    def test_execute_with_result_variable(self, executor):
        """Test executing code that sets result variable."""
        result = executor.execute(code="result = 5 * 5")
        
        assert result.success is True
        assert result.data["result"] == 25
    
    def test_execute_with_allowed_import(self, executor):
        """Test executing code with allowed import."""
        result = executor.execute(code="import math\nresult = math.sqrt(16)")
        
        assert result.success is True
        assert result.data["result"] == 4.0
    
    def test_execute_with_disallowed_import(self, executor):
        """Test executing code with disallowed import."""
        result = executor.execute(code="import os\nos.listdir('.')")
        
        assert result.success is False
        assert "disallowed imports" in result.error.lower()
    
    def test_execute_with_syntax_error(self, executor):
        """Test executing code with syntax error."""
        result = executor.execute(code="if True print('test')")
        
        assert result.success is False
        assert "SyntaxError" in result.error
    
    def test_execute_with_runtime_error(self, executor):
        """Test executing code with runtime error."""
        result = executor.execute(code="1 / 0")
        
        assert result.success is False
        assert "ZeroDivisionError" in result.error
    
    def test_execute_multiline_code(self, executor):
        """Test executing multiline code."""
        code = """
x = 10
y = 20
result = x + y
"""
        result = executor.execute(code=code)
        
        assert result.success is True
        assert result.data["result"] == 30
    
    def test_execute_with_list_comprehension(self, executor):
        """Test executing code with list comprehension."""
        result = executor.execute(code="[x**2 for x in range(5)]")
        
        assert result.success is True
        assert result.data["result"] == [0, 1, 4, 9, 16]
    
    def test_execute_with_json_module(self, executor):
        """Test executing code with json module."""
        code = "import json\nresult = json.dumps({'key': 'value'})"
        result = executor.execute(code=code)
        
        assert result.success is True
        assert '"key": "value"' in result.data["result"]
    
    def test_execution_time_tracking(self, executor):
        """Test that execution time is tracked."""
        result = executor.execute(code="2 + 2")
        
        assert result.success is True
        assert "execution_time" in result.metadata
        assert result.metadata["execution_time"] >= 0


class TestFileWriterTool:
    """Tests for FileWriterTool."""
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def writer(self, temp_output_dir):
        """Create file writer instance."""
        return FileWriterTool(output_dir=temp_output_dir)
    
    def test_initialization(self, temp_output_dir):
        """Test file writer initialization."""
        tool = FileWriterTool(output_dir=temp_output_dir)
        assert tool.output_dir == Path(temp_output_dir)
        assert tool.output_dir.exists()
    
    def test_validate_input_success(self, writer):
        """Test input validation with valid inputs."""
        assert writer.validate_input(filename="test.txt", content="Hello") is True
        assert writer.validate_input(
            filename="test",
            content="Hello",
            format="json"
        ) is True
    
    def test_validate_input_missing_params(self, writer):
        """Test input validation fails with missing parameters."""
        assert writer.validate_input(filename="test.txt") is False
        assert writer.validate_input(content="Hello") is False
    
    def test_validate_input_empty_filename(self, writer):
        """Test input validation fails with empty filename."""
        assert writer.validate_input(filename="", content="Hello") is False
        assert writer.validate_input(filename="   ", content="Hello") is False
    
    def test_validate_input_path_traversal(self, writer):
        """Test input validation prevents path traversal."""
        assert writer.validate_input(filename="../test.txt", content="Hello") is False
        assert writer.validate_input(filename="/etc/passwd", content="Hello") is False
    
    def test_validate_input_invalid_format(self, writer):
        """Test input validation fails with invalid format."""
        assert writer.validate_input(
            filename="test",
            content="Hello",
            format="invalid"
        ) is False
    
    def test_write_text_file(self, writer, temp_output_dir):
        """Test writing text file."""
        result = writer.execute(
            filename="test.txt",
            content="Hello, World!",
            format="txt"
        )
        
        assert result.success is True
        assert result.data["filename"] == "test.txt"
        assert result.data["format"] == "txt"
        
        # Verify file exists and content
        file_path = Path(temp_output_dir) / "test.txt"
        assert file_path.exists()
        assert file_path.read_text() == "Hello, World!"
    
    def test_write_json_file(self, writer, temp_output_dir):
        """Test writing JSON file."""
        json_content = json.dumps({"key": "value", "number": 42})
        
        result = writer.execute(
            filename="test.json",
            content=json_content,
            format="json"
        )
        
        assert result.success is True
        assert result.data["format"] == "json"
        
        # Verify file exists and content
        file_path = Path(temp_output_dir) / "test.json"
        assert file_path.exists()
        
        data = json.loads(file_path.read_text())
        assert data["key"] == "value"
        assert data["number"] == 42
    
    def test_write_markdown_file(self, writer, temp_output_dir):
        """Test writing markdown file."""
        md_content = "# Heading\n\nParagraph text."
        
        result = writer.execute(
            filename="test.md",
            content=md_content,
            format="md"
        )
        
        assert result.success is True
        assert result.data["format"] == "md"
        
        # Verify file exists
        file_path = Path(temp_output_dir) / "test.md"
        assert file_path.exists()
    
    def test_write_with_auto_extension(self, writer, temp_output_dir):
        """Test that extension is added automatically."""
        result = writer.execute(
            filename="test",
            content="Hello",
            format="txt"
        )
        
        assert result.success is True
        assert result.data["filename"] == "test.txt"
    
    def test_write_invalid_json(self, writer):
        """Test writing invalid JSON fails."""
        result = writer.execute(
            filename="test.json",
            content="not valid json",
            format="json"
        )
        
        assert result.success is False
        assert "Invalid JSON" in result.error
    
    def test_overwrite_existing_file(self, writer, temp_output_dir):
        """Test overwriting existing file."""
        # Write first file
        writer.execute(filename="test.txt", content="First", format="txt")
        
        # Overwrite
        result = writer.execute(
            filename="test.txt",
            content="Second",
            format="txt",
            overwrite=True
        )
        
        assert result.success is True
        
        # Verify content was overwritten
        file_path = Path(temp_output_dir) / "test.txt"
        assert file_path.read_text() == "Second"
    
    def test_no_overwrite_existing_file(self, writer, temp_output_dir):
        """Test not overwriting existing file when overwrite=False."""
        # Write first file
        writer.execute(filename="test.txt", content="First", format="txt")
        
        # Try to write again with overwrite=False
        result = writer.execute(
            filename="test.txt",
            content="Second",
            format="txt",
            overwrite=False
        )
        
        assert result.success is False
        assert "already exists" in result.error.lower()
    
    def test_file_size_tracking(self, writer):
        """Test that file size is tracked."""
        result = writer.execute(
            filename="test.txt",
            content="Hello, World!",
            format="txt"
        )
        
        assert result.success is True
        assert "size" in result.data
        assert result.data["size"] > 0


class TestJSONFormatterTool:
    """Tests for JSONFormatterTool."""
    
    @pytest.fixture
    def formatter(self):
        """Create JSON formatter instance."""
        return JSONFormatterTool()
    
    def test_initialization(self):
        """Test JSON formatter initialization."""
        tool = JSONFormatterTool()
        assert tool is not None
    
    def test_validate_input_success(self, formatter):
        """Test input validation with valid inputs."""
        assert formatter.validate_input(data={"key": "value"}) is True
        assert formatter.validate_input(data=[1, 2, 3]) is True
        assert formatter.validate_input(data="string") is True
    
    def test_validate_input_missing_data(self, formatter):
        """Test input validation fails without data."""
        assert formatter.validate_input(schema={}) is False
    
    def test_validate_input_invalid_schema(self, formatter):
        """Test input validation fails with invalid schema."""
        assert formatter.validate_input(data={}, schema="not a dict") is False
    
    def test_format_simple_dict(self, formatter):
        """Test formatting simple dictionary."""
        data = {"key": "value", "number": 42}
        result = formatter.execute(data=data)
        
        assert result.success is True
        assert "key" in result.data["json"]
        assert "value" in result.data["json"]
        assert result.data["minified"] is False
    
    def test_format_with_minify(self, formatter):
        """Test formatting with minification."""
        data = {"key": "value", "number": 42}
        result = formatter.execute(data=data, minify=True)
        
        assert result.success is True
        assert result.data["minified"] is True
        # Minified JSON should not have spaces after colons
        assert ": " not in result.data["json"]
    
    def test_format_with_custom_indent(self, formatter):
        """Test formatting with custom indentation."""
        data = {"key": "value"}
        result = formatter.execute(data=data, indent=4)
        
        assert result.success is True
        # Should have 4-space indentation
        assert "    " in result.data["json"]
    
    def test_format_list(self, formatter):
        """Test formatting list."""
        data = [1, 2, 3, 4, 5]
        result = formatter.execute(data=data)
        
        assert result.success is True
        assert "[" in result.data["json"]
        assert "]" in result.data["json"]
    
    def test_format_nested_structure(self, formatter):
        """Test formatting nested structure."""
        data = {
            "users": [
                {"name": "Alice", "age": 30},
                {"name": "Bob", "age": 25}
            ],
            "count": 2
        }
        result = formatter.execute(data=data)
        
        assert result.success is True
        assert "users" in result.data["json"]
        assert "Alice" in result.data["json"]
    
    def test_schema_validation_success(self, formatter):
        """Test schema validation with valid data."""
        data = {"name": "Alice", "age": 30}
        schema = {
            "type": "object",
            "required": ["name", "age"]
        }
        
        result = formatter.execute(data=data, schema=schema)
        
        assert result.success is True
        assert result.data["validated"] is True
    
    def test_schema_validation_missing_required(self, formatter):
        """Test schema validation fails with missing required field."""
        data = {"name": "Alice"}
        schema = {
            "type": "object",
            "required": ["name", "age"]
        }
        
        result = formatter.execute(data=data, schema=schema)
        
        assert result.success is False
        assert "Required field missing" in result.error
    
    def test_schema_validation_wrong_type(self, formatter):
        """Test schema validation fails with wrong type."""
        data = "string"
        schema = {"type": "object"}
        
        result = formatter.execute(data=data, schema=schema)
        
        assert result.success is False
        assert "Expected type" in result.error
    
    def test_non_serializable_data(self, formatter):
        """Test formatting non-serializable data fails."""
        class CustomClass:
            pass
        
        data = {"obj": CustomClass()}
        result = formatter.execute(data=data)
        
        assert result.success is False
        assert "not JSON serializable" in result.error
    
    def test_size_tracking(self, formatter):
        """Test that JSON size is tracked."""
        data = {"key": "value"}
        result = formatter.execute(data=data)
        
        assert result.success is True
        assert "size" in result.data
        assert result.data["size"] > 0
