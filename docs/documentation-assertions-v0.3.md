# v0.3 documentation assertions

This is the source-of-truth checklist for behavioral claims in `README.md`,
`docs/migration-v0.3.md`, `CHANGELOG.md`, and
`skills/aph-hamilton/references/ABOUT.md`. A claim is publishable only when it maps to an automated
test below or is labeled as an explicit support policy. Test IDs use
`module.Class.test_method`.

Checked items were reverified on 2026-07-26 against the full 225-test suite, CLI help, doctor JSON,
the Hamilton validator run against the repository bundle, and a local-link/test-ID audit.

## Product and command surface

- [x] **DOC-001 — Hamilton-only product.** The installed runtime contains the Hamilton skill,
  Hamilton crew generators, and the `aph` runtime; retired context and private-export assets are not
  packaged.
  Tests: `test_package_inventory.HamiltonPackageInventoryTests.test_activation_installs_only_the_explicit_hamilton_runtime`,
  `test_package_inventory.HamiltonPackageInventoryTests.test_skills_tree_contains_only_hamilton`,
  `test_package_inventory.HamiltonPackageInventoryTests.test_removed_runtime_assets_are_absent_from_shipped_paths`,
  `test_package_inventory.HamiltonPackageInventoryTests.test_context_runtime_and_private_exports_are_not_packaged`,
  `test_generators.GeneratorTests.test_claude_generator_writes_all_27_agents`,
  `test_generators.GeneratorTests.test_codex_generator_writes_parseable_named_roles_and_preserves_config`.
- [x] **DOC-002 — Supported commands.** The public CLI is `deploy`, `undeploy`, `doctor`, `status`,
  `update`, `uninstall`, `version`, and `help`; unsupported or incomplete commands fail with
  remediation.
  Tests: `test_cli.CliSubprocessTests.test_help_exposes_only_hamilton_commands`,
  `test_cli.CliSubprocessTests.test_unknown_and_incomplete_commands_are_actionable_failures`,
  `test_cli.CliSubprocessTests.test_lifecycle_commands_are_implemented_not_placeholders`.
- [x] **DOC-003 — First-class hosts.** Claude Code and Codex are the only deployment targets.
  Tests: `test_package_inventory.HamiltonPackageInventoryTests.test_supported_targets_are_claude_and_codex_only`,
  `test_cli.CliSubprocessTests.test_help_exposes_only_hamilton_commands`.
- [x] **DOC-004 — Install location and PATH behavior.** Installation activates the verified release
  at `$APHELOCOMA_ROOT/tool` (default `~/.aphelocoma/tool`) and uses one owned block in the first
  existing supported shell file (`.zshrc`, `.bashrc`, or `.bash_profile`); when none exists, the user
  adds the tool's `bin` directory manually.
  Tests: `test_lifecycle.InstallerEntrypointTests.test_installer_activates_verified_tool_without_context_setup`,
  `test_lifecycle.ActivationTests.test_manifest_owned_path_block_allows_repeated_update`,
  `test_lifecycle.PathMarkerTests.test_path_marker_is_idempotent_and_preserves_shell_configuration`.
- [x] **DOC-005 — Platform/runtime support.** Python 3.9 or newer is required. The supported
  installation platforms are current macOS and GNU/Linux with Bash and Git available to the
  download-based installer. This is an explicit v0.3 support policy; Python enforcement is covered by
  `test_doctor.DoctorChecksTests.test_current_checkout_passes_all_base_checks` and installer
  requirements are declared by `install.sh`.
