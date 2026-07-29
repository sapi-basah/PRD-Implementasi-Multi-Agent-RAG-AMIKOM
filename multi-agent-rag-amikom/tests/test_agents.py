import unittest
from app.agents.academic import academic_agent
from app.agents.schedule import schedule_agent
from app.agents.admin import admin_agent

class TestAgents(unittest.TestCase):
    def test_academic_agent(self):
        res = academic_agent.process_request("syarat kelulusan")
        self.assertEqual(res["status"], "SUCCESS")
        self.assertIn("Academic Agent", res["agent"])
        # Could check if evidence is returned, but depends on DB
        if res["evidence"]:
            self.assertEqual(res["evidence"][0].lifecycle, "ACTIVE")
            
    def test_schedule_agent(self):
        res = schedule_agent.process_request("jadwal kuliah")
        self.assertEqual(res["status"], "SUCCESS")
        
    def test_admin_agent(self):
        res = admin_agent.process_request("cara cuti")
        self.assertEqual(res["status"], "SUCCESS")

if __name__ == "__main__":
    unittest.main()
