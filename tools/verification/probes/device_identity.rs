//! Read compiled public identity functions only; never initialize or open a Host/device.
#[cfg(not(unix))]
compile_error!("This probe is the Linux/Unix verification profile, not a non-Unix port.");

fn main() {
    use rx_host::service::{device_package, external_package, jtc_package,
        python_execution_package, python_library, python_package};
    use serde_json::json;
    let melsec = device_package::driver();
    let jtc = jtc_package::driver();
    let hex = |value: Vec<u8>| value.iter().map(|byte| format!("{byte:02x}")).collect::<String>();
    println!("{}", json!({
        "schema": "rx.compiled-source-identities.v1", "role": "device",
        "target": {"os": std::env::consts::OS, "arch": std::env::consts::ARCH, "cfg_unix": cfg!(unix)},
        "package": {"name": env!("CARGO_PKG_NAME"), "version": env!("CARGO_PKG_VERSION")},
        "values": {
            "host.MELSEC": melsec.source_digest,
            "host.JTC": jtc.source_digest,
            "host.DYNAMIXEL": rx_host::dynamixel::profile::source_digest(),
            "driver.MELSEC": melsec,
            "driver.JTC": jtc,
            "driver.python-sdk": python_package::driver(),
            "driver.python-library": python_library::driver(),
            "driver.python-execution": python_execution_package::driver(),
            "driver.external-process": external_package::driver(),
            "S.device-package-validator.unix": rx_device_package::review::validator_digest()
        },
        "public_protocol_manifests": {
            "base/v1": hex(rx_host::rpc::base_manifest_hash()),
            "cell/v1": hex(rx_host::rpc::cell_manifest_hash())
        },
        "unobserved": {"S.device-package-validator.nonunix": "NOT_COMPILED_FOR_THIS_TARGET"},
        "scope": "PUBLIC_COMPILED_IDENTITY_FUNCTIONS_NO_HOST_INITIALIZE_OPEN_OR_DEVICE_IO"
    }));
}
