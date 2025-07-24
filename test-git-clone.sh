#!/bin/bash
set -e

echo "=== Testing Git Clone Optimization ==="

# Check if git-operations.sh exists
if [ ! -f "./config/rootfs/debos/scripts/git-operations.sh" ]; then
    echo "Error: git-operations.sh not found!"
    exit 1
fi

# Source our git operations function
source ./config/rootfs/debos/scripts/git-operations.sh

# Test the function with a small repository
echo "Testing git_clone_optimized..."

# Create a temporary directory for testing
TEMP_DIR="/tmp/git-test-$$"
mkdir -p "$TEMP_DIR"
cd "$TEMP_DIR"

echo "Temp directory: $TEMP_DIR"

# Test with a small repository (auto-detect branch)
echo "Cloning test repository (auto-detect default branch)..."
if git_clone_optimized https://github.com/octocat/Hello-World.git hello-world-test; then
    echo "✓ Clone successful"
    
    if [ -d "hello-world-test" ]; then
        cd hello-world-test
        echo "Commit count: $(git rev-list --count HEAD)"
        echo "Current branch: $(git branch --show-current)"
        echo "All branches: $(git branch -a)"
        echo "Repository size: $(du -sh . | cut -f1)"
        cd ..
    fi
    
    # Cleanup
    rm -rf hello-world-test
    echo "✓ Test completed successfully"
else
    echo "✗ Clone failed"
    exit 1
fi

# Cleanup temp directory
cd /
rm -rf "$TEMP_DIR"