- [x] **DOC-006 — CLI exit-status contract.** Supported help, version, healthy doctor, successful
  `status`, and successful lifecycle operations return `0`; actionable usage or health failures
  (including a missing or unsupported-version `status` target) return `1`; an unexpected internal
  failure returns `2` with remediation and no traceback.
  Tests: `test_cli.CliSubprocessTests.test_empty_command_and_help_option_show_help`,
  `test_cli.CliSubprocessTests.test_version_uses_the_checked_out_version_file`,
  `test_cli.CliSubprocessTests.test_healthy_doctor_has_human_and_json_contracts`,
  `test_cli.CliSubprocessTests.test_subcommand_help_is_successful`,
  `test_cli.CliSubprocessTests.test_lifecycle_commands_are_implemented_not_placeholders`,
  `test_cli.CliSubprocessTests.test_unknown_and_incomplete_commands_are_actionable_failures`,
  `test_cli.CliSubprocessTests.test_doctor_json_is_machine_readable_and_reports_missing_git`,
  `test_cli.CliStatusBoardTests.test_missing_project_state_is_an_actionable_failure`,
  `test_cli.CliStatusBoardTests.test_unsupported_version_refuses_in_both_output_forms`,
  `test_cli.CliInternalFailureTests.test_unexpected_failure_returns_two_without_traceback`,
  `test_cli.CliInternalFailureTests.test_status_internal_failure_returns_two_without_traceback`.
- [x] **DOC-007 — Hamilton skill command behavior.** Guided start asks whether the project is new or
  existing and what to build; the explicit `start` form is the fast path; `resume` validates and
  continues durable state, printing and writing the progress board at the top; `status` validates and
  reports, writing `.aphelocoma/STATUS.md` only when `--write` is passed; and `sync-agents` is the
  Claude-only per-project crew override that requires a session restart after regeneration. These are
  explicit workflow support policies defined by the corresponding `(no arguments)`, `start`,
  `resume`, `status`, and `sync-agents` sections of `skills/aph-hamilton/skill.md`.
- [x] **DOC-008 — Project records and single-writer boundary.** The shared Hamilton definition is
  installed read-only, product files live beside project-local `.aphelocoma/` state, the task board
  records current state, the event ledger is append-only history, and the orchestrator is the sole
  writer of both shared mutable records during parallel work. These are explicit workflow support
  policies defined by `skills/aph-hamilton/references/PROTOCOL.md` §0, §1, and §5 and by
  `skills/aph-hamilton/references/PARALLEL.md` “The one safety rule: a single writer for shared
  state.”
- [x] **DOC-009 — Transactional installer activation.** The installer stages and verifies a release
  before activation. An interrupted clean activation leaves no partial active tool or install
  manifest, and a failed installer upgrade restores the old tool.
  Tests: `test_lifecycle.InstallerEntrypointTests.test_installer_activates_verified_tool_without_context_setup`,
  `test_lifecycle.ActivationTests.test_interrupted_clean_install_leaves_no_partial_active_tool`,
  `test_lifecycle.InstallerEntrypointTests.test_installer_failure_after_activation_rolls_back_old_tool`.

## Deployment ownership and recovery

- [x] **DOC-010 — Manifest ownership.** Deployments record exact generated artifacts, digests,
  collision backups, and managed configuration blocks; repeated deploys are idempotent.
  Tests: `test_deploy.DeploymentTests.test_claude_deploy_is_hamilton_only_idempotent_and_reversible`,
  `test_deploy.DeploymentTests.test_codex_deploy_preserves_user_config_and_undeploys_only_managed_block`,
  `test_deploy.ManifestValidationTests.test_collision_records_are_schema_validated`.
- [x] **DOC-011 — Host configuration preservation.** Deploy does not replace user-wide Claude or
  Codex configuration. Codex receives one marker-delimited block; generated Claude/Codex roles and
  the Hamilton skill are standalone files.
  Tests: `test_deploy.DeploymentTests.test_claude_deploy_is_hamilton_only_idempotent_and_reversible`,
  `test_deploy.DeploymentTests.test_codex_deploy_preserves_user_config_and_undeploys_only_managed_block`.
- [x] **DOC-012 — Collision recovery.** A pre-existing file at a generated path is backed up before
  replacement and restored by a clean undeploy.
  Test: `test_deploy.DeploymentTests.test_collision_is_backed_up_and_restored_on_undeploy`.
