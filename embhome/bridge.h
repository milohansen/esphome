#pragma once

#include "../esphome/core/component.h"
#include "../esphome/core/preferences.h"
#include "../esphome/components/interval/interval.h"
#include "../esphome/components/dht/dht.h"

extern "C" {
  void* create_my_rust_comp_proxy();
  void* create_preferences_intervalsyncer_id();
  void* create_my_dht();
  void* create_interval_intervaltrigger_id();
  void call_cpp_loop(void* ptr);
}