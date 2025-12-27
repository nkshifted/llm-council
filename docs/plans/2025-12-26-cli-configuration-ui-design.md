# CLI Configuration UI Design

## Overview

Add a settings modal accessible from the sidebar to configure CLI commands that power the LLM Council. Users can add, edit, delete, enable/disable CLIs, and select which CLI serves as chairman.

## Data Model & Storage

**File location:** `data/cli_config.json`

**Schema:**
```json
{
  "clis": [
    {
      "id": "gemini",
      "name": "Gemini",
      "command": "gemini",
      "args": [],
      "enabled": true
    },
    {
      "id": "claude",
      "name": "Claude",
      "command": "claude",
      "args": ["-p"],
      "enabled": true
    }
  ],
  "chairman_id": "gemini",
  "council_ids": ["gemini", "claude", "codex", "amp"]
}
```

**Field definitions:**
- `id`: Unique identifier (auto-generated for new CLIs)
- `name`: Display name shown in UI and Stage tabs
- `command`: CLI executable name
- `args`: Array of arguments before the prompt
- `enabled`: Whether this CLI participates in the council
- `chairman_id`: Which CLI does Stage 3 synthesis
- `council_ids`: Order of CLIs (for consistent Response A/B/C labeling)

**Fallback:** If config file doesn't exist, backend creates it with defaults (gemini, claude, codex, amp).

## Backend API

**New endpoints:**

```
GET  /api/config
     Returns the full CLI config JSON

PUT  /api/config
     Saves the full CLI config JSON
     Body: { clis: [...], chairman_id: "...", council_ids: [...] }
     Validates: at least one enabled CLI, chairman must be enabled

POST /api/config/test-cli
     Tests a single CLI with a simple prompt
     Body: { command: "gemini", args: [] }
     Timeout: 30 seconds
     Returns: { success: true, response: "..." }
          or: { success: false, error: "..." }
```

**New file:** `backend/cli_config.py`
- `load_config()` - Read from JSON, return defaults if missing
- `save_config(config)` - Write to JSON
- `get_active_clis()` - Returns enabled CLIs in council order
- `get_chairman()` - Returns chairman CLI config

**Changes to existing files:**
- `cli_adapter.py` - Load configs dynamically instead of hardcoded dict
- `council.py` - Get council/chairman from cli_config
- `config.py` - Remove COUNCIL_MODELS and CHAIRMAN_MODEL constants

## Frontend Components

**New components:**

`components/SettingsModal.jsx`
- Modal overlay (500px max-width, centered, backdrop)
- Header: "Settings" title, X close button
- Accordion list of CLIs:
  - Collapsed: CLI name, enabled toggle, expand arrow
  - Expanded: name input, command input, args input, Test button, Delete button
- "Add CLI" button (new CLI auto-expands)
- Chairman dropdown (only enabled CLIs)
- Footer: Cancel, Save buttons

`components/SettingsModal.css`
- Modal and backdrop styling
- Accordion expand/collapse animation

**Changes to existing files:**
- `Sidebar.jsx` - Add gear icon next to title
- `App.jsx` - Settings state, fetch config, render modal
- `api.js` - Add getConfig, saveConfig, testCli functions

## Validation Rules

- Name and command are required
- Cannot disable the chairman (toggle disabled with tooltip)
- Cannot delete the chairman
- Cannot delete the last remaining CLI
- Must have at least one enabled CLI

## Test Button UX

- Click: Show spinner + "Testing..."
- Success (within 30s): Green checkmark + truncated response
- Timeout: Red error "CLI timed out after 30 seconds"
- Error: Red error message (e.g., "CLI not found")

## Unsaved Changes

- Track dirty state when any field changes
- Warn on close/cancel if unsaved changes exist
- Clear dirty state after successful save

## Implementation Tasks

### Backend

1. Create `backend/cli_config.py` with config schema and `load_config()` / `save_config()` functions
2. Add `get_active_clis()` and `get_chairman()` helper functions to `cli_config.py`
3. Add `GET /api/config` endpoint to `main.py`
4. Add `PUT /api/config` endpoint to `main.py` with validation
5. Add `POST /api/config/test-cli` endpoint with 30s timeout
6. Update `cli_adapter.py` to load CLI configs dynamically from `cli_config.py`
7. Update `council.py` to get council models and chairman from `cli_config.py`
8. Remove `COUNCIL_MODELS` and `CHAIRMAN_MODEL` from `config.py`

### Frontend

9. Add `getConfig()`, `saveConfig()`, `testCli()` to `api.js`
10. Create basic `SettingsModal.jsx` shell - modal overlay, header, close button, footer with Save/Cancel
11. Add accordion component structure for CLI list in `SettingsModal.jsx`
12. Add CLI form fields (name, command, args inputs) inside accordion
13. Add enable/disable toggle with chairman protection logic
14. Add Delete button with validation (prevent deleting chairman or last CLI)
15. Add "Add CLI" button that creates new entry and auto-expands
16. Add chairman dropdown (filtered to enabled CLIs only)
17. Add Test button with loading spinner, success/error display, 30s timeout
18. Add unsaved changes detection and warning on close
19. Create `SettingsModal.css` with modal and accordion styling
20. Update `Sidebar.jsx` - add gear icon button next to title
21. Update `App.jsx` - add settings state, fetch config, render modal

### Testing

22. Add tests for `cli_config.py` (load, save, defaults, helpers)
23. Add tests for new API endpoints (GET, PUT, test-cli)
24. Manual end-to-end test
