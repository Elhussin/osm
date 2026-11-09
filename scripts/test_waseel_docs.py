"""Tests for privacy-preserving documentation extraction, not a provider adapter."""
import json
import unittest
import subprocess
from check_waseel_docs import structure, summarize_request, collect, ROOT


class ExtractionTests(unittest.TestCase):
    def test_no_sample_values_in_structure(self):
        result = json.dumps(structure({"beneficiary": {"fullName": "PRIVATE_SENTINEL"}, "items": [{"net": 12345.67}, {"newField": True}]}))
        self.assertNotIn("PRIVATE_SENTINEL", result)
        self.assertNotIn("12345.67", result)
        self.assertIn("items[].newField", result)

    def test_empty_array_null_zero_false_distinguished(self):
        result = structure({"items": [], "name": None, "net": 0, "flag": False})
        self.assertIn({"path": "items", "type": "list"}, result)
        self.assertIn({"path": "name", "type": "null"}, result)
        self.assertIn({"path": "net", "type": "int"}, result)
        self.assertIn({"path": "flag", "type": "bool"}, result)

    def test_credentials_query_values_and_provider_are_omitted(self):
        result = summarize_request("Authentication", {
            "method": "POST", "url": {"raw": "https://api.stg-eclaims.waseel.com/approvals/providers/PRIVATE_ID/approval?token=PRIVATE_QUERY", "query": [{"key": "token", "value": "PRIVATE_QUERY"}]},
            "auth": {"type": "bearer", "bearer": [{"value": "PRIVATE_TOKEN"}]},
            "body": {"raw": json.dumps({"username": "PRIVATE_USER", "password": "PRIVATE_PASSWORD"})},
        })
        serialized = json.dumps(result)
        for secret in ("PRIVATE_ID", "PRIVATE_QUERY", "PRIVATE_TOKEN", "PRIVATE_USER", "PRIVATE_PASSWORD"):
            self.assertNotIn(secret, serialized)
        self.assertTrue(result["contains_nonempty_auth_value"])

    def test_unreviewed_host_is_rejected(self):
        with self.assertRaises(ValueError):
            summarize_request("unknown", {"method": "POST", "url": "https://example.invalid/test"})

    def test_invalid_json_body_is_not_silently_accepted(self):
        result = summarize_request("invalid", {"method": "POST", "url": "https://api.stg-eclaims.waseel.com/test", "body": {"raw": "{invalid PRIVATE_SENTINEL}"}})
        self.assertEqual("non_strict_json_requires_review", result["body_status"])
        self.assertNotIn("PRIVATE_SENTINEL", json.dumps(result))

    def test_actual_sources_cover_vision_and_separate_outcomes(self):
        report = collect()
        self.assertEqual(17, len(report["operations"]))
        vision = next(x for x in report["operations"] if x["name"].endswith("Preauthorization Request- vISION"))
        paths = {x["path"] for x in vision["body_structure"]}
        self.assertIn("visionPrescription.lensSpecifications[].sphere", paths)
        self.assertIn("items[].payerShare", paths)
        states = {x["source"]: x["states"] for x in report["sample_structures"]}
        self.assertEqual("partial", states["Approval_Response_Partial.json"]["status"])
        self.assertEqual("Processing Complete", states["Approval_Response_Partial.json"]["outcome"])
        self.assertEqual("pended", states["Approval_Response_Pended.json"]["status"])
        self.assertEqual("Error", states["Approval_Response_outcome_Error.json"]["outcome"])
        self.assertTrue(any(x["field"] == "visionPrescription.lensSpecifications.sphere" for x in report["workbook"]["field_locations"]))

    def test_raw_sources_are_ignored_and_not_tracked(self):
        ignored = subprocess.run(["git", "check-ignore", "Waseel_PI_Document/readm.md", "Fwd__Waseel_API_Document.zip"], cwd=ROOT, capture_output=True, text=True, check=True)
        self.assertEqual(2, len(ignored.stdout.splitlines()))
        tracked = subprocess.run(["git", "ls-files", "--", "Waseel_PI_Document", "Fwd__Waseel_API_Document.zip"], cwd=ROOT, capture_output=True, text=True, check=True)
        self.assertFalse(tracked.stdout.strip(), "Raw documentation must not be tracked; review private contents first.")


if __name__ == "__main__":
    unittest.main()
