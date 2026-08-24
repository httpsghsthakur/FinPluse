# Finpluse Agentic AI (ReAct)

Agents follow the Reasoning + Acting (ReAct) pattern.

## State Machine
`IDLE -> TRIGGERED -> REASONING -> ACTION_PENDING -> CONFIRMED -> EXECUTED`

All decisions generate a `reasoning_trace` for auditability.
