from types import SimpleNamespace
import unittest

from connection.due_conductivity_sensor import DueConductivitySensor
from gui.appMainHemodialysis import HemodialysisHMI


class _FakeWidget:
    def __init__(self):
        self.called = 0
        self.last_values = None

    def update_values(self, values):
        self.called += 1
        self.last_values = dict(values)


class _CaptureUpdateConfig:
    def __init__(self):
        self.calls = []

    def update_config(self, port, enabled):
        self.calls.append((port, enabled))


class DueHotPortRuntimeTests(unittest.TestCase):
    def test_due_sensor_hot_port_config_lifecycle(self):
        sensor = DueConductivitySensor()
        state = {"start_called": 0, "stop_called": 0, "close_called": 0}

        sensor.start_reading = lambda: state.__setitem__("start_called", state["start_called"] + 1)
        sensor.stop = lambda: state.__setitem__("stop_called", state["stop_called"] + 1)
        sensor._close_port_resource = lambda: state.__setitem__("close_called", state["close_called"] + 1)

        sensor.running = False
        sensor._is_enabled = False
        sensor._user_selected_port = None
        sensor.update_config("COM5", True)
        self.assertEqual(state["start_called"], 1)

        sensor.running = True
        sensor._is_enabled = True
        sensor._user_selected_port = "COM5"
        sensor.update_config("COM6", True)
        self.assertEqual(state["close_called"], 1)

        sensor.running = True
        sensor._is_enabled = True
        sensor.update_config("COM6", False)
        self.assertEqual(state["stop_called"], 1)

    def test_due_data_updates_ui_without_restart(self):
        widget = _FakeWidget()
        fake_self = SimpleNamespace(
            current_values={},
            screen_stack=SimpleNamespace(currentWidget=lambda: widget),
        )

        HemodialysisHMI.on_due_cond_data(fake_self, "dueCondSensor", 1234.0)
        HemodialysisHMI.on_due_cond_data(fake_self, "dueTempSensor", 456.0)

        self.assertEqual(fake_self.current_values.get("dueCondSensor"), 1234.0)
        self.assertEqual(fake_self.current_values.get("dueTempSensor"), 456.0)
        self.assertGreaterEqual(widget.called, 2)

    def test_due_legacy_tags_are_normalized_to_canonical(self):
        widget = _FakeWidget()
        fake_self = SimpleNamespace(
            current_values={},
            screen_stack=SimpleNamespace(currentWidget=lambda: widget),
        )

        HemodialysisHMI.on_due_cond_data(fake_self, "dueCondRef", 10.0)
        HemodialysisHMI.on_due_cond_data(fake_self, "dueTempRef", 20.0)

        self.assertEqual(fake_self.current_values.get("dueCondSensor"), 10.0)
        self.assertEqual(fake_self.current_values.get("dueTempSensor"), 20.0)

    def test_comm_screen_routing_updates_due_controller(self):
        fake_main = SimpleNamespace(
            serial_comm=_CaptureUpdateConfig(),
            pattern_sensor=_CaptureUpdateConfig(),
            due_cond_sensor=_CaptureUpdateConfig(),
            bioz_urea_controller=_CaptureUpdateConfig(),
        )

        HemodialysisHMI.handle_comm_config_change(fake_main, "DUE_CONDUCTIVITY", "COM9", True)

        self.assertEqual(fake_main.due_cond_sensor.calls, [("COM9", True)])


if __name__ == "__main__":
    unittest.main()
