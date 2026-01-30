"""
Interval component code generation for Rust.
"""

from typing import Any
import esphome.config_validation as cv
import esphome.codegen as cg
from esphome.const import CONF_INTERVAL, CONF_STARTUP_DELAY, CONF_ID
from esphome.rust_generator import RustDependency, RustFunction
from embhome.core.rust_component import (
    RustComponent,
    RustComponentConfig,
    register_rust_component,
)

# ESPHome-like namespace
interval_ns = cg.esphome_ns.namespace("interval")

CONFIG_SCHEMA = cv.All(
    cv.ensure_list(
        cv.Schema(
            {
                cv.GenerateID(): cv.declare_id(interval_ns.class_("IntervalTrigger")),
                cv.Required(CONF_INTERVAL): cv.positive_time_period_milliseconds,
                cv.Optional(
                    CONF_STARTUP_DELAY, default="0s"
                ): cv.positive_time_period_milliseconds,
            }
        ).extend(cv.COMPONENT_SCHEMA)
    )
)


class IntervalComponent(RustComponent):
    """Interval component code generation for Rust."""

    def __init__(self):
        super().__init__("interval")

    def get_dependencies(
        self, gen: Any, config: RustComponentConfig
    ) -> list[RustDependency]:
        rust_root = config.rust_root
        return [
            RustDependency(
                "esphome-interval",
                "0.1.0",
                path=str(rust_root / "components/interval"),
            ),
        ]

    def add_setup_code(self, gen: Any, config: RustComponentConfig) -> None:
        # intervals is a list because of cv.ensure_list
        intervals = config.config.get("interval", [])

        for i, conf in enumerate(intervals):
            interval_id = conf[CONF_ID]
            interval_ms = conf[CONF_INTERVAL]
            startup_delay_ms = conf[CONF_STARTUP_DELAY]

            # Generate task function for this instance
            task_name = f"interval_task_{i}"

            body = f"""
    use esphome_interval::{{IntervalActor, IntervalConfig}};
    use esphome_core::Component;
    use embassy_sync::channel::Channel;
    use embassy_sync::blocking_mutex::raw::CriticalSectionRawMutex;

    static MAILBOX: Channel<CriticalSectionRawMutex, esphome_interval::IntervalMessage, 8> = Channel::new();

    let mut actor = IntervalActor::new("{interval_id}");
    let config = IntervalConfig {{
        interval_ms: {interval_ms},
        startup_delay_ms: {startup_delay_ms},
    }};

    actor.setup(config).await.expect("Failed to setup interval actor");
    actor.run(MAILBOX.receiver()).await;
            """

            func = RustFunction(
                name=task_name,
                body=body,
                is_async=True,
                attributes=["#[embassy_executor::task]"],
            )
            gen.add_function(func)

            gen.add_component_spawn(f"spawner.spawn({task_name}()).unwrap();")


register_rust_component("interval", IntervalComponent())


async def to_code(config):
    # This is for the C++ generation path, which we might still want to support
    # but for now we focus on the Rust side.
    pass
