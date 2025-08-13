# Power Apps + Power BI + Railway (FastAPI) + Groq Starter

This starter kit lets you drop a chatbot UI (Power Apps) into a Power BI report that calls a FastAPI backend on Railway, which forwards prompts to Groq and returns responses.

## Architecture
Power BI → Power Apps visual → Power Apps App → (HTTP) → Railway (FastAPI) → Groq (LLM) → Response → Power Apps → Shown in Power BI

## Quick Deploy (Railway)
1) Create a new Railway project.
2) Upload these files or connect to a Git repo that contains them.
3) Set environment variable: `GROQ_API_KEY` (from console → Variables).
4) Deploy. When live, note your public URL, e.g. `https://<project>.up.railway.app`.
5) Test:
   ```bash
   curl https://<project>.up.railway.app/health
   curl -X POST https://<project>.up.railway.app/chat -H "content-type: application/json" -d '{"prompt":"Say hello"}'
   ```

## Power Apps (Canvas) Setup
1) Create a Canvas app with:
   - **TextInput**: `tiPrompt`
   - **Button**: `btnSend`
   - **Label**: `lblReply` (Multi-line)
2) If using **Power Automate** (recommended for easier auth/rate limiting):
   - Import the provided flow (see `powerautomate/flow-definition.json`), or build manually:
     - Trigger: **PowerApps (V2)** with one input: `Prompt` (Text).
     - Action: **HTTP** (POST) to `https://<project>.up.railway.app/chat`
       - Headers: `Content-Type: application/json`
       - Body: `{"prompt": "@{triggerBody()['text']}"}`
     - Action: **Response**: return `@{body('HTTP')}`
   - In Power Apps `btnSend.OnSelect`:
     ```powerfx
     Set(
       varReply,
       YourFlowName.Run(tiPrompt.Text)
     );
     // If the flow returns JSON text, you may need to parse:
     Set(
       varParsed,
       If(
         IsBlankValue(varReply),
         Blank(),
         If(IsType(varReply, Record), varReply, JSON(varReply, JSONFormat.IgnoreUnsupportedTypes))
       )
     );
     // Easiest: return a record with field 'text' from Flow. Then:
     Set(lblReply.Text, varReply.text)
     ```

3) If calling **backend directly from Power Apps** (Premium Custom Connector):
   - Import the **Custom Connector** using `powerapps-connector/openapi.json`.
   - Create a connector instance pointing to your Railway base URL.
   - Then use:
     ```powerfx
     Set(
       varReply,
       GroqBridge.Chat(
         { prompt: tiPrompt.Text }
       )
     );
     Set(lblReply.Text, varReply.text)
     ```

## Power BI Integration
1) Open your Power BI report → **Insert** → **Power Apps** visual.
2) Add at least one field (can be a dummy) to the visual's data well.
3) Choose the Canvas app you created.
4) Publish report to the Power BI Service. Ensure the Power Apps/Automate trials or licenses are active for consumers.

## Security Notes
- Do not store the Groq key in Power Apps. Keep it only in Railway env vars.
- In production, restrict CORS origins and add API auth (e.g., a simple header token or JWT) to `/chat`.
- Rate limit the endpoint to prevent abuse.
- Log and monitor errors.

## Licenses
- **Power BI**: Pro (for sharing) or Premium per user/capacity.
- **Power Apps**: Premium (30-day trial ok) for custom connector or calling flows.
- **Power Automate**: Premium (trial ok) for the HTTP action.
- **Railway**: Free tier is fine for POC; consider upgrades for uptime.
- **Groq**: Free (subject to fair use / changes).

## Troubleshooting
- 401/403 from Groq: check `GROQ_API_KEY` in Railway.
- Power Apps connector errors: confirm the correct base URL and that `/health` works.
- CORS issues: adjust `allow_origins` in `app.py`.
- Large responses: bump `max_tokens` in request body.