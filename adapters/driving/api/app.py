from fastapi import FastAPI

from adapters.driving.api.routes import router
from application.use_cases.manage_task_queue_use_case import ManageTaskQueueUseCase
from application.use_cases.process_queue_use_case import ProcessQueueUseCase
from domain.progress_tracker import ProgressTracker


def create_app(
    use_case: ManageTaskQueueUseCase,
    process_queue_use_case: ProcessQueueUseCase | None = None,
    progress_tracker: ProgressTracker | None = None,
) -> FastAPI:
    app = FastAPI(title="PodLitPy Task Queue API")
    app.state.use_case = use_case
    app.state.process_queue_use_case = process_queue_use_case
    app.state.progress_tracker = progress_tracker
    app.include_router(router)
    return app
