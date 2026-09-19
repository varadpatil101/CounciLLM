# CounciLLM

CounciLLM is a fully local multi-model council backed by the LM Studio llama.cpp runtime that is already installed on this machine.

Project layout:

- `frontend/` contains the existing HTML UI, preserved and wired to the backend API.
- `backend/` contains the offline server and local model launcher.
- `config/council.json` lists the discovered local GGUF files and the LM Studio runtime settings.

Used local models:

- `qwen3-router` for routing and intent classification.
- `qwen3-general` for general responses.
- `granite-coding` for coding and implementation tasks.
- `qwen3-vision` for vision-capable requests, with its paired `mmproj` file.

What the backend does:

- Serves the frontend from the same local server.
- Exposes `GET /api/health`, `GET /api/models`, `GET /api/state`, and `POST /api/chat`.
- Starts `llama-server.exe` from the local LM Studio installation on demand.
- Routes requests automatically through the router model unless the UI asks for a specific role.

Run it:

```powershell
cd C:\Users\Varad\Documents\Codex\2026-08-28\referenced-chatgpt-conversation-this-is-an\CounciLLM
python backend\server.py
```

Then open:

```text
http://127.0.0.1:8765
```

Notes:

- This environment could not write directly to `Downloads`, so the project was created in the writable workspace instead.
- The project uses the local LM Studio `llama-server.exe` binaries already installed on the machine.

## Offline local authentication

CouncilLM uses an offline authentication gate stored only in the browser profile that opens `http://127.0.0.1:8780`.

- Account metadata is stored in IndexedDB. Passwords and recovery codes are never stored in plaintext.
- Password and recovery-code verifiers use the browser Web Crypto API with PBKDF2-SHA-256, unique random salts, and a high work factor.
- Each account has one recovery code, shown once during setup. If both the password and recovery code are lost, the account cannot be recovered.
- Reloading the page requires a new local login. The account is not synchronized to other browsers or devices.
- Clearing browser site data removes the local credentials and recovery verifier. Deleting the account also clears CouncilLM workspace state, attachments, generated artifacts, and CouncilLM-created projects; it does not remove models, source code, or unrelated browser data.

This is an application lock for the local browser UI. The bundled backend remains intentionally loopback-only (`127.0.0.1`) and is not an OS-level access-control service; anyone with direct access to the same Windows account and its local process/browser data is inside the device trust boundary.
