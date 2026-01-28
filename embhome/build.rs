use std::env;
use std::path::PathBuf;
use std::process::Command;

fn main() {
    let out_dir = PathBuf::from(env::var("OUT_DIR").unwrap());

    // Trigger the C++ build
    println!("cargo:rerun-if-changed=build_cpp.py");
    let status = Command::new("python3")
        .arg("build_cpp.py")
        .status()
        .expect("Failed to execute build_cpp.py");

    if !status.success() {
        panic!("build_cpp.py failed");
    }

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
