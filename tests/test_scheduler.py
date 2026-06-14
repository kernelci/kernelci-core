# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2026 Collabora Limited

"""Unit tests for kernelci.scheduler edge-triggered matching (#2912)"""

import types
import unittest

from kernelci.scheduler import Scheduler


def _entry(event):
    """Build a minimal scheduler entry exposing an ``event`` mapping."""
    return types.SimpleNamespace(event=event)


def _scheduler(entries):
    """Build a Scheduler with a preset list of entries, bypassing __init__."""
    sched = Scheduler.__new__(Scheduler)
    sched._scheduler = entries
    return sched


class TestGetConfigsEdgeTrigger(unittest.TestCase):
    """get_configs() should fire on the transition into a matched state,
    not on every update that keeps the node in that state (#2912)."""

    KBUILD_AVAILABLE = {
        "channel": "node",
        "kind": "kbuild",
        "state": "available",
        "name": "kbuild-gcc-14-arm",
    }

    def _matches(self, entries, event, channel="node"):
        sched = _scheduler(entries)
        return list(sched.get_configs(event, channel))

    def test_created_event_matches(self):
        """A creation event in the matched state fires (rising edge)."""
        entry = _entry(self.KBUILD_AVAILABLE)
        event = {
            "op": "created",
            "kind": "kbuild",
            "state": "available",
            "name": "kbuild-gcc-14-arm",
        }
        self.assertEqual(self._matches([entry], event), [entry])

    def test_update_into_state_matches(self):
        """An update transitioning INTO the matched state fires."""
        entry = _entry(self.KBUILD_AVAILABLE)
        event = {
            "op": "updated",
            "kind": "kbuild",
            "state": "available",
            "name": "kbuild-gcc-14-arm",
            "previous_state": "running",
            "previous_result": None,
        }
        self.assertEqual(self._matches([entry], event), [entry])

    def test_update_keeping_state_does_not_match(self):
        """An update that keeps the already-matched state does NOT fire.

        This is the duplicate-job scenario from #2912: an artifact/timeout
        update on a node that is already `available`.
        """
        entry = _entry(self.KBUILD_AVAILABLE)
        event = {
            "op": "updated",
            "kind": "kbuild",
            "state": "available",
            "name": "kbuild-gcc-14-arm",
            "previous_state": "available",
            "previous_result": None,
        }
        self.assertEqual(self._matches([entry], event), [])

    def test_update_without_previous_state_is_level_triggered(self):
        """Older API events (no previous_*) fall back to level-triggered."""
        entry = _entry(self.KBUILD_AVAILABLE)
        event = {
            "op": "updated",
            "kind": "kbuild",
            "state": "available",
            "name": "kbuild-gcc-14-arm",
        }
        self.assertEqual(self._matches([entry], event), [entry])

    def test_result_rising_edge(self):
        """An entry matching state+result fires on the transition to done."""
        entry = _entry(
            {
                "channel": "node",
                "kind": "kbuild",
                "state": "done",
                "result": "pass",
            }
        )
        rising = {
            "op": "updated",
            "kind": "kbuild",
            "state": "done",
            "result": "pass",
            "previous_state": "available",
            "previous_result": None,
        }
        self.assertEqual(self._matches([entry], rising), [entry])

    def test_result_no_edge_when_already_done(self):
        """No fire when the node was already done/pass and is updated again."""
        entry = _entry(
            {
                "channel": "node",
                "kind": "kbuild",
                "state": "done",
                "result": "pass",
            }
        )
        no_edge = {
            "op": "updated",
            "kind": "kbuild",
            "state": "done",
            "result": "pass",
            "previous_state": "done",
            "previous_result": "pass",
        }
        self.assertEqual(self._matches([entry], no_edge), [])

    def test_non_matching_event(self):
        """An event that doesn't match the entry never fires."""
        entry = _entry(self.KBUILD_AVAILABLE)
        event = {
            "op": "updated",
            "kind": "kbuild",
            "state": "running",
            "name": "kbuild-gcc-14-arm",
            "previous_state": "running",
        }
        self.assertEqual(self._matches([entry], event), [])

    def test_channel_mismatch_skipped(self):
        """Entries for another channel are skipped."""
        entry = _entry(
            {"channel": "retry", "kind": "kbuild", "state": "available"}
        )
        event = {"op": "created", "kind": "kbuild", "state": "available"}
        self.assertEqual(self._matches([entry], event, channel="node"), [])

    def test_retry_event_without_op_is_level_triggered(self):
        """Retry events carry no ``op`` key and must always fire."""
        entry = _entry(self.KBUILD_AVAILABLE)
        # Synthesised retry event: parent node data with state forced
        # to available, no "op"/"previous_state".
        event = {
            "kind": "kbuild",
            "state": "available",
            "name": "kbuild-gcc-14-arm",
            "retry_counter": 1,
        }
        self.assertEqual(self._matches([entry], event), [entry])

    def test_non_dict_event_returns_nothing(self):
        """A non-dict event is handled gracefully."""
        self.assertEqual(
            self._matches([_entry(self.KBUILD_AVAILABLE)], None), []
        )


if __name__ == "__main__":
    unittest.main()
