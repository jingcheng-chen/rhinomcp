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

## Current external dependencies

No dedicated isolated Rhino environment has been provisioned. The existing stopped
Windows 11 VM is personal and untouched. The user has been asked whether to provision
a separate disposable VM or use an existing dedicated machine. Claude Code on the
host is also signed out. These are pending environment choices/access, not passing
milestones. VM and guest licensing, authentication and the host/guest transfer route
must be resolved before this design can be tested end to end.
