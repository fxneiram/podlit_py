from domain.progress_tracker import ProgressTracker


def test_initial_state_is_idle():
    tracker = ProgressTracker()

    assert tracker.state.status == "idle"
    assert tracker.state.queue_progress == 0.0


def test_start_sets_running_with_zero_progress():
    tracker = ProgressTracker()

    tracker.start()

    assert tracker.state.status == "running"
    assert tracker.state.queue_progress == 0.0


def test_update_current_task_computes_overall_queue_progress():
    """Mirrors WindowTaskQueueManager.update_queue_progress's formula:
    (completed_tasks + current_task_fraction) / total_tasks * 100."""
    tracker = ProgressTracker()
    tracker.start()

    # First of 4 tasks, halfway done
    tracker.update_current_task(task_index=0, total_tasks=4, task_progress=50, status="Processing fragment 1/2")

    assert tracker.state.status == "running"
    assert tracker.state.current_task_index == 0
    assert tracker.state.current_task_progress == 50
    assert tracker.state.current_task_status == "Processing fragment 1/2"
    assert tracker.state.queue_progress == 12.5  # (0 + 0.5) / 4 * 100


def test_update_current_task_for_a_later_task_reflects_prior_completions():
    tracker = ProgressTracker()
    tracker.start()

    # Third of 4 tasks (index 2), fully done
    tracker.update_current_task(task_index=2, total_tasks=4, task_progress=100, status="Done")

    assert tracker.state.queue_progress == 75.0  # (2 + 1.0) / 4 * 100


def test_complete_sets_completed_status_and_full_progress():
    tracker = ProgressTracker()
    tracker.start()

    tracker.complete()

    assert tracker.state.status == "completed"
    assert tracker.state.queue_progress == 100.0
