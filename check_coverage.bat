@echo off
coverage run -m pytest tests
if %ERRORLEVEL% neq 0 (
    echo Error: pytest tests failed.
    exit /b %ERRORLEVEL%
)

coverage html
if %ERRORLEVEL% neq 0 (
    echo Error: Failed to generate HTML coverage report.
    exit /b %ERRORLEVEL%
)

start "" htmlcov\index.html
