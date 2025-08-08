@echo off
echo Setting up AI Code Reviewer...

cd backend
python -m venv venv
call venv\Scripts\activate
pip install -r requirements.txt


echo Setup complete!