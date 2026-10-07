import sys
import os
from pathlib import Path
import unittest

sys.stdout.reconfigure(encoding='utf-8')

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import tempfile
import time
import json
from core.license import LicenseManager, get_machine_guid, TRIAL_DAYS, FREE_MAX_BATCH_FILES, generate_valid_key
from i18n import i18n

class TestLicenseModule(unittest.TestCase):
    def setUp(self):
        self.orig_lang = i18n.current_language
        i18n.apply_language("zh_TW")
        self.temp_dir = tempfile.TemporaryDirectory()
        self.old_appdata = os.environ.get("APPDATA")
        os.environ["APPDATA"] = self.temp_dir.name
        LicenseManager._instance = None
        self.mgr = LicenseManager.get_instance()

    def tearDown(self):
        LicenseManager._instance = None
        if self.old_appdata:
            os.environ["APPDATA"] = self.old_appdata
        self.temp_dir.cleanup()
        i18n.apply_language(self.orig_lang)

    def test_machine_guid(self):
        guid = get_machine_guid()
        self.assertIsInstance(guid, str)
        self.assertGreater(len(guid), 10)
        print("OK: test_machine_guid passed:", guid[:16] + "...")

    def test_trial_initialization(self):
        self.assertEqual(TRIAL_DAYS, 7)
        self.assertEqual(self.mgr.get_trial_days_left(), 7)
        self.assertTrue(self.mgr.is_unlimited())
        self.assertEqual(self.mgr.get_plan_type(), "trial")
        self.assertFalse(self.mgr.is_activated())
        self.assertTrue(self.mgr.trial_file.exists())
        print("OK: test_trial_initialization passed: 7 days trial active")

    def test_trial_expiry_downgrade(self):
        eight_days_ago = time.time() - (8 * 86400)
        data = {
            "installed_at": eight_days_ago,
            "last_seen": eight_days_ago + 100,
            "machine_id": self.mgr.machine_id,
            "checksum": self.mgr._calc_trial_checksum(eight_days_ago, eight_days_ago + 100)
        }
        with open(self.mgr.trial_file, "w", encoding="utf-8") as f:
            json.dump(data, f)

        self.mgr._check_trial_status()
        self.assertEqual(self.mgr.get_trial_days_left(), 0)
        self.assertFalse(self.mgr.is_unlimited())
        self.assertEqual(self.mgr.get_plan_type(), "free")
        print("OK: test_trial_expiry_downgrade passed: successfully downgraded to free")

    def test_trial_anti_clock_rollback(self):
        now = time.time()
        future_seen = now + (2 * 86400)
        data = {
            "installed_at": now,
            "last_seen": future_seen,
            "machine_id": self.mgr.machine_id,
            "checksum": self.mgr._calc_trial_checksum(now, future_seen)
        }
        with open(self.mgr.trial_file, "w", encoding="utf-8") as f:
            json.dump(data, f)

        self.mgr._check_trial_status()
        self.assertFalse(self.mgr.is_unlimited())
        self.assertEqual(self.mgr.get_trial_days_left(), 0)
        print("OK: test_trial_anti_clock_rollback passed: detected clock rollback")

    def test_downgrade_batch_limit(self):
        # 試用期內無限制
        allowed, _ = self.mgr.check_batch_limit(100)
        self.assertTrue(allowed)

        # 降級為免費版
        self.mgr._is_trial_valid = False
        self.mgr._is_pro = False

        # <= 10 檔允許
        allowed, _ = self.mgr.check_batch_limit(10)
        self.assertTrue(allowed)

        # > 10 檔拒絕
        allowed, msg = self.mgr.check_batch_limit(11)
        self.assertFalse(allowed)
        self.assertTrue(f"{FREE_MAX_BATCH_FILES} 個檔案" in msg or f"{FREE_MAX_BATCH_FILES} files" in msg, f"Expected 10 files limit in msg: {msg}")
        print("OK: test_downgrade_batch_limit passed: 10 files limit enforced")

    def test_downgrade_rules_limit(self):
        self.mgr._is_trial_valid = False
        self.mgr._is_pro = False

        # 基礎規則永久免費
        for r in ["ReplaceRule", "PrefixSuffixRule", "CaseRule", "TrimRule", "SanitizeRule", "SerialRule"]:
            allowed, _ = self.mgr.check_rule_allowed(r, {})
            self.assertTrue(allowed, f"{r} 應永久免費開放")

        # 進階規則被限制
        allowed, msg = self.mgr.check_rule_allowed("MetadataRule", {})
        self.assertFalse(allowed)
        self.assertTrue("中繼資料" in msg or "Metadata" in msg, f"Expected metadata warning in msg: {msg}")

        allowed, msg = self.mgr.check_rule_allowed("PinyinRule", {})
        self.assertFalse(allowed)
        self.assertTrue("拼音" in msg or "Pinyin" in msg, f"Expected pinyin warning in msg: {msg}")

        allowed, msg = self.mgr.check_rule_allowed("ReplaceRule", {"use_regex": True})
        self.assertFalse(allowed)
        self.assertTrue("正規表達式" in msg or "Regex" in msg or "Regular" in msg, f"Expected regex warning in msg: {msg}")
        print("OK: test_downgrade_rules_limit passed: pro rules restricted, basic rules free")

    def test_pro_unlimited(self):
        self.mgr._is_pro = True
        self.mgr._is_trial_valid = False

        self.assertTrue(self.mgr.is_unlimited())
        self.assertEqual(self.mgr.get_plan_type(), "pro")

        allowed, _ = self.mgr.check_batch_limit(99999)
        self.assertTrue(allowed)

        allowed, _ = self.mgr.check_rule_allowed("MetadataRule")
        self.assertTrue(allowed)
        allowed, _ = self.mgr.check_rule_allowed("PinyinRule")
        self.assertTrue(allowed)
        allowed, _ = self.mgr.check_rule_allowed("ReplaceRule", {"use_regex": True})
        self.assertTrue(allowed)
        print("OK: test_pro_unlimited passed: pro plan unlocked all")

    def test_generate_valid_key(self):
        key = generate_valid_key(seed="K7R9", prefix="KR")
        self.assertTrue(key.startswith("KR-K7R9-2026-"))
        self.assertEqual(len(key), 17)
        print("OK: test_generate_valid_key passed:", key)

if __name__ == "__main__":
    unittest.main()
