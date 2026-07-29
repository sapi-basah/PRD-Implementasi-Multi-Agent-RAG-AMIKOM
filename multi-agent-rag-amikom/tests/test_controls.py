import unittest
from app.controls.registry import control_registry
from app.controls.pre_control import pre_control
from app.controls.pii_checker import check_pii
from app.controls.scope_checker import check_out_of_scope

class TestControls(unittest.TestCase):
    def test_pii_checker(self):
        self.assertTrue(check_pii("NIM saya 23.11.5887, tolong bantu."))
        self.assertTrue(check_pii("Email saya budi@amikom.ac.id"))
        self.assertTrue(check_pii("Nomor HP 081234567890"))
        self.assertTrue(check_pii("KTP 1234567890123456"))
        self.assertFalse(check_pii("Bagaimana cara KRS?"))

    def test_scope_checker(self):
        self.assertTrue(check_out_of_scope("Bagaimana cara bayar SPP?"))
        self.assertTrue(check_out_of_scope("Info beasiswa terbaru?"))
        self.assertTrue(check_out_of_scope("Lowongan magang MBKM"))
        self.assertFalse(check_out_of_scope("Kapan jadwal ujian akhir?"))

    def test_pre_control_pii_refusal(self):
        res = pre_control.validate_request("NIM 23.11.5887")
        self.assertTrue(res.short_circuit)
        self.assertEqual(res.response_mode, "REFUSE")
        
    def test_pre_control_scope_refusal(self):
        res = pre_control.validate_request("cara bayar denda")
        self.assertTrue(res.short_circuit)
        self.assertEqual(res.response_mode, "REFUSE")
        
    def test_pre_control_cf002(self):
        res = pre_control.validate_request("Kalau IPK 2.00 apakah bisa lulus?")
        self.assertTrue(res.short_circuit)
        self.assertEqual(res.response_mode, "ESCALATE")
        self.assertIn("CF002", res.control_flags)

    def test_pre_control_g02(self):
        res = pre_control.validate_request("Jadwal uas belum keluar ya?")
        self.assertTrue(res.short_circuit)
        self.assertEqual(res.response_mode, "ABSTAIN")
        self.assertIn("G02", res.control_flags)

    def test_pre_control_normal(self):
        res = pre_control.validate_request("Bagaimana prosedur cuti akademik?")
        self.assertFalse(res.short_circuit)
        self.assertEqual(res.response_mode, "AUTO")

if __name__ == "__main__":
    unittest.main()
