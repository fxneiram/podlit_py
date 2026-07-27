from fastapi import FastAPI

from adapters.driving.api.routes import router
from application.use_cases.manage_task_queue_use_case import ManageTaskQueueUseCase


def create_app(use_case: ManageTaskQueueUseCase) -> FastAPI:
    app = FastAPI(title="PodLitPy Task Queue API")
    app.state.use_case = use_case
    app.include_router(router)
    return app
