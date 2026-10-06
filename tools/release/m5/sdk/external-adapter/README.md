# External adapter simulation SDK

`rx_external_adapter.py` is the unchanged helper exported by the selected installed release. `counter.py`, `make_package_inputs.py` and `conformance.py` are independent public examples. They import neither RX core source nor private authority APIs.

An adapter implements finite `execute(envelope, correlation)`, passive `observe(sources)`, and passive `custody()`. It preserves the Host-supplied original operation/invocation. The helper records native facts; Host independently validates declarations, freshness, custody and authority. An adapter must never settle/release P work or turn UNKNOWN into success.

This example increments a file-backed simulation counter by one. Its deliberate after-entry and after-completion process-loss modes are isolated verification injections, not an operating recovery policy or physical adapter.

Use the installed CLI sequence `external-program → external-assemble → request → external signer → seal → external-register`. Preserve actual Program references and use CLI validation/normalization rather than reimplementing their digests. `make_package_inputs.py --help` describes fresh installation context inputs. Changing helper/template bytes changes the program/package pin and requires fresh review/qualification. Registration makes a package available; it does not authorize activation or native execution.

`schema-reference.json` is a descriptive interface index, not a new normative contract or duplicated JSON Schema validator. The same selected release's CLI and Host validate authoring and native messages.

Fresh Linux component conformance:

```sh
CI=true python3 -B conformance.py --sdk . --output /fresh/component-evidence --execute-fresh-linux-ci
```

This synthetic native-channel result has component scope only. The separate verification kit must prove actual registered P/Host/Executor execution and source-free author boundaries. Publisher GPG provenance and CI package/review/qualification fixture signatures remain separate.
