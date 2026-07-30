import unittest
from app.agents.academic import academic_agent
from app.agents.schedule import schedule_agent
from app.agents.admin import admin_agent
from app.schemas import SubQueryTask, TemporalMode


class TestAgents(unittest.TestCase):
    def test_academic_agent(self):
        res = academic_agent.process_request("syarat kelulusan")
        self.assertEqual(res["status"], "SUCCESS")
        self.assertIn("Academic", res["agent"])
        if res["evidence"]:
            self.assertEqual(res["evidence"][0].lifecycle, "ACTIVE")

    def test_academic_agent_typed(self):
        task = SubQueryTask(
            sub_query="syarat kelulusan S1 Informatika",
            agent="academic",
            namespace=["active_academic"],
            temporal_mode=TemporalMode.CURRENT,
            k=5,
        )
        result = academic_agent.process(task)
        self.assertIn(result.status.value, ["SUCCESS", "PARTIAL"])
        self.assertEqual(result.agent, "AcademicAgent")

    def test_schedule_agent(self):
        res = schedule_agent.process_request("jadwal kuliah")
        self.assertIn(res["status"], ["SUCCESS", "PARTIAL"])

    def test_schedule_agent_historical(self):
        task = SubQueryTask(
            sub_query="jadwal kuliah semester lalu",
            agent="schedule",
            namespace=["archive_schedule"],
            temporal_mode=TemporalMode.HISTORICAL,
            k=5,
        )
        result = schedule_agent.process(task)
        self.assertEqual(result.agent, "ScheduleAgent")
        # All evidence should be archive only
        for ev in result.evidence:
            self.assertEqual(ev.retrieval_namespace, "archive_schedule")

    def test_admin_agent(self):
        res = admin_agent.process_request("cara cuti")
        self.assertIn(res["status"], ["SUCCESS", "PARTIAL"])

    def test_admin_agent_refuses_personal(self):
        task = SubQueryTask(
            sub_query="nilai saya berapa?",
            agent="administration",
            namespace=["active_administration"],
            temporal_mode=TemporalMode.CURRENT,
            k=5,
        )
        result = admin_agent.process(task)
        self.assertEqual(result.status.value, "REFUSED")
        self.assertEqual(result.response_mode.value, "HANDOFF")


if __name__ == "__main__":
    unittest.main()
