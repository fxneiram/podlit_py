from fastapi import APIRouter, Depends, HTTPException, Request

from adapters.driving.api.schemas import QueueReplaceRequest, TaskCreateRequest, TaskResponse
from application.use_cases.manage_task_queue_use_case import ManageTaskQueueUseCase
from domain.exceptions import TaskNotFoundError

router = APIRouter()


def get_use_case(request: Request) -> ManageTaskQueueUseCase:
    return request.app.state.use_case


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
