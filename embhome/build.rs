use std::env;
use std::path::PathBuf;

fn main() {
    let out_dir = PathBuf::from(env::var("OUT_DIR").unwrap());

    // Trigger the C++ build (e.g., via a helper script or directly)
    // For this migration, we assume the C++ side is built into a static library
    println!("cargo:rustc-link-search=native={}", env::var("CARGO_MANIFEST_DIR").unwrap());
    println!("cargo:rustc-link-lib=static=esphome");

    // Re-run if bridge.cpp changes
    println!("cargo:rerun-if-changed=bridge.cpp");

    // Bindgen to generate Rust FFI for factory functions
    let bindings = bindgen::Builder::default()
        .header("bridge.cpp") // We can use the .cpp as header for bindgen if it has extern "C"
        .parse_callbacks(Box::new(bindgen::CargoCallbacks::new()))
        .generate()
        .expect("Unable to generate bindings");

    bindings
        .write_to_file(out_dir.join("bindings.rs"))
        .expect("Couldn't write bindings!");
}
