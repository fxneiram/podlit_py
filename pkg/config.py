import os

# FOLDER PATHS
TEMP_DIR = os.getcwd() + "/tmp"
OUTPUT_DIR = os.getcwd() + "/output"

# COLORS
BACKGROUND_COLOR = (0, 0, 0)
TEXT_COLOR = (255, 255, 255)

# SIZES
HEIGHT = 720
WIDTH = 720
MAX_WIDTH = 600
FONT_SIZE = 80

# MEDIA
DURATION_BETWEEN_FRAGMENTS = 0  # ms
FPS = 24

# TTS ENGINE
# "coqui" (default, always available) or "magpie" (requires nemo_toolkit installed separately -
# see `make install-magpie` - not part of the default install).
TTS_ENGINE = os.environ.get("TTS_ENGINE", "coqui")

# TASK QUEUE API
# Single JSON file backing the REST API's task queue (adapters/driving/api). Independent of
# WindowTaskQueueManager's own in-memory + pickle .que save/load - the two aren't unified yet.
QUEUE_STORAGE_PATH = os.environ.get("QUEUE_STORAGE_PATH", os.path.join(os.getcwd(), "queue_storage.json"))
