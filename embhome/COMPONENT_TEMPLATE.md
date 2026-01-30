# Component Implementation Template

Use this template when implementing new embhome components.

## Single Command Workflow

**User says:** "Implement uart component"

**Claude does:**
1. Read ESPHome source for uart
2. Implement Python layer (`embhome/components/uart/__init__.py`)
3. Implement Rust layer (`embhome/components/uart/Cargo.toml` + `src/lib.rs`)
4. Create ONE `README.md` (see template below)
5. Done.

## README.md Template

```markdown
# Component Name

## Python API

\`\`\`yaml
component:
  required_field: value
  optional_field: default_value
\`\`\`

**Helper functions** (if any):
- `helper_function()` - Description

## Rust API

\`\`\`rust
// Key types and public methods
pub struct Component { }

impl Component {
    pub fn new() -> Self { }
    pub fn key_method(&mut self) { }
}
\`\`\`

## Divergences from ESPHome

**Removed:**
- Feature X (reason)

**Simplified:**
- Feature Y (reason)

**Added:**
- Feature Z (reason)

## Example

\`\`\`yaml
# Minimal working config
component:
  field: value
\`\`\`

\`\`\`rust
// Minimal Rust usage
let component = Component::new();
\`\`\`
```

## What to Include

### Python (`__init__.py`)
- Configuration schema
- Validation logic
- Helper functions for dependent components
- Code generation (`to_code`)

### Rust (`src/lib.rs`)
- Core implementation using esp-hal
- Public API
- Error types
- embedded-hal trait implementations (if applicable)
- Brief inline documentation

### README
- Python config schema
- Rust API surface
- Divergences from ESPHome C++
- 1-2 minimal examples
- **That's it!**

## What NOT to Include

- ❌ Multiple documentation files
- ❌ Implementation status documents
- ❌ Progress reports
- ❌ Comparison tables
- ❌ Metrics
- ❌ Verbose explanations
- ❌ Separate examples files (put in README or inline)

## Rust Code Style

- Use esp-hal for peripheral access
- Leverage `embassy` and `esp-rs` whenever possible
- Implement embedded-hal traits where applicable
- Type-safe error handling
- Brief inline docs (not verbose)
- Examples in README, not separate file

## Keep It Simple

The goal is **working code + concise docs**, not extensive documentation.
