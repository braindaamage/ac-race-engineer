"""Tests for engineer API response models."""

from __future__ import annotations

from api.engineer.serializers import (
    ApplyRequest,
    ApplyResponse,
    ChatJobResponse,
    ChatRequest,
    ClearMessagesResponse,
    DriverFeedbackDetail,
    EngineerJobResponse,
    MessageListResponse,
    MessageResponse,
    RecommendationDetailResponse,
    RecommendationListResponse,
    RecommendationSummary,
    SetupChangeDetail,
)


class TestEngineerJobResponse:
    def test_create(self) -> None:
        resp = EngineerJobResponse(job_id="j1", session_id="s1")
        assert resp.job_id == "j1"
        assert resp.session_id == "s1"


class TestRecommendationSummary:
    def test_create(self) -> None:
        rec = RecommendationSummary(
            recommendation_id="r1",
            session_id="s1",
            status="proposed",
            summary="Reduce front ARB",
            change_count=2,
            created_at="2026-03-05T12:00:00+00:00",
        )
        assert rec.recommendation_id == "r1"
        assert rec.change_count == 2
        assert rec.status == "proposed"


class TestRecommendationListResponse:
    def test_create_empty(self) -> None:
        resp = RecommendationListResponse(session_id="s1", recommendations=[])
        assert resp.session_id == "s1"
        assert resp.recommendations == []

    def test_create_with_items(self) -> None:
        item = RecommendationSummary(
            recommendation_id="r1",
            session_id="s1",
            status="proposed",
            summary="test",
            change_count=1,
            created_at="2026-03-05T12:00:00+00:00",
        )
        resp = RecommendationListResponse(session_id="s1", recommendations=[item])
        assert len(resp.recommendations) == 1


class TestSetupChangeDetail:
    def test_create_with_defaults(self) -> None:
        change = SetupChangeDetail(
            section="ARB",
            parameter="FRONT",
            old_value="5",
            new_value="3",
            reasoning="Reduce understeer",
        )
        assert change.expected_effect == ""
        assert change.confidence == "medium"

    def test_create_with_all_fields(self) -> None:
        change = SetupChangeDetail(
            section="ARB",
            parameter="FRONT",
            old_value="5",
            new_value="3",
            reasoning="Reduce understeer",
            expected_effect="Less understeer in T3",
            confidence="high",
        )
        assert change.expected_effect == "Less understeer in T3"
        assert change.confidence == "high"


class TestDriverFeedbackDetail:
    def test_create(self) -> None:
        fb = DriverFeedbackDetail(
            area="braking",
            observation="Late braking",
            suggestion="Brake earlier",
            corners_affected=[3, 7],
            severity="medium",
        )
        assert fb.area == "braking"
        assert fb.corners_affected == [3, 7]

    def test_empty_corners(self) -> None:
        fb = DriverFeedbackDetail(
            area="throttle",
            observation="Good",
            suggestion="Keep it up",
            severity="low",
        )
        assert fb.corners_affected == []


class TestRecommendationDetailResponse:
    def test_create_with_defaults(self) -> None:
        resp = RecommendationDetailResponse(
            recommendation_id="r1",
            session_id="s1",
            status="proposed",
            summary="Test",
            created_at="2026-03-05T12:00:00+00:00",
        )
        assert resp.explanation == ""
        assert resp.confidence == "medium"
        assert resp.signals_addressed == []
        assert resp.setup_changes == []
        assert resp.driver_feedback == []

    def test_create_with_full_data(self) -> None:
        resp = RecommendationDetailResponse(
            recommendation_id="r1",
            session_id="s1",
            status="proposed",
            summary="Test",
            explanation="Detailed explanation",
            confidence="high",
            signals_addressed=["high_understeer"],
            setup_changes=[
                SetupChangeDetail(
                    section="ARB", parameter="FRONT",
                    old_value="5", new_value="3",
                    reasoning="test", expected_effect="less understeer",
                    confidence="high",
                )
            ],
            driver_feedback=[
                DriverFeedbackDetail(
                    area="braking", observation="Late",
                    suggestion="Earlier", corners_affected=[3],
                    severity="medium",
                )
            ],
            created_at="2026-03-05T12:00:00+00:00",
        )
        assert len(resp.setup_changes) == 1
        assert len(resp.driver_feedback) == 1
        assert resp.confidence == "high"


class TestApplyModels:
    def test_apply_request(self) -> None:
        req = ApplyRequest(setup_path="C:/path/to/setup.ini")
        assert req.setup_path == "C:/path/to/setup.ini"

    def test_apply_response(self) -> None:
        resp = ApplyResponse(
            recommendation_id="r1",
            status="applied",
            backup_path="C:/path/backup.ini",
            changes_applied=3,
        )
        assert resp.status == "applied"
        assert resp.changes_applied == 3


class TestChatModels:
    def test_chat_request(self) -> None:
        req = ChatRequest(content="Why reduce ARB?")
        assert req.content == "Why reduce ARB?"

    def test_chat_job_response(self) -> None:
        resp = ChatJobResponse(job_id="j1", message_id="m1")
        assert resp.job_id == "j1"
        assert resp.message_id == "m1"


class TestMessageModels:
    def test_message_response(self) -> None:
        msg = MessageResponse(
            message_id="m1",
            role="user",
            content="Hello",
            created_at="2026-03-05T12:00:00+00:00",
        )
        assert msg.role == "user"

    def test_message_list_response(self) -> None:
        resp = MessageListResponse(session_id="s1", messages=[])
        assert resp.messages == []

    def test_clear_messages_response(self) -> None:
        resp = ClearMessagesResponse(session_id="s1", deleted_count=5)
        assert resp.deleted_count == 5