- [x] **DOC-013 — Transactional deploy.** Generation completes in staging, and a failed deployment
  rolls back host changes instead of leaving a partial deployment.
  Tests: `test_deploy.DeploymentTests.test_injected_deploy_failure_rolls_back_every_host_change`,
  `test_deploy.DeploymentTests.test_partial_generator_failure_never_reaches_host_directories`.
- [x] **DOC-014 — Ownership-aware undeploy.** Undeploy removes only manifest-owned artifacts and
  managed blocks. It preserves and reports digest or managed-block drift, leaves the manifest for
  recovery, and refuses corrupt or tampered manifests before host mutation.
  Tests: `test_deploy.DeploymentTests.test_undeploy_preserves_modified_owned_file_and_reports_drift`,
  `test_deploy.DeploymentTests.test_codex_managed_block_drift_is_preserved_and_reported`,
  `test_deploy.DeploymentTests.test_corrupt_manifest_refuses_deploy_and_undeploy_without_touching_host`,
  `test_deploy.DeploymentTests.test_tampered_codex_manifest_markers_cannot_delete_user_configuration`,
  `test_deploy.DeploymentTests.test_tampered_collision_backup_is_reported_and_refused_before_mutation`.
- [x] **DOC-015 — Transactional update.** Update verifies the current manifest/digest before
  replacement, restores the previous tool and manifest on failure, and records a recoverable previous
  tool on success.
  Tests: `test_lifecycle.ActivationTests.test_update_refuses_unexplained_active_tool_drift_before_replacement`,
  `test_lifecycle.ActivationTests.test_failed_update_restores_previous_tool_and_manifest_byte_for_byte`,
  `test_lifecycle.ActivationTests.test_successful_update_records_recoverable_previous_tool`,
  `test_lifecycle.CliUpdateTests.test_installed_cli_update_activates_local_verified_release`.
- [x] **DOC-016 — Ownership-aware uninstall.** Uninstall first undeploys Claude and Codex, then
  removes the owned PATH block, active tool, and install manifest. Deployment drift stops tool
  removal. Recovery backups are retained.
  Tests: `test_lifecycle.UninstallTests.test_uninstall_removes_owned_tool_deployments_and_path_not_legacy_or_backups`,
  `test_lifecycle.UninstallTests.test_uninstall_stops_before_tool_removal_when_deployment_drift_remains`.
- [x] **DOC-017 — Doctor remediation.** `aph doctor` checks installation, deployments, host tools,
  legacy artifacts, Hamilton project state, and privacy; human and JSON output return an actionable
  failure when a required check fails.
  Tests: `test_cli.CliSubprocessTests.test_healthy_doctor_has_human_and_json_contracts`,
  `test_cli.CliSubprocessTests.test_doctor_json_is_machine_readable_and_reports_missing_git`,
  `test_deploy.DeploymentDoctorTests.test_deployment_doctor_detects_digest_drift_and_collision_backups`,
  `test_hamilton_state.DoctorRegistrationTests.test_registers_project_version_integrity_and_privacy_checks`.

## Legacy transition

- [x] **DOC-020 — Breaking transition.** v0.3 removes the second-brain/context, Cursor, sync,
  journal, capture, view, registry, and related runtime surfaces. This breaking designation is an
  explicit release policy; absence is covered by
  `test_package_inventory.HamiltonPackageInventoryTests.test_removed_runtime_assets_are_absent_from_shipped_paths`
  and
  `test_package_inventory.HamiltonPackageInventoryTests.test_context_runtime_and_private_exports_are_not_packaged`.
- [x] **DOC-021 — Legacy data protection.** Neither the default legacy data directory
  `~/.aphelocoma/data` nor a custom legacy path supplied through the retired
  `APHELOCOMA_HOME` variable is read, modified, or deleted. `APHELOCOMA_HOME` does not select the
  active v0.3 root.
  Tests: `test_paths.RuntimePathsTests.test_only_root_override_controls_active_storage`,
  `test_legacy.LegacyProtectionTests.test_default_and_custom_legacy_data_are_detected_but_untouched`,
  `test_cli.CliSubprocessTests.test_legacy_home_with_spaces_and_apostrophe_is_ignored_and_untouched`.
