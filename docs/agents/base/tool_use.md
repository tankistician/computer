# Tool Use Discipline

## Before calling a tool
- Confirm you understand: inputs, outputs, and side effects.
- If tool is destructive or costly, request approval or simulate first.

## When calling a tool
- Provide the smallest valid input.
- Use structured inputs that match the tool schema exactly.
- Prefer read-only tools unless the task explicitly requires writes.

## After calling a tool
- Validate the output:
  - Is it complete?
  - Does it match expected schema?
  - Are there errors/warnings?
- If errors: summarize error + propose fix + retry with a minimal change.

## Anti-patterns (avoid)
- Hallucinating tool names or outputs.
- Retrying the same failing call without changing inputs.
- Embedding secrets in tool inputs or logs.
