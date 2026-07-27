import asyncio
import json
from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from adapters.driving.api.schemas import QueueProcessRequest, QueueReplaceRequest, TaskCreateRequest, TaskResponse
from application.use_cases.manage_task_queue_use_case import ManageTaskQueueUseCase
from application.use_cases.process_queue_use_case import ProcessQueueUseCase
from domain.exceptions import QueueAlreadyProcessingError, TaskNotFoundError
from domain.progress_tracker import ProgressTracker

PROGRESS_POLL_INTERVAL_SECONDS = 0.2

router = APIRouter()


def get_use_case(request: Request) -> ManageTaskQueueUseCase:
    return request.app.state.use_case


def get_process_queue_use_case(request: Request) -> ProcessQueueUseCase:
    return request.app.state.process_queue_use_case


def get_progress_tracker(request: Request) -> ProgressTracker:
    return request.app.state.progress_tracker


def _to_response(record) -> TaskResponse:
    return TaskResponse(id=record.id, data=record.data)


@router.post("/tasks", response_model=TaskResponse, status_code=201)
def create_task(body: TaskCreateRequest, use_case: ManageTaskQueueUseCase = Depends(get_use_case)):
    try:
        record = use_case.add_task(body.raw_text)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return _to_response(record)


@router.get("/tasks", response_model=list[TaskResponse])
def list_tasks(use_case: ManageTaskQueueUseCase = Depends(get_use_case)):
    return [_to_response(record) for record in use_case.list_tasks()]


@router.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: str, use_case: ManageTaskQueueUseCase = Depends(get_use_case)):
    try:
        record = use_case.get_task(task_id)
    except TaskNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return _to_response(record)


@router.put("/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: str, body: TaskCreateRequest, use_case: ManageTaskQueueUseCase = Depends(get_use_case)):
    try:
        record = use_case.update_task(task_id, body.raw_text)
    except TaskNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return _to_response(record)


@router.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: str, use_case: ManageTaskQueueUseCase = Depends(get_use_case)):
    try:
        use_case.delete_task(task_id)
    except TaskNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/queue", response_model=list[TaskResponse])
def get_queue(use_case: ManageTaskQueueUseCase = Depends(get_use_case)):
    return [_to_response(record) for record in use_case.get_queue()]


@router.post("/queue", response_model=list[TaskResponse])
def replace_queue(body: QueueReplaceRequest, use_case: ManageTaskQueueUseCase = Depends(get_use_case)):
    try:
        records = use_case.replace_queue(body.raw_texts)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return [_to_response(record) for record in records]


@router.post("/queue/process", status_code=202)
def process_queue(
    body: QueueProcessRequest,
    process_queue_use_case: ProcessQueueUseCase = Depends(get_process_queue_use_case),
):
    try:
        process_queue_use_case.start(task_delay_ms=body.task_delay_ms, mix_queue=body.mix_queue)
    except QueueAlreadyProcessingError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return {"status": "started"}


@router.get("/queue/progress")
async def queue_progress(progress_tracker: ProgressTracker = Depends(get_progress_tracker)):
    async def event_stream():
        last_state = None
        while True:
            state = progress_tracker.state
            if state != last_state:
                yield f"data: {json.dumps(asdict(state))}\n\n"
                last_state = state
            if state.status == "completed":
                break
            await asyncio.sleep(PROGRESS_POLL_INTERVAL_SECONDS)

    return StreamingResponse(event_stream(), media_type="text/event-stream")
