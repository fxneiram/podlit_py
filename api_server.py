import uvicorn

from adapters.driven.persistence.json_task_repository import JsonTaskRepository
from adapters.driving.api.app import create_app
from application.use_cases.manage_task_queue_use_case import ManageTaskQueueUseCase
from pkg import config as cfg

repository = JsonTaskRepository(storage_path=cfg.QUEUE_STORAGE_PATH)
use_case = ManageTaskQueueUseCase(repository=repository)
app = create_app(use_case)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
