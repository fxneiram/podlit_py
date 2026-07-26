.PHONY: install install-ffmpeg install-espeak-ng install-deps install-magpie create-env activate-env run

# Default target when 'make' is run without arguments
all: install

# Main installation target
install: install-ffmpeg install-espeak-ng create-env install-deps

# Install ffmpeg using Homebrew (macOS)
install-ffmpeg:
	@echo "Checking for Homebrew..."
	@if ! command -v brew &> /dev/null; then \
		echo "Installing Homebrew..."; \
		/bin/bash -c "$$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"; \
		echo 'eval "$$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile; \
		eval "$$(/opt/homebrew/bin/brew shellenv)"; \
	fi
	@echo "Installing ffmpeg..."
	brew install ffmpeg

# Install espeak-ng (native CLI binary used by EspeakNGAdapter, not a pip package)
install-espeak-ng:
	@echo "Installing espeak-ng..."
	brew install espeak-ng

# Create conda environment
create-env:
	@echo "Creating conda environment 'tts'..."
	conda create -n tts python=3.9 -y
	@echo "\nTo activate the environment, run:"
	@echo "  conda activate tts"

# Install Python dependencies
install-deps:
	@echo "Installing Python dependencies..."
	pip install --upgrade pip
	pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
	pip install TTS==0.22.0
	pip install opencv-python
	pip install pydub
	pip install numpy==1.26.4
	@echo "\nDependencies installed successfully!"

# Optional: install MagpieTTSAdapter's dependency (nvidia/magpie_tts_multilingual_357m via
# NeMo). NOT part of `make install` - nemo_toolkit is a large (~2.2GB), unpinned install from
# its main git branch (the stable PyPI release fails to load this specific model checkpoint),
# too heavy/unstable to force on every install. Run this yourself, then set TTS_ENGINE=magpie
# to use it (see pkg/config.py) - the default TTS_ENGINE (coqui) never needs this.
# torchcodec is also required: a fresh, unpinned torchaudio moved its .save() default backend
# to require it (confirmed while running the #37 regression test) - without it, synthesize()
# fails with "ImportError: TorchCodec is required for save_with_torchcodec".
install-magpie:
	@echo "Installing nemo_toolkit from its main branch (large, unpinned - this will take a while)..."
	pip install "nemo_toolkit[tts] @ git+https://github.com/NVIDIA-NeMo/NeMo.git"
	pip install torchcodec

# Run the application
run:
	@echo "Running the application..."
	python app.py

# Clean up temporary files
clean:
	@echo "Cleaning up..."
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -exec rm -rf {} +

# Show help
help:
	@echo "Available targets:"
	@echo "  install         : Install all dependencies (default)"
	@echo "  install-ffmpeg  : Install ffmpeg using Homebrew"
	@echo "  install-espeak-ng : Install espeak-ng using Homebrew"
	@echo "  create-env      : Create conda environment"
	@echo "  install-deps    : Install Python dependencies"
	@echo "  install-magpie  : Install MagpieTTS's nemo_toolkit dependency (optional, not part of 'install')"
	@echo "  run             : Run the application"
	@echo "  clean           : Clean up temporary files"
	@echo "  help            : Show this help message"
