---
name: terzya-node-session-bootstrap
description: "Trigger: fresh session, session start, Terzya Node. Build one bounded, read-only Studio checkpoint for the active profile."
license: Apache-2.0
metadata:
  author: Terzya
  version: "1.3"
---

## Activation Contract

Run once per genuinely fresh session for the active profile, not on every response. Reuse the checkpoint already present in the conversation. Run only for the default profile unless another profile explicitly loads this skill.

## Hard Rules

- While building the checkpoint, use read-only Studio evidence and keep every result sanitized and bounded.
- While building the checkpoint, never use polling or loops; restart, update, pairing/connect/disconnect, command execution, terminal/file transfer, or POST/PUT/PATCH/DELETE.
- While building the checkpoint, never read message or context content, expose secrets, or persist the checkpoint outside the conversation.
- A user read-only constraint includes bookkeeping and lifecycle writes: do not call `mem_session_start`, memory save/update/session-summary operations, or any equivalent state-creating tool. Read-only memory review or context lookup remains allowed only when independently required.
- Use the timestamp returned by Studio; never call terminal only to obtain the clock.
- Runtime owns active/running liveness. Native session rows provide persisted recency and lifecycle metadata only.
- Treat discovery, pairing, connection, and verified capability as distinct states; never infer one from another.
- After the checkpoint is emitted, ordinary work follows its own skills and user authorization; this skill imposes no continuing tool restriction.

## Decision Gates

| Evidence | State |
| --- | --- |
| All required reads succeed | `ready`; use `attention` only for a current component fault or an equivalent-owner contradiction |
| Native Hermes sessions are unavailable | `degraded`; do not substitute Studio bridge sessions as if they were Telegram/CLI sessions |
| Timeout, 401, or tools are unavailable | `degraded`; state the missing evidence and continue tasks that do not depend on it |
| Runtime version details unavailable | Continue; runtime versions are optional |

## Execution Steps

1. Record node and active profile. Derive UTC evidence time from the required Studio response metadata or HTTP `Date` header, never a separate clock command.
2. Make only these minimal reads: `GET /health`; `GET /api/studio/performance/runtime`; `GET /api/studio/sessions/hermes?limit=5`; and `peer_connections` without scanning.
3. Report active/running work from Studio runtime. Use native Hermes rows only for recent-session metadata; `ended_at: null` means unclosed metadata, not live execution. Bound session output to five entries and peer output to counts plus named connection states.
4. Query Studio bridge `sessions_list` only when its separate run population is materially relevant; label it `Studio bridge sessions` and never compare its count directly with native Telegram/CLI sessions.
5. Identify contradictions only between equivalent owners, populations, semantics, and evidence times, without repairing them. Do not mark `attention` solely because unclosed native rows differ from runtime active counts. Produce the checkpoint once and reuse it for the rest of the conversation.

## Output Contract

Return one sanitized, bounded checkpoint containing: node, profile, evidence time, health, runtime, active work, peer summary, contradictions, and state. Mark evidence sources and unknown fields. Never claim verified capability without direct evidence. Inspect the executed tool sequence before claiming the checkpoint was entirely read-only; disclose any state-changing call instead of making that claim.

## References

None.
