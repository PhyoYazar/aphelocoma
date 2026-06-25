# FOUNDATIONS — the Discovery checklist (read-only)

The leadership core walks these **six foundation topics** with the advisor during Discovery
(PROTOCOL §2, Phase 1), *before* Checkpoint 1. They are **advisory**: they shape the product
**direction** (CP1) and the **roadmap** (CP2) — they are *not* acceptance criteria that block a task
from `done`. Record the advisor's decisions in `.aphelocoma/state/brief.md` (`## Foundations`) and
reflect each one in `.aphelocoma/state/roadmap.md` as **addressed** (how) or **consciously deferred** (why).

- **New project:** ask the advisor where each foundation should land for v1.
- **Existing project:** run this *after* the codebase survey and assess the **current state** of each
  (how does it deploy today? is it observable? accessible?), surfacing gaps as roadmap candidates.

Unknowns become questions to the advisor — never fabricated scope.

## The six topics

1. **Deploy** — Where and how does this ship? Target platform/host, the tech/runtime, and the path to
   production (manual, script, CI/CD). _Owner when active: `devops-engineer` / `cloud-engineer`._
2. **Fault-tolerance** — How does it behave when things fail? Graceful degradation, retries/timeouts,
   error handling, no single point of failure. _Owner when active: `sre`._
3. **Security** — What's the threat model? Authn/authz, secrets handling, input validation, data
   protection. _Owner when active: `security-engineer` / `appsec-engineer`._
4. **UX** — What's the experience bar? Key user flows, empty/error/loading states, overall feel.
   _Owner when active: `uiux-designer`._
5. **Observability** — How will we see what it's doing in production? Logging, metrics, tracing,
   alerting. _Owner when active: `sre`._
6. **Accessibility** — Who must be able to use it? WCAG target, keyboard navigation, screen-reader
   support, color contrast. _Owner when active: `uiux-designer`._

When a foundation's owner role is not active at the chosen crew size, the `cto` covers it (PROTOCOL §7).

## TDD (a default, not a foresight topic)

TDD is **on by default** for every project. The advisor may turn it **off** at kickoff for a throwaway
(e.g. a PoC) by saying so. Record the choice in `brief.md` (`## TDD`). When **on**, every task's spec
acceptance criteria (PROTOCOL §4) require tests written first, and QA verifies them at Review before
the task is `done`. When **off**, that requirement is skipped.
