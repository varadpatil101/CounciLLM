# Offline AI Council — foundation

This is the first backend foundation for an entirely local, multi-model AI
Council. It has no cloud service, no LM Studio runtime dependency, and does not
launch any models yet.

## What it does now

- Serves an existing static HTML frontend unchanged from `frontend/`.
- Provides `GET /api/health` for the frontend or launcher to check that the
  local server is available.
- Provides `GET /api/models` to report whether the locally discovered GGUF
  files are present.
- Returns a clear `501 Not Implemented` response for future `/api/*` actions.

## Run it

1. Copy the existing HTML frontend project into `frontend/` (or change
   `frontend_dir` in `config/council.json`).
2. Run `python backend/server.py`.
3. Open `http://127.0.0.1:8765`.

The model paths in `config/council.json` are discovery-time paths on this PC,
not a portable-package design. The packaging step will replace them with paths
relative to the application folder and bundle an inference runtime such as
`llama-server`.

## Next implementation step

After the frontend is provided, map its actual request formats and replace the
`501` placeholder with one local inference-adapter endpoint. Keep the frontend
contract stable, then add model lifecycle management and routing.
