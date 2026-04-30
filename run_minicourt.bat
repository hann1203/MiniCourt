@echo off
echo === Starting MiniCourt ===

echo Setting working directory...
cd /d C:\Users\hjb23\Documents\MiniCourt
echo Current directory:
cd
echo.

echo Activating venv...
call venv\Scripts\activate
echo venv activated.
echo.

echo Running app.py...
python app.py
echo.

echo If you see this, python exited.
pause


