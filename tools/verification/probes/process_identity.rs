//! Calls the actual process package validator identity; no package installation/execution.
fn main() {
    println!("{}", serde_json::json!({
        "schema": "rx.compiled-source-identities.v1", "role": "process",
        "target": {"os": std::env::consts::OS, "arch": std::env::consts::ARCH, "cfg_unix": cfg!(unix)},
        "package": {"name": env!("CARGO_PKG_NAME"), "version": env!("CARGO_PKG_VERSION")},
        "values": {"S.process-package-validator": rx_process_package::review::validator_digest()},
        "scope": "PUBLIC_COMPILED_IDENTITY_FUNCTION_NO_PROCESS_OR_PACKAGE_EXECUTION"
    }));
}
