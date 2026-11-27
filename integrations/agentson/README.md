# AgentSON Integration

Planned adapter for recording boot, inference and agent lifecycle events in a versioned AgentSON-compatible format.

Initial event candidates:
- `system.boot.started`
- `system.boot.completed`
- `inference.model.loaded`
- `inference.request.started`
- `inference.request.completed`
- `agent.execution.started`
- `agent.tool.invoked`
- `agent.execution.completed`
- `agent.execution.failed`

These are design candidates, not a published schema. Validate event names and fields against the current AgentSON specification before implementation.
