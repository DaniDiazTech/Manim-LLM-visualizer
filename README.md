# AI - Manim Video Generator

Automatic video generation using an agentic LLM flow in combination with the [manim](https://www.manim.community/) python library.

## Overview

The project experiments with automated Manim video creation. An agent workflow delegates code drafting to a `Code Writer` and validation to a `Code Reviewer`, using LiteLLM for model routing so different models from different providers can be compared on the same task. The flow focuses on reducing render failures and improving visual consistency through iterative feedback and optional vision inputs.

## Current Flow (subject to change)

![Creation flow](images/flow.png)

## Installation

### 1. Clone the repository:

```bash
git clone https://github.com/makefinks/manim-generator.git
cd manim-generator
```

### 2. Install the requirements

#### Option A: Using traditional venv (recommended for API)

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Install package and all dependencies
pip install -e .
```

Or use the setup script (Linux/macOS):
```bash
./setup_venv.sh
```

On Windows:
```cmd
setup_venv.bat
```

#### Option B: Using uv (alternative)

With [uv](https://github.com/astral-sh/uv):

```bash
uv sync
```

### 3. Additional dependencies

Install ffmpeg and, if you plan to render LaTeX, a LaTeX distribution.

Windows (using Chocolatey):

```bash
choco install ffmpeg
choco install miktex
```

macOS (using Homebrew):

```bash
brew install ffmpeg
brew install --cask mactex
```

Linux (Debian/Ubuntu):

```bash
sudo apt-get update
sudo apt-get install texlive texlive-latex-extra texlive-fonts-extra texlive-science
```

### 4. Configure environment variables

Create a `.env` file from the provided template:

```bash
cp .env.example .env
```

Then edit `.env` and add your API keys. Providers available via [openrouter](https://openrouter.ai/) are supported through LiteLLM with the prefix openrouter.
For example `openrouter/openai/gpt-5.1`

If you configure or have an openai/anthropic API key already configured you can use their respective APIs directly: `openai/gpt-5.1` / `anthropic/claude-sonnet-4-5`

## Usage

### 1. Execute the script

With uv (recommended):

```bash
uv run manim-generate
```

Or if you've activated the virtual environment:

```bash
source .venv/bin/activate
manim-generate
```

Or using Python directly:

```bash
python -m manim_generator.main
```

### 2. CLI Arguments

The script supports the following command-line arguments:

#### Video Data Input

| Argument            | Description                                        | Default          |
| ------------------- | -------------------------------------------------- | ---------------- |
| `--video-data`      | Description of the video to generate (text string) | -                |
| `--video-data-file` | Path to file containing video description          | "video_data.txt" |

#### Model Configuration

| Argument         | Description                                                                              | Default                                |
| ---------------- | ---------------------------------------------------------------------------------------- | -------------------------------------- |
| `--manim-model`  | Model to use for generating Manim code                                                   | "openrouter/anthropic/claude-sonnet-4" |
| `--review-model` | Model to use for reviewing code                                                          | "openrouter/anthropic/claude-sonnet-4" |
| `--streaming`    | Enable streaming responses from the model                                                | False                                  |
| `--temperature`  | Temperature for the LLM Model                                                            | 0.4                                    |
| `--force-vision` | Adds images to the review process, regardless if LiteLLM reports vision is not supported | -                                      |
| `--provider`     | Specific provider to use for OpenRouter requests (e.g., 'anthropic', 'openai')           | -                                      |

#### Process Configuration

| Argument                  | Description                                                                                 | Default                                        |
| ------------------------- | ------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| `--review-cycles`         | Number of review cycles to perform                                                          | 5                                              |
| `--manim-logs`            | Show Manim execution logs                                                                   | False                                          |
| `--output-dir`            | Directory for generated artifacts (overrides auto-naming)                                   | Auto (e.g., `manim_animation_20250101_120000`) |
| `--success-threshold`     | Percentage of scenes that must render successfully to trigger enhanced visual review mode   | 100                                            |
| `--frame-extraction-mode` | Frame extraction mode: highest_density (single best frame) or fixed_count (multiple frames) | "highest_density"                              |
| `--frame-count`           | Number of frames to extract when using fixed_count mode                                     | 3                                              |
| `--scene-timeout`         | Maximum seconds allowed for a single scene render (set to 0 to disable)                     | 120                                            |
| `--headless`              | Suppress most output and show only a single progress bar                                    | False                                          |

#### Reasoning Tokens Configuration

| Argument                 | Description                                                                                  | Default |
| ------------------------ | -------------------------------------------------------------------------------------------- | ------- |
| `--reasoning-effort`     | Reasoning effort level for OpenAI-style models (choices: "none", "minimal", "low", "medium", "high") | -       |
| `--reasoning-max-tokens` | Maximum tokens for reasoning (Anthropic-style)                                               | -       |
| `--reasoning-exclude`    | Exclude reasoning tokens from response (model still uses reasoning internally)               | -       |

> Note: You cannot use both `--reasoning-effort` and `--reasoning-max-tokens` at the same time.

Providing `--output-dir` skips the automatic descriptor-based folder name and uses the supplied path instead.

### Example

```bash
uv run manim-generate --video-data "Explain the concept of neural networks with visual examples" --manim-model "openrouter/anthropic/claude-sonnet-4" --review-model "openrouter/anthropic/claude-sonnet-4" --review-cycles 3
```

Or with the command directly (if virtual environment is activated):

```bash
manim-generate --video-data "Explain the concept of neural networks with visual examples" --manim-model "openrouter/anthropic/claude-sonnet-4" --review-model "openrouter/anthropic/claude-sonnet-4" --review-cycles 3
```

Some standard prompts for benchmarking different models are in the directoy `bench_prompts/`

```
manim-generate --video-data-file bench_prompts/llm_explainer.txt
```

### 3. Configure image support

Images are available only when the reviewer model supports multimodal input.

- https://openrouter.ai/models?modality=text+image-%3Etext
- https://github.com/BerriAI/litellm/blob/main/model_prices_and_context_window.json

## API Usage

The project includes a FastAPI server for generating videos from Manim scripts via HTTP API.

### Quick Start with Traditional venv

1. **Set up the environment** (if not already done):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install --upgrade pip
   pip install -e .
   ```

2. **Start the API server**:
   ```bash
   source .venv/bin/activate  # Activate venv if not already active
   manim-api
   ```

   The server will start on `http://localhost:8000` by default.

### Starting the API Server

Activate your virtual environment and start the server:

```bash
source .venv/bin/activate  # or .venv/scripts/activate on Windows
manim-api
```

Or with custom host/port:

```bash
source .venv/bin/activate
manim-api --host 0.0.0.0 --port 8000
```

Or using Python directly:

```bash
source .venv/bin/activate
python -m manim_generator.api_server
```

### API Endpoints

#### `POST /generate`

Generate a video from a description using LLM (like the `manim-generate` command).

This endpoint uses the full workflow: it generates Manim code from your description using an LLM, reviews and iterates on it, then renders the final video.

**Request Body:**
```json
{
  "video_data": "Explain the concept of neural networks with visual examples",
  "output_dir": "optional/custom/output/dir",
  "min_duration": 60.0,
  "max_duration": 180.0,
  "manim_model": "openrouter/anthropic/claude-sonnet-4",
  "review_model": "openrouter/anthropic/claude-sonnet-4",
  "review_cycles": 3,
  "temperature": 0.4
}
```

**Parameters:**
- `video_data` (required): Description of the video to generate (like `--video-data` argument)
- `output_dir` (optional): Custom output directory for generated files
- `min_duration` (optional): Minimum video duration in seconds (default: 60.0 = 1 minute)
- `max_duration` (optional): Maximum video duration in seconds (default: 180.0 = 3 minutes)
- `manim_model` (optional): Model to use for generating Manim code (default: from config)
- `review_model` (optional): Model to use for reviewing code (default: from config)
- `review_cycles` (optional): Number of review cycles to perform (default: 4)
- `temperature` (optional): Temperature for the LLM Model (default: 0.4)

**Response:**
```json
{
  "success": true,
  "video_path": "/absolute/path/to/video.mp4",
  "video_url": "/video/api_20240101_120000_abc123/final_video.mp4",
  "message": "Video generated successfully (duration: 60.0-180.0s)",
  "error": null
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "video_data": "Explain the concept of neural networks with visual examples",
    "manim_model": "openrouter/anthropic/claude-sonnet-4",
    "review_model": "openrouter/anthropic/claude-sonnet-4",
    "review_cycles": 3,
    "min_duration": 60.0,
    "max_duration": 180.0
  }'
```

#### `POST /generate/script`

Generate a video from a pre-written Manim script (without LLM generation).

**Request Body:**
```json
{
  "script": "from manim import *\n\nclass MyScene(Scene):\n    def construct(self):\n        self.play(Write(Text(\"Hello World\")))",
  "output_dir": "optional/custom/output/dir",
  "min_duration": 60.0,
  "max_duration": 180.0
}
```

**Parameters:**
- `script` (required): The Manim Python script code
- `output_dir` (optional): Custom output directory for generated files
- `min_duration` (optional): Minimum video duration in seconds (default: 60.0 = 1 minute). If the video is shorter, it will be looped/extended to meet this duration.
- `max_duration` (optional): Maximum video duration in seconds (default: 180.0 = 3 minutes). If the video is longer, it will be trimmed to this duration.

**Note:** This endpoint directly renders a provided script without using LLM generation. For LLM-based generation from descriptions, use `/generate` instead.

**Response:**
```json
{
  "success": true,
  "video_path": "/absolute/path/to/video.mp4",
  "video_url": "/video/api_20240101_120000_abc123/final_video.mp4",
  "message": "Video generated successfully",
  "error": null
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/generate/script" \
  -H "Content-Type: application/json" \
  -d '{
    "script": "from manim import *\n\nclass MyScene(Scene):\n    def construct(self):\n        self.play(Write(Text(\"Hello World\")))",
    "min_duration": 60.0,
    "max_duration": 180.0
  }'
```

**Note:** By default, videos are automatically adjusted to be between 1-3 minutes (60-180 seconds). If your script generates a shorter video, it will be looped to reach the minimum duration. If it's longer, it will be trimmed to the maximum duration.

#### `GET /video/{video_path}`

Download a generated video file.

**Example:**
```bash
curl "http://localhost:8000/video/api_20240101_120000_abc123/final_video.mp4" --output video.mp4
```

#### `GET /health`

Health check endpoint.

**Example:**
```bash
curl "http://localhost:8000/health"
```

#### `GET /`

API information endpoint.

**Example:**
```bash
curl "http://localhost:8000/"
```

## Contributing

Focus areas include prompt improvements, review loop refinements, code quality, and new features or optimizations.

### Known issues

- **Streaming**: current streaming implementation does not provide syntax highlighting
- **Prompting / environment setup**: the selected LLM version may not match the local installation.
# Manim-LLM-visualizer
