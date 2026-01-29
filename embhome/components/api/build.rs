fn main() {
    let mut config = prost_build::Config::new();
    config.compile_protos(
        &["../../components/api/api.proto"],
        &["../../components/api/"],
    ).unwrap();
}
