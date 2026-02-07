# EasySchedule

Lightweight course scheduling web app with streaming assistant support.

## Language
- Chinese: [README](./README.md)
- English: [README_EN](./README_EN.md)

## Project Structure
Backend: src/src/backend/; Frontend: src/src/frontend/; Docs: docs/

## Quick Start
pip install -r requirements.txt && python -m uvicorn backend.main:app --host 0.0.0.0 --port 9001 --reload

## Source Directory
- Unified source entry: [src](./src)

## Development Status
- This repository is maintained for open-source collaboration.
- Progress is tracked via commits and issues.

## Migration Note
- Core code has been physically moved to `src/backend` and `src/frontend`.
- Root `backend` / `frontend` are compatibility symlinks so existing run commands still work.
