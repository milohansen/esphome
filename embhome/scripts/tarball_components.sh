#!/bin/bash
set -e

# Directories
ESPHOME_ROOT="/home/miloh/repos/esphome"
DOCS_ROOT="/home/miloh/repos/esphome-docs/content/components"
OUTPUT_ROOT="${ESPHOME_ROOT}/embhome/components"
COMPONENTS_DIR="${ESPHOME_ROOT}/esphome/components"

# Counters
TOTAL=0
WITH_DOCS=0
CODE_ONLY=0
FAILED=0

echo "Creating tarballs for all ESPHome components..."
echo "================================================"
echo ""

# Create output directory
mkdir -p "${OUTPUT_ROOT}"

# Create temporary directory for staging
TEMP_DIR=$(mktemp -d)
trap "rm -rf ${TEMP_DIR}" EXIT

# Iterate through all components
for component_path in "${COMPONENTS_DIR}"/*; do
    if [ ! -d "${component_path}" ]; then
        continue
    fi

    component=$(basename "${component_path}")
    TOTAL=$((TOTAL + 1))

    # Create output directory for this component
    mkdir -p "${OUTPUT_ROOT}/${component}"

    # Prepare staging area
    STAGE_DIR="${TEMP_DIR}/${component}"
    rm -rf "${STAGE_DIR}"
    mkdir -p "${STAGE_DIR}"

    # Check if documentation exists (directory or .md file)
    DOCS_DIR_PATH="${DOCS_ROOT}/${component}"
    DOCS_FILE_PATH="${DOCS_ROOT}/${component}.md"
    HAS_DOCS=false
    DOCS_TYPE=""

    if [ -d "${DOCS_DIR_PATH}" ]; then
        HAS_DOCS=true
        DOCS_TYPE="dir"
        WITH_DOCS=$((WITH_DOCS + 1))
    elif [ -f "${DOCS_FILE_PATH}" ]; then
        HAS_DOCS=true
        DOCS_TYPE="file"
        WITH_DOCS=$((WITH_DOCS + 1))
    else
        CODE_ONLY=$((CODE_ONLY + 1))
    fi

    # Create tarball
    TARBALL="${OUTPUT_ROOT}/${component}/${component}-reference.tar.gz"

    if [ "$HAS_DOCS" = true ]; then
        # Include both code and docs
        if [ "$DOCS_TYPE" = "dir" ]; then
            # Documentation is a directory
            tar -czf "${TARBALL}" \
                -C "${DOCS_ROOT}" "${component}" \
                -C "${ESPHOME_ROOT}" "esphome/components/${component}" \
                2>/dev/null
        else
            # Documentation is a single .md file
            tar -czf "${TARBALL}" \
                -C "${DOCS_ROOT}" "${component}.md" \
                -C "${ESPHOME_ROOT}" "esphome/components/${component}" \
                2>/dev/null
        fi

        if [ $? -eq 0 ]; then
            SIZE=$(du -h "${TARBALL}" | cut -f1)
            echo "✓ ${component} (${SIZE}) - with docs (${DOCS_TYPE})"
        else
            echo "✗ ${component} - FAILED"
            FAILED=$((FAILED + 1))
            rm -f "${TARBALL}"
        fi
    else
        # Code only
        tar -czf "${TARBALL}" \
            -C "${ESPHOME_ROOT}" "esphome/components/${component}" \
            2>/dev/null

        if [ $? -eq 0 ]; then
            SIZE=$(du -h "${TARBALL}" | cut -f1)
            echo "✓ ${component} (${SIZE}) - code only"
        else
            echo "✗ ${component} - FAILED"
            FAILED=$((FAILED + 1))
            rm -f "${TARBALL}"
        fi
    fi
done

echo ""
echo "================================================"
echo "Summary:"
echo "  Total components: ${TOTAL}"
echo "  With documentation: ${WITH_DOCS}"
echo "  Code only: ${CODE_ONLY}"
echo "  Failed: ${FAILED}"
echo ""
echo "Tarballs created in: ${OUTPUT_ROOT}"
