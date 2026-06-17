from app.services.prompt_builder import build_system_prompt
from app.models.session import ExecutionResult


class TestBuildSystemPrompt:
    def test_contains_question_title(self, sample_session):
        prompt = build_system_prompt(sample_session)
        assert "Two Sum" in prompt

    def test_contains_difficulty(self, sample_session):
        prompt = build_system_prompt(sample_session)
        assert "easy" in prompt

    def test_contains_test_case(self, sample_session):
        prompt = build_system_prompt(sample_session)
        assert "nums=[2,7,11], target=9" in prompt

    def test_contains_follow_up(self, sample_session):
        prompt = build_system_prompt(sample_session)
        assert "What if the array were sorted?" in prompt

    def test_elapsed_time_shown(self, sample_session):
        sample_session.elapsed_seconds = 125  # 2 min 5 sec → shown as 2 minutes
        prompt = build_system_prompt(sample_session)
        assert "2 minutes" in prompt

    def test_hints_count_shown(self, sample_session):
        sample_session.hints_used = 1
        prompt = build_system_prompt(sample_session)
        assert "1 / 2" in prompt

    def test_no_code_section_when_no_snapshots(self, sample_session):
        prompt = build_system_prompt(sample_session)
        assert "current code" not in prompt

    def test_code_injected_when_snapshot_exists(self, sample_session):
        sample_session.snapshot_code("def two_sum(nums, target): pass")
        prompt = build_system_prompt(sample_session)
        assert "current code" in prompt
        assert "def two_sum" in prompt

    def test_execution_result_injected_with_code(self, sample_session):
        sample_session.snapshot_code("print('hello')")
        sample_session.last_execution = ExecutionResult(
            stdout="hello\n", stderr="", status="Accepted"
        )
        prompt = build_system_prompt(sample_session)
        assert "Accepted" in prompt

    def test_contains_alex_identity(self, sample_session):
        prompt = build_system_prompt(sample_session)
        assert "Alex" in prompt

    def test_contains_never_give_answer_rule(self, sample_session):
        prompt = build_system_prompt(sample_session)
        assert "NEVER" in prompt
