# Modeling resource and interruption policy

New binary comparisons create a persistent resource ledger before dispatch. The
contract may supply positive limits for sessions, observed tool attempts and modeling
seconds. Defaults cover the fixed AB/BA schedule, allowing one over-budget rejection
per session and ten seconds of session overhead beyond its configured timeout.

Before a session or required arm switch, reserve its allowance. After the session,
account for the full audited attempt count and measured time. Never clamp overshoots
or replace a failed run with a cheaper retry. Insufficient remaining allowance stops
new dispatch. An interruption leaves a pending reservation and blocks further work;
the comparator's existing recovery path restores baseline without replaying modeling.
An observed total above the frozen run limit is recorded and prevents a completed comparison claim. A session exceeding its reservation is accounted at its actual cost; the remaining total determines whether another session can start.

These are sequential admission limits, not a provider billing cap. The existing
session timeout and tool gateway enforce the per-session boundary. Rejected attempts,
startup/cleanup overhead and API token usage can exceed a reservation; report actual
usage and stop further sessions. No dollar or token ceiling is claimed. Lifecycle
restoration remains allowed even after modeling resources are exhausted.

Eight focused tests cover interruption, double accounting, replay, overshoot and
invalid amounts. Live integration will be exercised by the prospective planar-region
comparison. This does not yet implement a multi-candidate autonomous search budget.
