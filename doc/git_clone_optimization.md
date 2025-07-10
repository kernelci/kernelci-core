## Overview

This document establishes standardized git clone operations for KernelCI rootfs builder scripts to reduce network traffic and improve build performance in CI environments.

## Problem Statement

Rootfs builder scripts currently use inconsistent git clone approaches:

```bash
# Found patterns across scripts:
git clone $BLKTEST_URL .                           # No optimization
git clone --depth 1 $GSTREAMER_URL .               # Partial optimization  
git clone --depth=1 $LIBCAMERA_URL .               # Different syntax
git clone $DEQP_RUNNER_GIT_URL --single-branch --no-checkout  # Mixed approach
git clone -b ${LTP_SHA} ${LTP_URL}                  # Branch-specific

# Changed into format of this optimal git options
git clone --depth=1 --single-branch [--branch=<branch>] <repository_url> <target_dir>
# I can use it as 
git_clone_optimized https://github.com/octocat/Hello-World.git hello-world-test

