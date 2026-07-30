import unittest
from app.coordinator.coordinator import coordinator
from app.schemas import IntentType, TemporalMode


class TestCoordinator(unittest.TestCase):
    def test_routing_schedule(self):
        decision = coordinator.route_request("kapan jadwal ujian?")
        self.assertEqual(decision.agent_id, "schedule")

    def test_routing_admin(self):
        decision = coordinator.route_request("cara mengajukan cuti")
        self.assertEqual(decision.agent_id, "admin")

    def test_routing_academic(self):
        decision = coordinator.route_request("syarat kelulusan skripsi")
        self.assertEqual(decision.agent_id, "academic")

    def test_process_request(self):
        res = coordinator.process_request("jadwal kuliah")
        self.assertIn(res["status"], ["SUCCESS", "PARTIAL"])
        self.assertIn("Schedule", res["agent"])

    def test_multi_intent_classification(self):
        intents = coordinator.classify_intents("jadwal kuliah dan syarat kelulusan")
        self.assertIn(IntentType.SCHEDULE, intents)
        self.assertIn(IntentType.ACADEMIC, intents)

    def test_temporal_classification(self):
        mode = coordinator.classify_temporal_mode("jadwal semester lalu")
        self.assertEqual(mode, TemporalMode.HISTORICAL)

        mode = coordinator.classify_temporal_mode("jadwal saat ini")
        self.assertEqual(mode, TemporalMode.CURRENT)

    def test_decomposition(self):
        routing = coordinator.route_and_process("jadwal kuliah dan syarat kelulusan")
        self.assertGreaterEqual(len(routing.subqueries), 2)
        agents = [sq.agent for sq in routing.subqueries]
        self.assertIn("schedule", agents)
        self.assertIn("academic", agents)


if __name__ == "__main__":
    unittest.main()
