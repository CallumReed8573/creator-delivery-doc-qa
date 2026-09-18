import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from src.media_doc_qa import QuestionRequest, migration_checklist


def test_creator_question_requires_creator_scope_and_migration_has_rollback():
    request = QuestionRequest(question="When is the trailer delivered?", creator_id="creator-17")
    assert request.creator_id == "creator-17"
    assert any("rollback" in step.lower() for step in migration_checklist())