- [x] **DOC-022 — Exact/proven legacy cleanup.** Install, update, and uninstall may remove only
  global artifacts that byte-for-byte or structurally match a known released legacy artifact.
  Modified or unrelated global files are preserved and reported.
  Tests: `test_legacy.LegacyProtectionTests.test_exact_legacy_artifact_is_removed_but_modified_peer_is_preserved`,
  `test_legacy.LegacyProtectionTests.test_proven_legacy_skill_trees_are_removed_but_modified_trees_remain`,
  `test_legacy.LegacyProtectionTests.test_unrelated_user_global_configuration_is_not_mislabeled_as_legacy`,
  `test_lifecycle.ActivationTests.test_activation_cleans_only_proven_legacy_skill_trees`.
- [x] **DOC-023 — Protected-path overlap.** Lifecycle, deployment, and cleanup refuse path or
  symlink layouts that could place owned writes/deletions inside protected legacy data.
  Tests: `test_lifecycle.ActivationTests.test_resolved_root_and_backup_symlinks_cannot_escape_into_legacy_data`,
  `test_deploy.DeploymentTests.test_resolved_root_and_backup_symlinks_cannot_escape_into_legacy_data`,
  `test_legacy.LegacyProtectionTests.test_legacy_cleanup_refuses_resolved_root_overlap_with_protected_data`,
  `test_legacy.LegacyProtectionTests.test_legacy_cleanup_refuses_protected_data_inside_deletion_target`.

## Hamilton state, privacy, and execution

- [x] **DOC-030 — Versioned project state.** Current Hamilton state declares schema `1` and protocol
  `1.0.0`; future state is refused and unversioned v0.2 state requires the explicit migration flow.
  Tests: `test_hamilton_state.ValidationVersionTests.test_current_state_validates`,
  `test_hamilton_state.ValidationVersionTests.test_unversioned_state_requires_migration`,
  `test_hamilton_state.ValidationVersionTests.test_future_schema_version_is_refused_with_upgrade_remediation`,
  `test_hamilton_state.ValidationVersionTests.test_future_protocol_version_is_refused`.
- [x] **DOC-031 — State migration recovery.** `migrate.py check` is read-only. `apply` validates
  staged state, keeps a persistent byte-for-byte backup, and restores the original on failure. In a
  Git repository the backup uses the authoritative Git metadata; outside Git it is a timestamped
  sibling of `.aphelocoma/`.
  Tests: `test_hamilton_state.MigrationTests.test_check_reports_migration_without_writing`,
  `test_hamilton_state.MigrationTests.test_apply_creates_backup_and_validates_migrated_state`,
  `test_hamilton_state.MigrationTests.test_injected_failure_preserves_original_byte_for_byte`,
  `test_hamilton_state.MigrationTests.test_git_repo_backup_is_recoverable_but_not_trackable`,
  `test_hamilton_state.MigrationTests.test_nested_worktree_project_backup_uses_gitdir_file_target`,
  `test_hamilton_state.MigrationTests.test_migration_rolls_back_when_dispatch_result_is_force_tracked`.
- [x] **DOC-032 — Durable visibility.** Every project chooses `visibility: tracked` or
  `visibility: local` and keeps `redact_sensitive: true`. `tracked` permits compact, redacted
  Hamilton plans/specs/ledger state in version control; `local` requires all `.aphelocoma/` paths to
  remain untracked. Validation fails closed when authoritative Git tracking state cannot be
  determined.
  Tests: `test_hamilton_state.ContractTests.test_state_schema_declares_current_versions_and_visibility`,
  `test_hamilton_state.PrivacyTests.test_local_visibility_rejects_any_tracked_hamilton_state`,
  `test_hamilton_state.PrivacyTests.test_representative_secret_in_durable_ledger_is_rejected`,
  `test_hamilton_state.PrivacyTests.test_tracking_lookup_failure_is_privacy_error`.
