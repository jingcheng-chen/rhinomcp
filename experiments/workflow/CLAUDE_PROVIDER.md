# Claude Code adapter

`experiments.claude_provider` integrates with the existing runner and native pilot.
Select `--provider claude --model MODEL --reasoning-effort medium` on the pilot.
The optional adapter requires Python 3.11+ and an authenticated local Claude CLI.
It translates the existing explicit gateway configuration, uses a fresh directory,
disables built-in tools, restricts MCP servers and allowed tools, disables hooks,
plugins/skills and browser integration, and denies permission prompts. This is a
restricted agent interface, not an OS boundary against malicious native plugins.

Raw Claude stream events remain in `provider-events.jsonl`. Normalized events preserve
unique MCP call IDs, arguments, errors, unfinished calls and available usage for the
existing workflow audit. Missing usage is unknown. Structured output must validate
against the role schema; completion claims never override the Rhino evaluator.
Unexpected tools, child-agent records or conflicting IDs fail the session. Timeouts
terminate its process group and retain available evidence. No provider conversation
is resumed automatically. Binary comparisons currently remain Codex-only until the
Claude adapter is live-validated and environment comparability is established.

Six tests cover explicit gateway translation, signed-out refusal, restricted flags,
structured results, error/unfinished telemetry and unknown-provider rejection.
## Live native modeling validation — 2026-09-09

Local sign-in is confirmed. Three fresh sonnet/medium sessions report model
`claude-sonnet-5`; initialization exposes exactly the 13 approved MCP tools plus
StructuredOutput, with the gateway connected and dontAsk mode. All 20 calls complete
without errors, normalized/provider and gateway counts agree, and each session
preserves the document fingerprint. Total modeling time: 95.84 seconds.

Independent saved-file checks pass the box and through-hole solid. The reserved
trimmed patch fails its world pose despite a completion claim. Its topology, hole
and area pass. Claude rotates about the object center, then applies the requested
translation without compensating for the world-origin pivot. The measured local
shift [0, -2.5765358565, 11.6220021979] matches this construction exactly. The public
modify_object description omits the bounding-box-center pivot implemented in C#.
This is a workflow-guidance observation, not a planar-region topology defect.

See `claude-validation-results.json` and the three actual roadmap screenshots.
Local run: `runs/workflow-baseline-20260909-084123-58e4041b`; every original source,
model, raw event, screenshot and preservation check is retained with hashes.
Native modeling interoperability is now live-validated, including detection of a
failed agent result. One run per task is not a comparison between providers, a
broad success guarantee, or validation of Claude binary-comparison orchestration.
No production source change was made. Next controlled experiment: test explicit
rotation-pivot guidance against unchanged posed tasks before adopting wording.

Implementation references: the locally installed `claude --help`, the official
[CLI reference](https://code.claude.com/docs/en/cli-usage),
[streaming output](https://code.claude.com/docs/en/agent-sdk/streaming-output), and
[structured output](https://code.claude.com/docs/en/agent-sdk/structured-outputs).
