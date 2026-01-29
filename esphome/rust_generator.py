from dataclasses import dataclass, field


@dataclass
class RustDependency:
    name: str
    version: str
    features: list[str] = field(default_factory=list)
    git: str | None = None
    path: str | None = None


@dataclass
class RustFunction:
    name: str
    body: str
    is_async: bool = False
    attributes: list[str] = field(default_factory=list)
    args: list[str] = field(default_factory=list)
    return_type: str | None = None


class RustGenerator:
    def __init__(self):
        self.dependencies: list[RustDependency] = []
        self.modules: list[str] = []
        self.functions: list[RustFunction] = []
        self.main_body: list[str] = []
        self.component_spawns: list[str] = []

    def add_dependency(self, dep: RustDependency):
        self.dependencies.append(dep)

    def add_module(self, name: str):
        self.modules.append(name)

    def add_function(self, func: RustFunction):
        self.functions.append(func)

    def add_main_code(self, code: str):
        self.main_body.append(code)

    def add_component_spawn(self, code: str):
        self.component_spawns.append(code)

    def generate_cargo_toml(self) -> str:
        toml = '[package]\nname = "esphome_app"\nversion = "0.1.0"\nedition = "2021"\n\n[dependencies]\n'
        for dep in self.dependencies:
            toml += f'{dep.name} = {{ version = "{dep.version}"'
            if dep.features:
                feats = ", ".join([f'"{f}"' for f in dep.features])
                toml += f", features = [{feats}]"
            if dep.path:
                toml += f', path = "{dep.path}"'
            elif dep.git:
                toml += f', git = "{dep.git}"'
            toml += " }\n"

        toml += '\n[profile.release]\nopt-level = "s"\nlto = true\nstrip = true\n'
        return toml

    def generate_main_rs(self) -> str:
        code = "#![no_std]\n#![no_main]\n\n"
        code += "use embassy_executor::Spawner;\n"
        code += "use esp_backtrace as _;\n"
        code += "use esp_hal::{clock::ClockControl, peripherals::Peripherals, prelude::*, timer::TimerGroup};\n"
        code += "use esphome_core::{Application, Platform};\n\n"

        for mod_name in self.modules:
            code += f"mod {mod_name};\n"

        code += "\n"
        for func in self.functions:
            for attr in func.attributes:
                code += f"{attr}\n"
            async_kw = "async " if func.is_async else ""
            args_str = ", ".join(func.args)
            ret_str = f" -> {func.return_type}" if func.return_type else ""
            code += (
                f"{async_kw}fn {func.name}({args_str}){ret_str} {{\n{func.body}\n}}\n\n"
            )

        code += "#[esp_hal_embassy::main]\n"
        code += "async fn main(spawner: Spawner) {\n"
        code += "    let peripherals = Peripherals::take();\n"
        code += "    let system = peripherals.SYSTEM.split();\n"
        code += "    let clocks = ClockControl::max(system.clock_control).freeze();\n\n"
        code += "    let timer_group0 = TimerGroup::new(peripherals.TIMG0, &clocks);\n"
        code += "    esp_hal_embassy::init(&clocks, timer_group0.timer0);\n\n"

        for line in self.main_body:
            code += f"    {line}\n"

        code += "\n    // Spawn components\n"
        for line in self.component_spawns:
            code += f"    {line}\n"

        code += "}\n"
        return code
