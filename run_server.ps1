# PowerShell script to run the child safety backend server
	Set-Location "G:\VigilancePilot"
	.\.venv\Scripts\Activate.ps1
	Set-Location "backend"
	python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
