# Changelog

## [Unreleased]

### Added - esp-generate Integration

#### Code Generation
- **esp-generate integration**: Projects now use `cargo-generate` with esp-rs/esp-template as foundation
- `generate_project_with_esp_generate()`: Primary generation method using official esp-rs templates
- Automatic fallback to manual generation if cargo-generate not available
- Two-stage generation: esp-template base + ESPHome component injection

#### Dependency Management
- Workspace-level dependency management ensures single versions
- Automatic feature propagation for chip-specific features
- All components updated to use `{ workspace = true }`
- Unified dependency versions:
  - Embassy: executor 0.9.1, time 0.5.0, sync 0.7.2
  - esp-hal: 1.0.0 (unified from 0.22.0 and 1.0.0)

#### Documentation
- **ESP_GENERATE_INTEGRATION.md**: Complete esp-generate integration guide
- **DEPENDENCY_MANAGEMENT.md**: Comprehensive dependency system documentation
- **QUICK_REFERENCE.md**: Developer cheat sheet
- **README.md**: Updated getting started guide
- **CHANGELOG.md**: This file

#### Validation
- `validate_workspace.py`: Script to validate dependency consistency
- Checks for duplicate dependencies
- Validates feature forwarding
- Verifies Embassy version consistency

#### Examples
- `example-generated-project/`: Shows expected output structure
- Demonstrates feature propagation
- Includes cargo configuration

### Changed

#### Component Updates
All 9 workspace crates updated:
- Added chip feature forwarding (esp32, esp32c3, esp32s2, etc.)
- Migrated to workspace dependencies
- Added feature sections with proper forwarding

#### Code Generator
- `codegen_helpers.py`: Added esp-generate integration
- `DependencyManager`: New methods for template-based generation
- Chip mapping for esp-template MCU names

### Fixed

#### Version Conflicts Resolved
- **esphome-api**: Embassy 0.6.0 → 0.9.1/0.5.0/0.7.2
- **esphome-ota**: Embassy 0.6.0 → 0.9.1/0.5.0, esp-hal 0.22.0 → 1.0.0
- **esphome-uptime**: Embassy 0.6.0/0.3.2 → 0.9.1/0.5.0
- All components now use consistent dependency versions

### Benefits

#### For Users
- ✅ Smaller binaries (no duplicate libraries)
- ✅ No type incompatibility issues
- ✅ Builds work first time
- ✅ Official esp-rs ecosystem compatibility

#### For Developers
- ✅ Add `{ workspace = true }`, never worry about versions
- ✅ Automatic feature propagation
- ✅ Clear validation before commit
- ✅ Official template as foundation

#### For Maintainers
- ✅ Update version once, all components get it
- ✅ Validation catches issues early
- ✅ Less code to maintain (use esp-rs templates)
- ✅ Automatic updates from upstream

## Integration Guide

### For ESPHome Build System

```python
from embhome.codegen_helpers import DependencyManager, ProjectConfig

# In esphome/rust_codegen.py
def generate_rust_project(config, output_dir: Path):
    chip = config["esphome"].get("platform", "esp32c3")
    components = extract_components_from_config(config)

    dep_manager = DependencyManager(workspace_path=Path("./embhome"))
    project_config = ProjectConfig(
        name=config["esphome"]["name"],
        chip=chip,
        components=components,
    )

    # Use esp-generate (preferred)
    if dep_manager.generate_project_with_esp_generate(project_config, output_dir):
        print("Generated with esp-generate")
    else:
        # Fallback
        dep_manager.generate_project_cargo_toml(project_config, output_dir)
        dep_manager.generate_cargo_config(chip, output_dir)
```

### Required Python Dependencies

```bash
pip install tomli tomli-w
```

### Required Rust Tools

```bash
cargo install cargo-generate espflash
```

## Migration from Previous System

### Before
- Manual Cargo.toml generation
- Version conflicts between components
- Manual feature configuration
- Custom project structure

### After
- esp-generate creates base project
- Single dependency versions enforced
- Automatic feature propagation
- Standard esp-rs project structure

### Migration Steps

1. Install `cargo-generate`:
   ```bash
   cargo install cargo-generate
   ```

2. Update code generator to use new API:
   ```python
   # Old
   gen.generate_cargo_toml()

   # New
   dep_manager.generate_project_with_esp_generate(config, output_dir)
   ```

3. Validate workspace:
   ```bash
   cd embhome
   ./validate_workspace.py
   ```

## Breaking Changes

### None
The new system is fully backward compatible. If `cargo-generate` is not installed, automatic fallback to manual generation.

### Recommended Changes

- Install `cargo-generate` for best results
- Use `generate_project_with_esp_generate()` instead of manual methods
- Run `validate_workspace.py` before commits

## Future Plans

- [ ] Custom ESPHome cargo-generate template
- [ ] Pre-configured component bundles
- [ ] Component registry system
- [ ] Incremental generation (only regenerate changed files)
- [ ] Integration with ESPHome dashboard
