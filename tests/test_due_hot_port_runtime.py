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

    def test_mega_data_updates_ui_without_restart(self):
        widget = _FakeWidget()
        fake_self = SimpleNamespace(
            current_values={},
            screen_stack=SimpleNamespace(currentWidget=lambda: widget),
        )

        HemodialysisHMI.on_mega_cond_data(fake_self, "megaCondSensor", 1234.0)
        HemodialysisHMI.on_mega_cond_data(fake_self, "megaTempSensor", 456.0)

        self.assertEqual(fake_self.current_values.get("megaCondSensor"), 1234.0)
        self.assertEqual(fake_self.current_values.get("megaTempSensor"), 456.0)
        self.assertGreaterEqual(widget.called, 2)

    def test_pattern_data_updates_ui_without_restart(self):
        widget = _FakeWidget()
        fake_self = SimpleNamespace(
            current_values={},
            screen_stack=SimpleNamespace(currentWidget=lambda: widget),
        )

        HemodialysisHMI.on_pattern_data(fake_self, "patternCondSensor", 10.0)
        HemodialysisHMI.on_pattern_data(fake_self, "patternTempSensor", 20.0)

        self.assertEqual(fake_self.current_values.get("patternCondSensor"), 10.0)
        self.assertEqual(fake_self.current_values.get("patternTempSensor"), 20.0)
        self.assertGreaterEqual(widget.called, 2)

    def test_comm_screen_routing_updates_led_controller(self):
        fake_main = SimpleNamespace(
            serial_comm=_CaptureUpdateConfig(),
            pattern_sensor=_CaptureUpdateConfig(),
            mega_cond_sensor=_CaptureUpdateConfig(),
            bioz_urea_controller=_CaptureUpdateConfig(),
            led_bar=_CaptureUpdateConfig(),
        )

        HemodialysisHMI.handle_comm_config_change(fake_main, "LED_CONTROLLER", "COM7", True)

        self.assertEqual(fake_main.led_bar.calls, [("COM7", True)])

    def test_comm_screen_routing_updates_main_and_mega_controllers(self):
        fake_main = SimpleNamespace(
            serial_comm=_CaptureUpdateConfig(),
            pattern_sensor=_CaptureUpdateConfig(),
            mega_cond_sensor=_CaptureUpdateConfig(),
            bioz_urea_controller=_CaptureUpdateConfig(),
            led_bar=_CaptureUpdateConfig(),
        )

        HemodialysisHMI.handle_comm_config_change(fake_main, "MAIN_CONTROL", "COM9", True)
        HemodialysisHMI.handle_comm_config_change(fake_main, "MEGA_CONDUCTIVITY", "COM8", True)

        self.assertEqual(fake_main.serial_comm.calls, [("COM9", True)])
        self.assertEqual(fake_main.mega_cond_sensor.calls, [("COM8", True)])


if __name__ == "__main__":
    unittest.main()
