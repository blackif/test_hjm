#!/bin/bash
# setup_sdk.sh - Install SAP NW RFC SDK from workspace

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(dirname "$SCRIPT_DIR")"
WORKSPACE_ROOT="$HOME/.openclaw/workspace"
SDK_SOURCE="$WORKSPACE_ROOT/sap-sdk/nwrfcsdk"
SDK_TARGET="/usr/local/sap/nwrfcsdk"

echo "=== SAP NW RFC SDK Setup ==="
echo ""

# Check if SDK exists in workspace
if [ ! -d "$SDK_SOURCE" ]; then
    echo "ERROR: SAP SDK not found at $SDK_SOURCE"
    echo "Please ensure the SDK is extracted to: $WORKSPACE_ROOT/sap-sdk/nwrfcsdk"
    exit 1
fi

echo "✓ Found SDK at: $SDK_SOURCE"
echo ""

# Create target directory
echo "Installing SDK to: $SDK_TARGET"
sudo mkdir -p "$(dirname $SDK_TARGET)"
sudo cp -r "$SDK_SOURCE" "$SDK_TARGET"
echo "✓ SDK copied"

# Set permissions
sudo chmod -R 755 "$SDK_TARGET"
echo "✓ Permissions set"

# Set environment variables
ENV_LINE1="export SAPNWRFC_HOME=$SDK_TARGET"
ENV_LINE2="export LD_LIBRARY_PATH=\$SAPNWRFC_HOME/lib:\$LD_LIBRARY_PATH"

if ! grep -q "SAPNWRFC_HOME" ~/.bashrc 2>/dev/null; then
    echo "" >> ~/.bashrc
    echo "# SAP NW RFC SDK" >> ~/.bashrc
    echo "$ENV_LINE1" >> ~/.bashrc
    echo "$ENV_LINE2" >> ~/.bashrc
    echo "✓ Environment variables added to ~/.bashrc"
else
    echo "✓ Environment variables already in ~/.bashrc"
fi

# Export for current session
export SAPNWRFC_HOME=$SDK_TARGET
export LD_LIBRARY_PATH=$SAPNWRFC_HOME/lib:$LD_LIBRARY_PATH

echo ""
echo "=== Installing pyrfc ==="
pip3 install --user pyrfc
echo "✓ pyrfc installed"

echo ""
echo "=== Testing Installation ==="
if python3 -c "import pyrfc; print('pyrfc version:', pyrfc.__version__)" 2>/dev/null; then
    echo "✓ pyrfc import successful"
else
    echo "⚠ pyrfc import failed - may need to restart shell or run: source ~/.bashrc"
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "SDK Location: $SDK_TARGET"
echo "Environment: SAPNWRFC_HOME=$SAPNWRFC_HOME"
echo ""
echo "Next steps:"
echo "1. Run: source ~/.bashrc"
echo "2. Test: python3 -c 'import pyrfc; print(pyrfc.__version__)'"
echo "3. Start using SAP Agent commands"
