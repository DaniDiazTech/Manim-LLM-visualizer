#!/bin/bash
# Test script for the Manim Video Generator API

# Test the /generate endpoint (LLM-based generation)
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

echo ""

