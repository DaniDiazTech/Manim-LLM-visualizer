# Quick Start Guide - API with Traditional venv

This guide will help you set up and run the Manim Video Generator API using the traditional Python virtual environment approach.

## Step 1: Create Virtual Environment

```bash
python3 -m venv .venv
```

## Step 2: Activate Virtual Environment

**On Linux/macOS:**
```bash
source .venv/bin/activate
```

**On Windows:**
```cmd
.venv\Scripts\activate
```

## Step 3: Upgrade pip

```bash
pip install --upgrade pip
```

## Step 4: Install Package and Dependencies

```bash
pip install -e .
```

This will install all required dependencies including FastAPI, uvicorn, manim, and others.

## Step 5: Start the API Server

```bash
manim-api
```

Or with custom host/port:

```bash
manim-api --host 0.0.0.0 --port 8000
```

Or using Python directly:

```bash
python -m manim_generator.api_server
```

## Step 6: Test the API

The server should now be running on `http://localhost:8000`.

**Check if it's running:**
```bash
curl http://localhost:8000/health
```

**Generate a video:**
```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "script": "from manim import *\n\nclass MyScene(Scene):\n    def construct(self):\n        self.play(Write(Text(\"Hello World\")))"
  }'
```

## Troubleshooting

### If `manim-api` command is not found

Make sure your virtual environment is activated and the package is installed:
```bash
source .venv/bin/activate
pip install -e .
```

### If you get import errors

Ensure all dependencies are installed:
```bash
pip install -e .
```

### If ffmpeg is not found

Install ffmpeg on your system:
- **Linux:** `sudo apt-get install ffmpeg`
- **macOS:** `brew install ffmpeg`
- **Windows:** `choco install ffmpeg`

## Next Steps

- View API documentation at `http://localhost:8000/docs` (FastAPI auto-generated docs)
- Check the main README.md for more details on API endpoints
- See examples in the README.md API Usage section

