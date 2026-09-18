import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).parents[1]
SHARED_PATH = ROOT / "insighioNode/apps/demo_console/scenario_enviro_utils.py"


class TestPulseCounterAdcBackend(unittest.TestCase):
    def test_hot_paths_do_not_call_firmware_specific_adc_methods(self):
        tree = ast.parse(SHARED_PATH.read_text())
        hot_function_names = {
            "execute_pulse_counter_measurements",
            "detect_stable_edge",
            "pulse_counter_thread",
        }

        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name in hot_function_names:
                called_attributes = {
                    child.func.attr for child in ast.walk(node) if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute)
                }
                self.assertNotIn("read_uv", called_attributes)
                self.assertNotIn("read_voltage", called_attributes)

    def test_firmware_specific_readers_are_isolated_to_import_time_selection(self):
        tree = ast.parse(SHARED_PATH.read_text())
        selection = next(node for node in tree.body if isinstance(node, ast.If) and "_fw_major" in ast.unparse(node.test))
        branch_readers = [node for branch in (selection.body, selection.orelse) for node in branch if isinstance(node, ast.FunctionDef)]
        reader_methods = {
            child.func.attr
            for reader in branch_readers
            for child in ast.walk(reader)
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute)
        }

        self.assertEqual([reader.name for reader in branch_readers], ["_read_pcnt_adc", "_read_pcnt_adc"])
        self.assertEqual(reader_methods, {"read_uv", "read_voltage"})

    def test_custom_firmware_scale_is_selected_once(self):
        tree = ast.parse(SHARED_PATH.read_text())
        selection = next(node for node in tree.body if isinstance(node, ast.If) and "_fw_major" in ast.unparse(node.test))
        assignments = {
            node.targets[0].id: ast.literal_eval(node.value)
            for node in selection.body
            if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
        }
        reader = next(node for node in selection.body if isinstance(node, ast.FunctionDef))
        read_call = next(
            child
            for child in ast.walk(reader)
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute) and child.func.attr == "read_voltage"
        )

        self.assertEqual([ast.literal_eval(argument) for argument in read_call.args], [1])
        self.assertEqual(
            assignments,
            {
                "_PCNT_HIGH_MASK": 0x800,
                "_PCNT_LOW_MASK": 0x400,
                "_PCNT_VOLTAGE_MAX": 3300,
                "_PCNT_RAW_TO_MILLIVOLTS_DIVISOR": 1,
            },
        )


if __name__ == "__main__":
    unittest.main()
