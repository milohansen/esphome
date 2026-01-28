#include "esphome.h"

class my_rust_compProxy : public esphome::Component {
 public:
  void loop() override {}
  void turn_on() { /* call rust via FFI */ }
};
extern "C" void* create_my_rust_comp_proxy() {
  return (void*) new my_rust_compProxy();
}
extern "C" {
  void* create_preferences_intervalsyncer_id() {
    return (void*) new preferences::IntervalSyncer();
  }
  void* create_my_dht() {
    return (void*) new dht::DHT();
  }
  void* create_interval_intervaltrigger_id() {
    return (void*) new interval::IntervalTrigger();
  }
  void call_cpp_loop(void* ptr) {
    ((esphome::Component*)ptr)->loop();
  }
}