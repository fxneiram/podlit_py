import uvicorn

from adapters.driven.persistence.json_task_repository import JsonTaskRepository
from adapters.driving.api.app import create_app
from app import build_tts_engine
from application.use_cases.manage_task_queue_use_case import ManageTaskQueueUseCase
from application.use_cases.process_queue_use_case import ProcessQueueUseCase
from audio_video_generator import AudioVideoGenerator
from domain.progress_tracker import ProgressTracker
from pkg import config as cfg

repository = JsonTaskRepository(storage_path=cfg.QUEUE_STORAGE_PATH)
use_case = ManageTaskQueueUseCase(repository=repository)

media_generator = AudioVideoGenerator(tts_engine=build_tts_engine(cfg.TTS_ENGINE))
progress_tracker = ProgressTracker()
process_queue_use_case = ProcessQueueUseCase(
    repository=repository, media_generator=media_generator, progress_tracker=progress_tracker
)

app = create_app(use_case, process_queue_use_case=process_queue_use_case, progress_tracker=progress_tracker)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