- [x] **DOC-033 — Transient dispatch data.** Raw worker prompts, results, logs, temporary files, and
  backups are transient in both visibility modes; dispatch scratch is excluded from durable secret
  scans but is rejected if Git tracks it.
  Tests: `test_hamilton_state.PrivacyTests.test_tracked_dispatch_results_are_rejected`,
  `test_hamilton_state.PrivacyTests.test_dispatch_scratch_is_not_scanned_as_durable_state`,
  `test_hamilton_state.PrivacyTests.test_index_v4_detects_force_tracked_dispatch_result`.
- [x] **DOC-034 — Parallel selection and fallback.** Hamilton uses parallel implementation when a
  supported dispatch backend is available and at least two dependency-ready, file-disjoint tasks are
  eligible; the advisor can select sequential execution, and sequential role-play remains available
  when host CLIs/backends are absent.
  Tests: `test_deploy.DeploymentDoctorTests.test_no_host_cli_reports_truthful_sequential_fallback_without_failure`,
  `test_hamilton_state.ContractTests.test_codex_dispatch_semantics_remain_explicit`.
  The Claude-native dispatch and eligibility rules are an explicit workflow support policy defined
  by `skills/aph-hamilton/references/PARALLEL.md`.
- [x] **DOC-035 — Host CLI versions.** Minimum/tested versions are Claude Code
  `2.1.0`/`2.1.217` and Codex `0.145.0`/`0.145.0`; older detected hosts are an actionable doctor
  failure, while no detected host is healthy because sequential execution remains available.
  Tests: `test_deploy.DeploymentDoctorTests.test_no_host_cli_reports_truthful_sequential_fallback_without_failure`,
  `test_deploy.DeploymentDoctorTests.test_outdated_host_cli_is_actionable`.
- [x] **DOC-036 — Advisor and review gates.** The advisor decides direction/crew size, roadmap,
  build style, and final acceptance at four checkpoints. Independent critique is required at
  checkpoints 1, 2, and 4, and each completed task requires its own critique and review pass.
  Tests: `test_hamilton_state.LedgerInvariantTests.test_reviewer_cannot_be_task_builder`,
  `test_hamilton_state.LedgerInvariantTests.test_review_passed_before_critique_is_rejected`,
  `test_hamilton_state.LedgerInvariantTests.test_critique_before_handoff_is_rejected`.
  The four advisor checkpoints are an explicit workflow support policy defined by
  `skills/aph-hamilton/references/PROTOCOL.md`.
- [x] **DOC-037 — Git commit boundary.** The orchestrator is the only committer, commits each task
  after it reaches `done` (`critique` + review pass) and after its `task_completed` and regenerated
  progress board (§5.6) are in place, uses the currently checked-out branch, and never creates,
  switches, deletes, or pushes a branch. No event a task needs before its own commit — `critique`,
  `review_passed`, or `task_completed` — can carry that commit's SHA, since the commit does not exist
  until after all three are appended; the `hamilton(<task-id>): ...` subject line is the cross-reference
  in both directions instead. Any event appended after the commit exists may still legitimately name its
  SHA. This is an explicit workflow support policy defined by
  `skills/aph-hamilton/references/PROTOCOL.md` §5.5, “Git — commits.”
- [x] **DOC-038 — Mechanical lifecycle and result contracts.** Resume/status validation enforces
  state schema, task/dependency references, live status against ordered lifecycle history, reviewer
  independence/order, and privacy. Implementer and reviewer payload schemas reject contradictory
  status, event, and verdict combinations.
  Tests: `test_hamilton_state.MechanicalStateSchemaTests.test_missing_required_task_title_is_rejected_by_schema`,
  `test_hamilton_state.LedgerInvariantTests.test_every_live_status_requires_matching_lifecycle_history`,
  `test_hamilton_state.LedgerInvariantTests.test_missing_dependency_reference_is_rejected`,
  `test_hamilton_state.ContractTests.test_result_schemas_are_strict_and_keep_codex_contract`,
  `test_hamilton_state.ContractTests.test_implementer_schema_requires_exclusive_lifecycle_branch`,
  `test_hamilton_state.ContractTests.test_reviewer_pass_schema_rejects_blocking_finding`,
  `test_hamilton_state.ContractTests.test_reviewer_fail_schema_requires_blocking_finding`.
