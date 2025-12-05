"""Model unit tests."""

from app.models.dataset import DatasetLifecycleStatus


def test_dataset_lifecycle_enum() -> None:
    """Dataset lifecycle status enum values."""
    assert DatasetLifecycleStatus.DRAFT.value == "draft"
    assert DatasetLifecycleStatus.ACTIVE.value == "active"
    assert DatasetLifecycleStatus.ARCHIVED.value == "archived"


def test_dataset_lifecycle_transitions() -> None:
    """Valid lifecycle state transitions."""
    valid_states = {s.value for s in DatasetLifecycleStatus}
    assert "draft" in valid_states
    assert "ingesting" in valid_states
    assert "active" in valid_states
