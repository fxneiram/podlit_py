from typing import Optional

from fastapi import FastAPI

from adapters.driving.api.routes import router
from application.use_cases.manage_task_queue_use_case import ManageTaskQueueUseCase
from application.use_cases.manage_voices_use_case import ManageVoicesUseCase
from application.use_cases.process_queue_use_case import ProcessQueueUseCase
from domain.progress_tracker import ProgressTracker


def create_app(
    use_case: ManageTaskQueueUseCase,
    process_queue_use_case: Optional[ProcessQueueUseCase] = None,
    progress_tracker: Optional[ProgressTracker] = None,
    manage_voices_use_case: Optional[ManageVoicesUseCase] = None,
) -> FastAPI:
    app = FastAPI(title="PodLitPy Task Queue API")
    app.state.use_case = use_case
    app.state.process_queue_use_case = process_queue_use_case
    app.state.progress_tracker = progress_tracker
    app.state.manage_voices_use_case = manage_voices_use_case
    app.include_router(router)
    return app
