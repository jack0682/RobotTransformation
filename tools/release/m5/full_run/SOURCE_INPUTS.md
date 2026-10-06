# Verification inputs and authority boundary

The enclosing SDK/distribution manifests pin the actual monorepo commit and `rx-platform`/`rx-solutions` component tree OIDs. No mutable branch reference is an execution input.

Public provisioning behavior comes from `rx-platform/tools/cell_delivery/{api,docker,materials,installation,qualification}.py`, installed `rx-platformd` fixture export, and the public Platform REST interfaces. The separate `counter_commission.py` keeps the existing public gate sequence while labelling this finite external-adapter simulation accurately. It does not implement a product authority.

Authoring uses installed `rx-device-package`, `rx-process-package`, and `/opt/rx/client/rx`. The native helper is exported by the installed device package CLI and compared with the selected tracked helper. Counter and input generator are external public examples. The Host native message source is `rx-solutions/runtime/rx-host/src/external_process/{profile,wire,mod}.rs`; the harness observes persisted facts without changing those sources.

The release evidence must cover the exact selected S image and sealed source archive, with actual passing witnesses for `sigkill_at_both_journal_native_boundaries_never_replays_device_effect`, `lost_run_initialization_reply_recovers_binding_without_reinitializing`, and `run_creation_marker_cannot_change_after_header_initialization`. These generic software witnesses do not certify physical or external cold recovery.

Historical consumer provenance is separately pinned by `HISTORICAL_CONSUMER_LOCK.json`: published v0.4.0-rc.1 asset, OCI index/manifest/config/layer, old source commit and four unchanged installed Python files. Current SDK copies cannot satisfy this oracle.

Only fresh CI fixture signing is used during acceptance. Publisher OpenPGP signing occurs separately after the owner reviews exact artifact checksums. The original CP2 execution and its preservation environment are outside this harness.