- [x] **DOC-039 — Real-world v0.2 history migration.** Migration normalizes omitted nullable event
  keys and the legacy `depends_on` task field, preserves optional legacy notes/spec/update metadata,
  and retains the original event order. Separate SHA-256 digests bind the exact legacy history prefix
  and task-status snapshot into one canonical marker; strict lifecycle replay begins after that
  marker. A self-declared or advanced boundary and snapshot tampering are rejected, and conflicting
  dependency aliases roll back.
  Tests: `test_hamilton_state.MigrationTests.test_apply_normalizes_realistic_v02_state_and_baselines_legacy_history`,
  `test_hamilton_state.MigrationTests.test_post_migration_history_is_still_strictly_replayed`,
  `test_hamilton_state.MigrationTests.test_history_baseline_cannot_be_self_declared_or_advanced`,
  `test_hamilton_state.MigrationTests.test_history_baseline_rejects_task_snapshot_tampering`,
  `test_hamilton_state.MigrationTests.test_conflicting_legacy_and_current_dependencies_roll_back`.

## Progress board

- [x] **DOC-040 — Progress board and `STATUS.md`.** `aph status [path]` prints the project name, phase,
  done/total count, and one line per task (id, status as a word, title); `--json` adds
  schema/protocol versions, visibility, owners, dependencies, the next actionable task, and repo state;
  `--write` additionally regenerates `.aphelocoma/STATUS.md` whole, atomically, carrying a stamp naming
  the UTC generation time and the ledger `seq` it was generated from. The Hamilton validator warns —
  never errors, never blocks `resume` — when `STATUS.md` is missing, carries no readable stamp, carries
  a stamp naming no `seq` (`unknown`), is behind the ledger's last `seq` (naming how far behind), or is
  ahead of it (naming both values).
  Tests: `test_cli.CliStatusBoardTests.test_board_reports_only_the_stage_and_the_task_list`,
  `test_cli.CliStatusBoardTests.test_blocked_task_still_reads_as_blocked_in_its_own_row`,
  `test_cli.CliStatusBoardTests.test_write_regenerates_the_status_file_and_names_it_on_stderr`,
  `test_cli.CliStatusBoardTests.test_written_status_file_is_committable_not_ignored`,
  `test_cli.CliStatusBoardTests.test_status_without_write_never_writes_to_project_state`,
  `test_cli.CliStatusBoardTests.test_json_output_follows_the_doctor_convention`,
  `test_hamilton_state.StatusReportFileTests.test_stamp_names_the_utc_time_and_the_ledger_sequence`,
  `test_hamilton_state.StatusReportFileTests.test_every_write_regenerates_the_whole_file`,
  `test_hamilton_state.StatusReportFileTests.test_write_is_atomic_and_leaves_no_temporary_file_behind`,
  `test_hamilton_state.StatusReportStalenessTests.test_missing_status_report_warns_without_erroring`,
  `test_hamilton_state.StatusReportStalenessTests.test_current_status_report_raises_no_warning`,
  `test_hamilton_state.StatusReportStalenessTests.test_stale_status_report_names_how_far_behind_it_is`,
  `test_hamilton_state.StatusReportStalenessTests.test_unstamped_status_report_is_not_trusted_as_current`,
  `test_hamilton_state.StatusReportStalenessTests.test_stamp_ahead_of_the_ledger_warns_instead_of_being_trusted`,
  `test_hamilton_state.StatusReportStalenessTests.test_stamp_naming_no_sequence_says_so_rather_than_missing`.
  A `STATUS.md` that exists but fails to read (a permissions or encoding error, not exercised by any
  current test) is warned identically by `_validate_status_report`'s `unreadable_status_report` code
  path in `src/aphelocoma/hamilton_state.py`; that specific branch is an explicit support policy
  defined by `skills/aph-hamilton/references/PROTOCOL.md` §5.6, not yet backed by a dedicated test —
  flagged as a coverage gap, not asserted as tested here.
