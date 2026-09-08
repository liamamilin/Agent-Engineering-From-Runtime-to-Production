# Protocols: Where MCP and Agent-to-Agent Standards Fit

Protocols are taught as interoperability mechanisms, not as the definition of Agent architecture.

## MCP

Teach MCP as a standardized host/client/server mechanism for exposing context and capabilities such as resources, prompts, and tools to an LLM application.

Key course point:

> MCP primarily standardizes **Agent/application ↔ capability/context provider** integration.

It belongs near tool ecosystems, external context, permissions, and capability negotiation.

Do not teach MCP as synonymous with multi-agent communication.

## Agent-to-Agent Protocols

Teach A2A-style protocols as mechanisms for independent agent systems to discover capabilities, exchange task-related messages/artifacts, and coordinate without sharing all internal state.

Key course point:

> Agent-to-agent protocols primarily standardize **Agent system ↔ Agent system** interoperability.

## Comparison

| Concern | Tool API | MCP | A2A-style protocol |
|---|---|---|---|
| Main relationship | runtime -> function/service | host/runtime -> capability/context server | agent system -> agent system |
| Typical abstraction | function/action | resources/prompts/tools/session capabilities | tasks/messages/artifacts/capabilities |
| Internal state sharing required | no | no | no |
| Multi-agent by itself | no | no | supports inter-agent interaction |

## Versioning Rule

These standards evolve. Course prose should teach stable architectural concepts. Version-specific labs must record the protocol revision used and should be revalidated before release.
