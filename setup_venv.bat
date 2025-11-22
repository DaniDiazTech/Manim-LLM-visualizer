@echo off
REM Setup script for traditional venv approach (Windows)

echo Creating virtual environment...
python -m venv .venv

echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo Upgrading pip...
python -m pip install --upgrade pip

echo Installing package and dependencies...
pip install -e .

echo.
echo Setup complete!
echo.
echo To activate the virtual environment in the future, run:
echo   .venv\Scripts\activate
echo.
echo To start the API server, run:
echo   manim-api
echo   # or
echo   python -m manim_generator.api_server
echo.

