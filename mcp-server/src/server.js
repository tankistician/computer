const express = require('express');
const fs = require('fs');
const path = require('path');

const app = express();
app.use(express.json());

const toolsDir = path.join(__dirname, 'tools');
const tools = {};

// Dynamically load JS tool modules from src/tools
if (fs.existsSync(toolsDir)) {
  fs.readdirSync(toolsDir).forEach((f) => {
    if (f.endsWith('.js')) {
      const name = f.replace('.js', '');
      try {
        tools[name] = require(path.join(toolsDir, f));
        console.log(`Loaded tool: ${name}`);
      } catch (err) {
        console.error(`Failed to load tool ${name}:`, err.message);
      }
    }
  });
}

app.post('/tool', async (req, res) => {
  const body = req.body || {};
  const toolName = body.tool;
  const input = body.input || {};

  if (!toolName) return res.status(400).json({ ok: false, error: 'missing tool field' });
  const tool = tools[toolName];
  if (!tool || typeof tool.handle !== 'function') return res.status(404).json({ ok: false, error: `tool not found: ${toolName}` });

  try {
    const output = await tool.handle(input);
    return res.json({ ok: true, tool: toolName, output });
  } catch (err) {
    console.error(`Tool ${toolName} error:`, err);
    return res.status(500).json({ ok: false, error: String(err.message || err) });
  }
});

const port = process.env.PORT || 3000;
app.listen(port, () => {
  console.log(`MCP example server listening on http://localhost:${port}`);
  console.log('Available tools:', Object.keys(tools));
});
