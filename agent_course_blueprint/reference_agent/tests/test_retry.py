import pytest

from agent_course.llm import RetryPolicy, RetryableError, FakeModel, ModelResponse, Message
from agent_course.llm.retry import RetryingModelAdapter


class FailingModel:
    """Model that fails N times then succeeds."""

    def __init__(self, fail_count: int, success_response: ModelResponse | None = None):
        self._fail_count = fail_count
        self._call_count = 0
        self._success_response = success_response or ModelResponse(content="Success")

    def complete(self, messages, **kwargs):
        self._call_count += 1
        if self._call_count <= self._fail_count:
            raise RetryableError(f"Transient error {self._call_count}")
        return self._success_response


class TestRetryPolicy:
    def test_succeeds_first_try(self):
        model = FakeModel(responses=[ModelResponse(content="OK")])
        policy = RetryPolicy(max_retries=3, base_delay=0.01)
        result = policy.execute(lambda: model.complete([Message.user("test")]))
        assert result.content == "OK"

    def test_retries_then_succeeds(self):
        model = FailingModel(fail_count=2)
        policy = RetryPolicy(max_retries=3, base_delay=0.01)
        result = policy.execute(lambda: model.complete([Message.user("test")]))
        assert result.content == "Success"
        assert model._call_count == 3

    def test_exhausts_retries(self):
        model = FailingModel(fail_count=5)
        policy = RetryPolicy(max_retries=2, base_delay=0.01)
        with pytest.raises(RetryableError):
            policy.execute(lambda: model.complete([Message.user("test")]))

    def test_non_retryable_error_raises_immediately(self):
        class BadModel:
            def complete(self, messages, **kwargs):
                raise ValueError("Not retryable")

        policy = RetryPolicy(max_retries=3, base_delay=0.01)
        with pytest.raises(ValueError, match="Not retryable"):
            policy.execute(lambda: BadModel().complete([Message.user("test")]))


class TestRetryingModelAdapter:
    def test_wraps_adapter_with_retry(self):
        base = FailingModel(fail_count=1)
        adapter = RetryingModelAdapter(base, RetryPolicy(max_retries=3, base_delay=0.01))
        result = adapter.complete([Message.user("test")])
        assert result.content == "Success"
