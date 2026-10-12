# How to run

From the `api_practice` folder, open three PowerShell terminals and activate the virtual environment in each:

```powershell
cd api_practice; .venv\Scripts\Activate.ps1
```

Then run one command per terminal:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000              # API, docs at /docs
python -m http.server 5500 --bind 127.0.0.1 --directory frontend        # open http://127.0.0.1:5500
python cli.py check all                                                 # or: steps, show 6, burst, seed, ws
```

First-time setup (creating `.venv`, installing dependencies, building the C++ library) is in [README.md](README.md#quick-start).
