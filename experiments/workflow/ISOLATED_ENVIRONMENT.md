# Dedicated environment required for the remaining isolation milestone

The local deferred judge is validated for reviewed code. It is not a boundary
against deliberately hostile native code: a candidate C# plugin, Python import,
build hook or test currently executes with the supervisor's OS privileges. Merely
moving the evaluator to another process leaves its files and credentials exposed.

## Concrete deployment boundary

Use a dedicated disposable candidate VM and a separately controlled trusted judge
runtime. Candidate building, tests, Python catalog imports, modeling and Rhino all
run inside the candidate VM. Do not mount the host home, repository, judge files,
credentials or run journals into that VM. Disable shared folders and desktop data
sharing. Transfer an explicit reviewed source bundle inward and only frozen model,
image and trace artifacts outward. Candidate scripts do not choose host paths.

The host controller retains original source/evaluator hashes, budgets and ownership
records. It stops the candidate environment before the trusted judge measures a
copied model. The judge uses a separately provisioned known baseline and read-only
evaluator inputs. Both runtimes are disposable; a candidate-supplied model is still
untrusted input to the geometry parser. Logs and declared verdicts from the candidate
are observations, never a replacement for trusted measurements.

Provision the guest with a valid Rhino installation/license and a dedicated agent
login. Provider credentials must be scoped to the experiment and stay out of tracked
files, logs and artifact exports. Do not copy a personal VM or its user profile into
this role. No user credentials should be pasted into the conversation.

## Required evidence before calling isolation complete

1. From candidate native code and candidate Python, attempts to read judge inputs,
   alter controller journals, reach the trusted Rhino listener, and access host user
   files fail. Record actual denied operations, not a configuration-only assertion.
2. A deliberately altered candidate verdict cannot change the trusted verdict of a
   known good/bad calibration model. Export rejects unexpected paths and file types.
3. Stopping or crashing candidate Rhino, Python and the VM leaves the host controller
   and selected baseline intact. Restoring a clean guest snapshot preserves its
   recorded image and binary identity.
4. A fresh complete capability comparison passes through the isolated path with
   pinned evaluator inputs, separate modeling/judging identities, preserved failures,
   resource accounting and no host-level candidate execution.
5. Only after those checks should unattended acceptance/installation be enabled for
   this environment. The current reviewed desktop workflow remains supervised.

## Decision — 2026-09-10: a fresh Parallels VM on this Mac

The user chose a VM. Parallels Desktop and `prlctl` are installed on the host
(Apple Silicon, macOS 26). Constraints and plan:

- **Fresh guest only.** Create a new VM from an installer image; never clone, boot
  or mount the personal `Windows 11.pvm`. Shared folders, clipboard and drag-and-drop
  off. No host directory is ever mounted.
- **Roles.** Guest: candidate plugin build, candidate Python server, modeling agent
  (Codex CLI with its own login), Rhino 8 with a dedicated Rhino account. Host:
  controller, evaluators, journals, held-out bank, and the trusted judge, which is
  the host's dedicated Rhino on the released baseline. Its listener binds
  127.0.0.1 and is unreachable from the guest by construction; the denial test
  still has to record the failed attempt.
- **Network.** The guest needs the internet for Rhino licensing and the agent
  provider. It must not reach host services except the channel the host itself
  opens toward the guest (`prlctl exec` or host-initiated SSH). Record the policy and
  test it, do not assume it.
- **Snapshots.** One `clean-baseline` snapshot holds Rhino, the released plugin,
  Python, uv and the CLI, with identity recorded (snapshot id, Rhino version, plugin
  SHA and MVID). Every trial starts from a restore and ends with the guest stopped.
- **Transport.** Reviewed bundles go in; only model, image and trace files come out,
  size-capped, path-checked and hashed on arrival. Guest-declared verdicts are
  observations, never verdicts.
- **Licensing.** Verify whether one Rhino license permits host and guest to run at
  once. If not, the lifecycle runs them in sequence (the guest is stopped before
  judging anyway), or the user provides a second seat.
- **Lifecycle without a desktop.** Rhino must start from a command line with
  `mcpstart` in a startup script inside the guest. Prove this in the spike; it is
  what turns supervised tickets into unattended operations.

The steps M5a to M5d with their done criteria are in [CONTINUE.md](../CONTINUE.md).
Items a person must supply when reached: the guest OS installer, the guest's Rhino
login, the guest's Codex login, and any Parallels prompt. Nobody pastes a credential
into a session; the user enters them in the guest directly.

## Current external dependencies

No dedicated isolated Rhino environment has been provisioned yet; the decision
above (2026-09-10) settles what to provision. The existing stopped Windows 11 VM is
personal and untouched. Guest licensing, the two logins and the transfer route are
resolved during M5a and M5b, not assumed.
