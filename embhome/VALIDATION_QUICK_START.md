# Validation System Quick Start

## Overview

The improved `codegen_helpers.py` now includes comprehensive validation to ensure generated projects are correct and consistent with the workspace.

## Quick Commands

### Basic Validation

```python
from pathlib import Path
from codegen_helpers import DependencyManager, ProjectConfig

# Initialize
dep_manager = DependencyManager(workspace_path=Path("./embhome"))

# Validate workspace
issues = dep_manager.validate_workspace_consistency()
if issues:
    for issue in issues:
        print(f"❌ {issue}")
else:
    print("✅ Workspace OK")
```

### Generate with Validation

```python
# Create config
config = ProjectConfig(
    name="my-device",
    chip="esp32c3",
    components=["esphome-wifi", "esphome-api"]
)

# Show what will be included
print(dep_manager.generate_dependency_report(config))

# Generate project
if dep_manager.generate_project_with_esp_generate(config, Path("./output")):
    # Validate result
    results = dep_manager.validate_generated_project(Path("./output/my-device"))
    dep_manager.report_validation_results(results)
```

## What Gets Validated

### 1. Workspace Validation (Pre-Generation)

Checks workspace components for:
- ✓ Correct use of `{ workspace = true }`
- ✓ Proper feature forwarding
- ✓ No version conflicts

**Run**: `dep_manager.validate_workspace_consistency()`

### 2. Project Validation (Post-Generation)

Checks generated projects for:
- ✓ No duplicate dependencies (`cargo tree --duplicates`)
- ✓ Chip features propagate correctly
- ✓ Dependency graph is correct

**Run**: `dep_manager.validate_generated_project(project_dir)`

### 3. Dependency Report (Pre-Generation)

Shows:
- Core dependencies (always included)
- Component dependencies (conditional)
- Feature propagation paths
- Transitive dependencies

**Run**: `dep_manager.generate_dependency_report(config)`

## Example Output

### Dependency Report

```
============================================================
DEPENDENCY CONFIGURATION REPORT
============================================================

Project: my-device
Target Chip: esp32c3

CORE DEPENDENCIES (always included):
  • esphome-core (workspace component)
  • esp-hal (from workspace)
  • embassy-executor (from workspace)
  • embassy-time (from workspace)

COMPONENT DEPENDENCIES:
  • esphome-wifi
    └─ embassy-net
    └─ esp-wifi

FEATURE CONFIGURATION:
  Chip feature 'esp32c3' propagates to:
  • esphome-core
  • esp-hal
  • esphome-wifi
  • esp-wifi (WiFi detected)

============================================================
```

### Validation Results

```
=== Project Validation Results ===

✅ No duplicate dependencies
✅ Feature propagation correct

📊 Dependency Graph (depth 2):
my-device v0.1.0
├── esphome-core v0.1.0
│   ├── embassy-executor v0.9.1
│   └── embassy-sync v0.7.2
├── esphome-wifi v0.1.0
│   ├── esp-hal v1.0.0
│   └── esp-wifi v0.11.0
└── esp-hal v1.0.0

========================================
✅ All validation checks passed!
========================================
```

## Common Issues and Fixes

### Issue: Duplicate Dependencies

**Symptom**: Validation reports duplicate versions of a library

**Cause**: Component not using workspace dependencies

**Fix**: Edit component's `Cargo.toml`:
```toml
# Change from:
embassy-time = "0.3.2"

# To:
embassy-time = { workspace = true }
```

### Issue: Missing Feature Forward

**Symptom**: Feature validation fails for a chip

**Cause**: Component doesn't forward chip feature to dependencies

**Fix**: Edit component's `Cargo.toml`:
```toml
[features]
esp32c3 = [
    "esphome-core/esp32c3",
    "esp-hal/esp32c3",  # Add this
]
```

### Issue: Version Mismatch

**Symptom**: Generated project uses wrong version

**Cause**: Workspace `Cargo.toml` not updated

**Fix**: Edit `/embhome/Cargo.toml`:
```toml
[workspace.dependencies]
esp-hal = { version = "1.0.0", ... }  # Update here
```

The code generator will automatically pick up the new version!

## Integration with CI/CD

### GitHub Actions Example

```yaml
- name: Validate Workspace
  run: |
    cd embhome
    python3 validate_workspace.py

- name: Check for Duplicates
  run: |
    cd embhome
    cargo tree --duplicates
```

### Pre-Commit Hook

```python
#!/usr/bin/env python3
from pathlib import Path
from codegen_helpers import DependencyManager

dep_manager = DependencyManager(workspace_path=Path("./embhome"))
issues = dep_manager.validate_workspace_consistency()

if issues:
    print("❌ Workspace validation failed!")
    for issue in issues:
        print(f"  {issue}")
    exit(1)

print("✅ Workspace validation passed")
```

## Best Practices

1. **Always validate workspace before generating**
   ```python
   issues = dep_manager.validate_workspace_consistency()
   if issues:
       raise ValueError("Fix workspace issues first")
   ```

2. **Review dependency report before building**
   ```python
   print(dep_manager.generate_dependency_report(config))
   # User can see what will be included
   ```

3. **Validate generated projects in CI**
   ```python
   results = dep_manager.validate_generated_project(project_dir)
   if not results["success"]:
       raise ValueError("Project validation failed")
   ```

4. **Use workspace versions for all dependencies**
   - Never hardcode versions in component `Cargo.toml`
   - Always use `{ workspace = true }`
   - Update versions in workspace root only

## Advanced Usage

### Custom Validation

```python
# Run only duplicate check
result = subprocess.run(
    ["cargo", "tree", "--duplicates"],
    cwd=project_dir,
    capture_output=True
)
if result.stdout.strip():
    print("Found duplicates!")
```

### Detailed Dependency Graph

```python
# Get full dependency tree
result = subprocess.run(
    ["cargo", "tree", "--edges", "normal"],
    cwd=project_dir,
    capture_output=True,
    text=True
)
print(result.stdout)
```

### Feature Analysis

```python
# Check which features are enabled
result = subprocess.run(
    ["cargo", "tree", "--edges", "features", "--features", "esp32c3"],
    cwd=project_dir,
    capture_output=True,
    text=True
)
print(result.stdout)
```

## Troubleshooting

### Validation Script Fails

**Error**: `ModuleNotFoundError: No module named 'tomli'`

**Fix**: Install Python dependencies:
```bash
pip install tomli tomli-w
```

### Cargo Commands Not Found

**Error**: `FileNotFoundError: [Errno 2] No such file or directory: 'cargo'`

**Fix**: Install Rust toolchain:
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

### False Positives

If validation reports issues that seem incorrect:
1. Check workspace `Cargo.toml` is valid
2. Ensure all components are in workspace members
3. Run `cargo update` to refresh lock file
4. Try `cargo clean` and regenerate

## Further Reading

- [IMPROVEMENTS.md](IMPROVEMENTS.md) - Detailed explanation of improvements
- [DEPENDENCY_MANAGEMENT.md](DEPENDENCY_MANAGEMENT.md) - Complete system documentation
- [dependency_comparison_analysis.md](dependency_comparison_analysis.md) - Analysis and recommendations

## Quick Test

Run the example to see all features in action:

```bash
cd embhome
python3 -c "from codegen_helpers import example_usage; example_usage()"
```

Expected output:
- ✅ Workspace validation
- 📊 Dependency report
- ✅ Project generation
- ✅ Post-generation validation
