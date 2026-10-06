# RX contracts and canonical ownership

RobotTransformation owns current contract sources. Normative meaning, implementation
bindings, generated SDK material, and historical evidence have separate roles.

| Material | Canonical owner in this repository | Consumers |
|---|---|---|
| Common operation semantics v1.0 | [semantic/v1.0](semantic/v1.0/README.md) | Platform spec mirror and exported Host SDK |
| Cell operations v1.0 | [cell-operations/v1.0](cell-operations/v1.0/README.md) | Platform spec mirror and exported Host SDK |
| Workflow execution v2 | [semantic/workflow-execution/v2](semantic/workflow-execution/v2/README.md) | Binding and implementation gates |
| Wire definitions until the M7 layout transition | [rx-platform/proto](../rx-platform/proto/) | Generated clients and runtime protocols |
| Implementation bindings until M7 | [rx-platform/spec](../rx-platform/spec/) | Implementation identity and Host SDK generation |

The 24 v1.0 contract files mirrored in `rx-platform/spec/` and
`rx-solutions/sdk/spec/` must remain byte-identical to these canonical sources.
They are consumer copies, not competing authorship locations. Host SDK parity and
contract integrity checks remain required.

The 18 imported hash-bound documents retain their exact bytes. Some inherited links
therefore still name original rx_docs locations; those original documents remain
preserved, and a link's existence is not new acceptance evidence. The two workflow
README links whose relative base changed use small navigation-only routes at
[the cell model route](implementation/laser_cell_model.md) and
[the master plan route](42_framework_master_plan.md). These pages point to both
current canonical documents and immutable originals and have no independent
normative authority. They are not content mirrors or substitute contracts.

Two exact JSON projections remain under `references/execution_v2_design_2026-10-02/`
solely to preserve other byte-frozen workflow links. Bulk execution evidence remains
in rx_docs. Their complete inventory, hashes, and dispositions are in the
[M4 document map](../provenance/import/M4-canonical-document-map.json).

Document migration does not qualify a runtime or installation, authorize a retry,
settle UNKNOWN, or accept the preserved CP2 Run. Changes to normative semantics
follow the contract revision procedure and their affected conformance gates.
