//! Non-actuating public-library identity probe. Inject only into an isolated CI copy.
use rx_domain::workflow;
use rx_process_contract::{execution_v2, source_validation};
use serde_json::json;
use std::collections::BTreeMap;

fn main() {
    let reference = json!({
        "catalog": "00000000-0000-4000-8000-000000000001",
        "id": "00000000-0000-4000-8000-000000000002",
        "revision": "1", "digest": "11".repeat(32)
    });
    // Valid model shape, deliberately absent definitions/context. The actual
    // resolver returns a BLOCKED report containing its compiled resolver digest.
    let spec: workflow::Spec = serde_json::from_value(json!({
        "schema": "rx.workflow-model.v1",
        "contexts": {"actor": {
            "label": "Identity probe", "kind": "RESOURCE",
            "accepted_types": [reference.clone()], "required": true, "multiple": false
        }},
        "defaults": {}, "property_sets": [],
        "tasks": {"probe": {
            "label": "Identity probe", "contexts": ["actor"],
            "properties": {"timeout": {
                "property": reference.clone(), "sources": [{"kind": "DEFAULT"}],
                "default": {"unit": "s", "data": {"kind": "NUMBER", "range": {"min": 1.0, "max": 1.0}}}
            }},
            "constraints": [],
            "capabilities": [{"name": "probe", "slot": "actor", "field": "can"}],
            "skills": [{
                "capability": "probe", "slot": "actor",
                "implementation_field": "implementation", "version_field": "version",
                "primitive": "probe", "parameters": {"timeout": "timeout"}
            }],
            "timeout_property": "timeout",
            "done": {"observation": "done", "property": reference.clone(),
                "equals": {"unit": "unitless", "data": {"kind": "BOOLEAN", "value": true}}},
            "on_failure": "STOP", "on_unknown": "HOLD_AND_RECONCILE"
        }},
        "rules": {}, "constraints": {},
        "steps": [{"id": "probe-node", "task": "probe"}]
    })).expect("probe Spec shape JSON");
    let request: workflow::Request = serde_json::from_value(json!({
        "workflow": reference, "contexts": {}, "property_sets": [],
        "overrides": {}, "inputs": {}, "slot_index": "0"
    })).expect("probe Request shape JSON");
    spec.validate_shape().expect("probe Spec shape");
    request.validate_shape().expect("probe Request shape");
    let resolution = workflow::resolve(&spec, request, &BTreeMap::new())
        .expect("resolver refusal report");
    assert!(!resolution.valid && !resolution.concrete);
    assert_eq!(resolution.status, "BLOCKED");
    assert!(!resolution.violations.is_empty());

    // This calls the real validator. An intentionally malformed document is
    // refused, but Report::empty supplies the actual compiled validator digest.
    let source = source_validation::document(&json!({}));
    assert!(!source.structurally_valid);
    assert!(source.issues.iter().any(|issue| issue.code == "DOCUMENT_SHAPE"));
    println!("{}", json!({
        "schema": "rx.compiled-source-identities.v1", "role": "platform",
        "target": {"os": std::env::consts::OS, "arch": std::env::consts::ARCH, "cfg_unix": cfg!(unix)},
        "package": {"name": env!("CARGO_PKG_NAME"), "version": env!("CARGO_PKG_VERSION")},
        "values": {
            "P.workflow-resolver": resolution.resolver_digest,
            "P.workflow-materializer": execution_v2::compiler_digest(),
            "P.process-source-validator": source.validator_digest
        },
        "bindings": {"executor-execution/v2": execution_v2::executor::binding_hash()},
        "fixture_outcomes": {"resolver": "BLOCKED", "source_validator": "DOCUMENT_SHAPE"},
        "scope": "PUBLIC_PURE_LIBRARY_FUNCTIONS_NO_ENGINE_NO_DEVICE_NO_TRANSPORT"
    }));
}
