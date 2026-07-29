import unittest
from app.coordinator.coordinator import coordinator

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
        self.assertEqual(res["status"], "SUCCESS")
        self.assertIn("Schedule Agent", res["agent"])

if __name__ == "__main__":
    unittest.main()
