# Aphelocoma v0.3.0 release

Two things live here: draft GitHub release notes to publish once the tag exists, and the advisor's
step-by-step checklist for actually shipping this release. Nothing in this document pushes, merges,
tags, or publishes anything — those steps stay the advisor's, as decided for this task.

## Draft GitHub release notes

Use this as the body of the `v0.3.0` GitHub release. It is written for someone deciding whether to
install or upgrade, not for someone reading the changelog line by line — see `CHANGELOG.md` for the
complete, itemized history.

---

### Aphelocoma v0.3.0

Aphelocoma is now Hamilton, and only Hamilton: a file-based agent crew for building software with
Claude Code or Codex. This release removes the earlier second-brain/context product entirely and makes
the `aph` command line, Hamilton's shared skill definition, and the Claude/Codex crew generators the
whole product.

**Install:**

```bash
curl -fsSL https://raw.githubusercontent.com/PhyoYazar/aphelocoma/main/install.sh | bash
```

**Deploy a host and start a build:**

```bash
aph deploy claude   # or: aph deploy codex
aph doctor
```

Then open Claude Code or Codex in the project you want to build and run `/aph-hamilton`.

**What's new**

- A small, dependency-free `aph` CLI (`deploy`, `undeploy`, `doctor`, `status`, `update`, `uninstall`,
  `version`, `help`) with a transactional installer: a failed install or update leaves the previous
  working tool in place instead of a half-applied one.
- `aph status` — a Hamilton progress board. Run it any time to see project name, phase, and one line
  per task; add `--write` to regenerate the committable `.aphelocoma/STATUS.md` snapshot, so a
  project's progress is readable without running anything.
- Manifest-owned deployment to Claude Code and Codex: exact generated files and digests are tracked, a
  pre-existing file at a generated path is backed up before it's replaced, and `undeploy` only ever
  removes what it owns.
- Versioned Hamilton project state, with an explicit, backed-up migration path for existing v0.2
  Hamilton projects (`migrate.py check` / `apply`).

**Breaking changes**

- The former second-brain/context runtime, Cursor deployment, project registry, and
  sync/journal/capture/view features are gone, with no automatic replacement. Existing legacy data
  under `~/.aphelocoma/data` is left untouched but is no longer read by anything in this release.
- Claude Code and Codex are the only supported deployment targets.

**If you're upgrading from v0.2:** read `docs/migration-v0.3.md` first, in particular the section
"If you have the old install command saved" — the old `v0.2.0`-pinned install command does not fail
cleanly for every user once this tag exists, and that section explains what you'll actually see and
what to run instead.

**Requirements:** Python 3.9 or newer and Git, on macOS or GNU/Linux.

---

## Advisor's release checklist

This assumes CP4 (final acceptance) has already been given and every task through T15 is `done`. Each
step below names who does it. Steps 1–8 are sequential; do not skip ahead when a step says to stop.

1. **Push `develop`. (Advisor. Crew agents never run this.)**
   Push the local `develop` branch to `origin/develop`. As of this writing all 23 commits that make up
   v0.3 are local only — the last push to `origin/develop` predates this work, so this is a real push,
   not a no-op. This push is what triggers the first hosted CI run; nothing before this step has run on
   GitHub's runners.

2. **Watch CI. (Advisor.)**
   Open the GitHub Actions run for that push. It runs four legs: `ubuntu-latest` and `macos-latest`,
   each on Python `3.9` and the current `3.x`. Each leg validates the Bash installer syntax, runs the
   full test suite, runs the independent Hamilton validator against the repository, re-runs the
   package/release inventory tests, and smoke-tests an isolated installation. Wait for all four to
   finish.

3. **If any leg is red: fix it there, don't route around it. (Advisor + whichever crew role owns the
   failure.)**
   Everything in this codebase has so far been verified only on macOS with Python `3.14.4`; a red
   Linux leg or a red Python `3.9` leg is exactly the kind of gap CI exists to catch, not a flake to
   dismiss. Diagnose the actual failure from the job log, fix it on `develop`, push again, and return
   to step 2. Do not weaken, skip, or `continue-on-error` a check to force a green run — that would
   turn "CI passed" back into an unverified claim.

4. **Once CI is green on all four legs, give `docs/release-readiness-v0.3.md` its second pass. (Advisor
   or technical-writer, as its own step — do not fold this into step 2 or step 5.)**
   That document's status line currently reads `READY FOR CI — NOT YET READY TO RELEASE` precisely
   because CI had not run when it was written. Now that it has, update it: replace the
   "Hosted runner execution: pending first CI run" line with the actual green result (run URL and date
   are enough), and update the status line to reflect that Linux and Python `3.9` are now verified, not
   just declared as policy. **Read `tests/test_release_smoke.py`'s
   `test_release_metadata_and_report_are_final` before editing this document by hand** — it currently
   asserts the literal substrings `Status: READY`, `` Release version: `0.3.0` ``, and
   `Hosted runner execution: pending first CI run` are present in the file. Rewording those exact
   strings (for example, replacing "pending first CI run" with a pass date) will fail that test on the
   next CI run unless the test itself is updated in the same change. That test update is a separate,
   deliberate task — not something to slip into this pass silently — because it removes a check that
   currently keeps this document honest.

5. **Merge `develop` to `main`. (Advisor.)**
   Standard merge or fast-forward, whichever this repository normally uses. **Merging alone does not
   yet break the old v0.2.0 install command** — verified locally: the published
   `v0.2.0`-pinned installer script picks the highest-versioned Git *tag* it finds, not whatever `main`
   points at, so until a `v0.3.0` tag exists it keeps resolving to `v0.2.0` regardless of what's on
   `main`.

6. **Tag `main` at the merge commit as `v0.3.0` and push the tag. (Advisor.)**
   This is the step that actually changes behavior for anyone with the old install command saved —
   verified locally, not inferred: once the `v0.3.0` tag exists, the old script's tag lookup resolves
   to it instead of `v0.2.0`, and depending on what's already on that person's machine they either see
   `Error: Unknown command 'setup'`, see `Error: git fetch failed`, or (for a returning v0.2 user with
   real prior data) see no error at all while `aph doctor` later reports an unmanaged install. All
   three are documented in `docs/migration-v0.3.md`. Consider this the moment to point existing v0.2
   users at that document, since after this step their saved command stops behaving like v0.2.

7. **Publish the GitHub release for the `v0.3.0` tag. (Advisor.)**
   Use the draft notes above (edit freely; they're a starting point, not a script). A pushed tag alone
   does not create a release page — this step is what makes it visible on the repository's Releases
   tab and what most users will actually read.

8. **Verify end to end. (Advisor.)**
   From a machine or a genuinely clean `$HOME` (not a directory that already has `~/.aphelocoma`), run
   the current install command from the README, deploy a host, and run `aph doctor`. Confirm it reports
   `0.3.0` and healthy. This closes the loop started at step 1: CI proved the matrix passes in
   isolation, this step proves the real published artifact installs the way the docs say it does.
