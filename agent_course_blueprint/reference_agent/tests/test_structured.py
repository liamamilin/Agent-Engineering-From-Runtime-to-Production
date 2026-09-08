import pytest

from agent_course.llm import StructuredOutput, SchemaValidator


class TestStructuredOutput:
    def test_parse_direct_json(self):
        content = '{"answer": "42", "confidence": 0.95}'
        result = StructuredOutput.parse_json(content)
        assert result["answer"] == "42"
        assert result["confidence"] == 0.95

    def test_parse_json_from_code_block(self):
        content = '''Here is the result:
```json
{"answer": "Paris", "confidence": 0.9}
```
Done.'''
        result = StructuredOutput.parse_json(content)
        assert result["answer"] == "Paris"

    def test_parse_json_from_text(self):
        content = 'The answer is {"answer": "yes", "confidence": 1} according to analysis.'
        result = StructuredOutput.parse_json(content)
        assert result["answer"] == "yes"

    def test_parse_invalid_json_raises(self):
        with pytest.raises(ValueError):
            StructuredOutput.parse_json("no json here")


class TestSchemaValidator:
    def test_valid_data(self):
        validator = SchemaValidator({"name": str, "age": int})
        is_valid, errors = validator.validate({"name": "Alice", "age": 30})
        assert is_valid
        assert errors == []

    def test_missing_field(self):
        validator = SchemaValidator({"name": str, "age": int})
        is_valid, errors = validator.validate({"name": "Alice"})
        assert not is_valid
        assert len(errors) == 1
        assert "age" in errors[0]

    def test_wrong_type(self):
        validator = SchemaValidator({"name": str, "age": int})
        is_valid, errors = validator.validate({"name": "Alice", "age": "thirty"})
        assert not is_valid
        assert "age" in errors[0]

    def test_decision_validator(self):
        validator = SchemaValidator.for_decision()
        is_valid, errors = validator.validate({
            "kind": "tool",
            "name": "search",
            "arguments": {"query": "test"},
        })
        assert is_valid

    def test_answer_validator(self):
        validator = SchemaValidator.for_answer()
        is_valid, errors = validator.validate({
            "answer": "Paris",
            "confidence": 0.9,
        })
        assert is_valid
