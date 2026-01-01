# MCP Server (Example)

This is a minimal example MCP-style tool server implemented with Node + Express.

Provided example tool:
- `echo` — returns the provided JSON input as `output.echoed`.

Run locally:

```powershell
cd mcp-server
npm install
npm start
```

Call the example tool:

```powershell
curl -X POST "http://localhost:3000/tool" -H "Content-Type: application/json" -d '{"tool":"echo","input":{"hello":"world"}}'
```

Expected response:

```json
{"ok":true,"tool":"echo","output":{"echoed":{"hello":"world"},"message":"echo tool received input"}}
```

Notes:
- This is intentionally tiny and synchronous for demo purposes.
- In production you should add input validation (use the JSON schemas in `src/schemas/`), authentication, logging, and process supervision.
