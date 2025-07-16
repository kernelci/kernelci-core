#!/bin/bash
# git-operations.sh - Standardized git operations for KernelCI rootfs builds

# Optimized git clone function for CI environments
# Usage: git_clone_optimized <repository_url> <target_dir> [branch] [depth]
git_clone_optimized() {
    local repo_url="$1"
    local target_dir="$2"
    local branch="${3:-}"
    local depth="${4:-1}"
    
    if [ $# -lt 2 ]; then
        echo "Usage: git_clone_optimized <repo_url> <target_dir> [branch] [depth]"
        return 1
    fi
    
    echo "Cloning $repo_url (depth: $depth) to $target_dir"
    
    # If no branch specified, let git choose the default
    if [ -z "$branch" ]; then
        echo "No branch specified, using repository default"
        git clone \
            --depth="$depth" \
            --single-branch \
            "$repo_url" \
            "$target_dir"
    else
        echo "Using specified branch: $branch"
        git clone \
            --depth="$depth" \
            --single-branch \
            --branch="$branch" \
            "$repo_url" \
            "$target_dir"
    fi
}

# Wrapper for backward compatibility
git_clone() {
    if [[ $# -eq 2 && -z "${3:-}" ]]; then
        echo "Warning: Using deprecated git clone interface. Consider updating to git_clone_optimized"
        git_clone_optimized "$1" "$2"
    else
        git_clone_optimized "$@"
    fi
}
