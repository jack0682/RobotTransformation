# RX product documentation

RobotTransformation owns current RX product documentation and contracts. The original
[rx_docs snapshot](https://github.com/jack0682/rx_docs/tree/4384ed49e384c53e645f71757ce597292b928eb6/docs)
remains available with its original history, paths, tags, signatures, and evidence.
Later historical records remain evidence about their recorded revisions; they do not
silently update the current product's acceptance state.

Start with the [product definition](01_product_definition.md),
[core charter](43_core_charter.md), [framework plan](42_framework_master_plan.md),
and [implementation limits](implementation/critical_open_items.md).
The [contract index](../contracts/README.md) identifies normative sources and mirrors.

This migration changes document ownership and navigation. Dated conclusions and
code blocks retain their original scope. They are not new build, deployment,
physical-equipment, performance, or functional-safety evidence. In particular, the
preserved F2′ CP2 failure is not accepted or settled by this document migration.

## Sources and navigation

- Current product explanations live under `docs/`.
- Current semantic contracts live under `contracts/semantic/` and `contracts/cell-operations/`.
- Historical execution evidence remains in [rx_docs](https://github.com/jack0682/rx_docs).
- The [M4 document map](../provenance/import/M4-canonical-document-map.json) records
  source paths, exact input hashes, canonical paths, mirror relationships, and the
  finite compatibility projections.
- The [M3 origin index](../provenance/import/M3-document-origins.json) retains the
  original paths and immutable evidence destinations. Use the M4 map to resolve
  those historical paths to current documents; its line numbers describe the
  earlier input, not permanent positions in current files.

Ordinary documentation can evolve through reviewed PRs. Hash-bound normative bytes,
contract manifests, and compatibility projections require their integrity gates.
The wiki and GitHub Project organize navigation and delivery; neither replaces
normative documents, CI results, or an explicit acceptance record.
