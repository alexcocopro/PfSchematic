from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from Diagramador import build_diagram_payload, load_pfsense_config


class DiagramadorTests(unittest.TestCase):
    def test_full_demo_config_loads_firewall_rules(self):
        config = load_pfsense_config(ROOT / "muestra" / "demo-pfschematic.xml")

        self.assertEqual(config["stats"]["total_rules"], 5)
        self.assertEqual(config["stats"]["actions"].get("pass", 0), 2)
        self.assertEqual(config["stats"]["actions"].get("block", 0), 1)
        self.assertEqual(config["stats"]["actions"].get("reject", 0), 1)
        self.assertEqual(config["stats"]["actions"].get("unknown", 0), 1)
        self.assertEqual(config["stats"]["interface_count"], 3)
        self.assertEqual(config["stats"]["alias_count"], 4)

    def test_filter_only_export_is_supported(self):
        config = load_pfsense_config(ROOT / "muestra" / "filter-demo-pfschematic.xml")

        self.assertEqual(config["root_tag"], "filter")
        self.assertEqual(config["stats"]["total_rules"], 2)

    def test_diagram_payload_contains_nodes_and_edges(self):
        config = load_pfsense_config(ROOT / "muestra" / "demo-pfschematic.xml")
        payload = build_diagram_payload(config)

        self.assertEqual(len(payload["edges"]), 5)
        self.assertGreater(len(payload["nodes"]), 1)
        self.assertIn("rules", payload)
        self.assertIn("aliases", payload)
        self.assertEqual(payload["edges"][0]["ruleNumber"], 1)
        self.assertIn("firstRule", payload["nodes"][0])
        self.assertIn("ruleNumbers", payload["nodes"][0])

    def test_alias_members_are_available_for_exploration(self):
        config = load_pfsense_config(ROOT / "muestra" / "demo-pfschematic.xml")
        payload = build_diagram_payload(config)

        alias = payload["aliases"]["PUERTOS_WEB"]
        self.assertEqual(alias["type"], "port")
        self.assertEqual(alias["entries"][0]["value"], "80")
        self.assertEqual(alias["entries"][0]["kind"], "Puerto")
        self.assertEqual(alias["entries"][1]["description"], "HTTPS")


if __name__ == "__main__":
    unittest.main()
