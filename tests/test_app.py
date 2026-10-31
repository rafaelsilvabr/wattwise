import copy
from io import BytesIO
import json
import unittest
from unittest.mock import patch

from app import SAMPLE, advise, analyze, ollama_model, ollama_status


class AppTests(unittest.TestCase):
    def setUp(self):
        self.config = copy.deepcopy(SAMPLE)

    def test_single_change_keeps_other_household_uses(self):
        report = analyze(self.config)
        best = report["opportunities"][0]
        self.assertEqual(best["id"], "ac")
        self.assertEqual(best["energy_reduction_kwh"], 27)
        self.assertAlmostEqual(best["household_after_kwh"], report["total"]["baseline_kwh"] - 27)
        self.assertNotIn("work", [c["id"] for c in report["opportunities"]])

    def test_family_appliances_use_average_power_and_total_daily_shower_time(self):
        report = analyze(self.config)
        rows = {row["id"]: row for row in report["devices"]}
        self.assertEqual(rows["shower"]["baseline_kwh"], 82.5)
        self.assertEqual(rows["shower"]["energy_reduction_kwh"], 16.5)
        self.assertEqual(rows["fridge"]["baseline_kwh"], 50.4)
        self.assertEqual(rows["fridge"]["hours"], 24)
        self.assertTrue(rows["fridge"]["protected"])
        self.assertNotIn("fridge", [c["id"] for c in report["opportunities"]])
        self.assertEqual(report["total"]["baseline_kwh"], 480.24)

    def test_cannot_reduce_a_protected_use(self):
        self.config["devices"][0]["plannedHours"] = 1
        with self.assertRaisesRegex(ValueError, "protegido"):
            analyze(self.config)

    def test_duplicate_ids_and_invalid_hours_are_rejected(self):
        self.config["devices"][1]["id"] = "work"
        with self.assertRaises(ValueError):
            analyze(self.config)
        self.config = copy.deepcopy(SAMPLE)
        self.config["devices"][0]["hours"] = 25
        with self.assertRaises(ValueError):
            analyze(self.config)

    def test_zero_price_keeps_energy_opportunity(self):
        self.config["rate"] = 0
        report = analyze(self.config)
        self.assertGreater(report["opportunities"][0]["energy_reduction_kwh"], 0)
        self.assertEqual(report["opportunities"][0]["modeled_variable_cost_reduction_brl"], 0)

    def model_response(self, candidate_id="tv", decision="recommend"):
        content = json.dumps({"decision": decision, "candidate_id": candidate_id, "reason": "Compatível com a rotina.",
                              "next_step": "Confirme o período de uso.", "question": "Esse ajuste é possível?"})
        return BytesIO(json.dumps({"message": {"content": content}}).encode())

    def test_model_selects_only_precomputed_candidate(self):
        with patch("app.request.urlopen", return_value=self.model_response()) as mocked:
            result = advise(self.config)
            payload = json.loads(mocked.call_args.args[0].data)
        self.assertFalse(payload["stream"])
        self.assertFalse(payload["think"])
        self.assertIn("candidate_id", payload["format"]["properties"])
        self.assertEqual(result["provider"], "ollama")
        self.assertEqual(result["candidate"]["id"], "tv")
        self.assertEqual(result["candidate"]["energy_reduction_kwh"], 3)
        self.assertEqual(result["candidate"]["modeled_variable_cost_reduction_brl"], 3.15)
        self.assertEqual(result["skill"]["name"], "household-energy-coach")
        self.assertEqual(result["experiment"]["duration_days"], 7)

    def test_invalid_or_protected_model_choice_is_rejected(self):
        for identity in ["invented", "work"]:
            with self.subTest(identity=identity), patch("app.request.urlopen", return_value=self.model_response(identity)):
                with self.assertRaisesRegex(ValueError, "fora das opções"):
                    advise(self.config)

    def test_missing_model_does_not_report_ready(self):
        with patch("app.request.urlopen", side_effect=ConnectionRefusedError):
            self.assertFalse(ollama_status()["available"])

    def test_cloud_tags_are_not_accepted_as_local(self):
        with patch.dict("os.environ", {"OLLAMA_MODEL": "gemma4:31b-cloud"}):
            with self.assertRaises(ValueError):
                ollama_model()

    def test_no_eligible_change_can_be_clarified_without_inventing_savings(self):
        for device in self.config["devices"]:
            device["plannedHours"], device["plannedWatts"] = device["hours"], device["watts"]
        with patch("app.request.urlopen", return_value=self.model_response("none", "clarify")):
            result = advise(self.config)
        self.assertEqual(result["decision"], "clarify")
        self.assertIsNone(result["candidate"])
        self.assertIsNone(result["experiment"])

    def test_answers_and_real_skill_are_loaded_into_model_request(self):
        self.config["advisorAnswers"] = [{"question": "Qual uso pode mudar?", "answer": "A televisão pode ser reduzida."}]
        with patch("app.request.urlopen", return_value=self.model_response()) as mocked:
            result = advise(self.config)
        payload = json.loads(mocked.call_args.args[0].data)
        from energy_skill import load_skill
        self.assertEqual(payload["messages"][0]["content"], load_skill()["body"])
        supplied = json.loads(payload["messages"][1]["content"])
        self.assertEqual(supplied["answers"], self.config["advisorAnswers"])
        self.assertEqual(result["answers_considered"], 1)

    def test_clarification_cannot_smuggle_an_action(self):
        with patch("app.request.urlopen", return_value=self.model_response("ac", "clarify")):
            with self.assertRaises(ValueError):
                advise(self.config)

    def test_missing_routine_constrains_generation_to_a_question(self):
        self.config["context"] = ""
        with patch("app.request.urlopen", return_value=self.model_response("none", "clarify")) as mocked:
            result = advise(self.config)
        payload = json.loads(mocked.call_args.args[0].data)
        self.assertEqual(payload["format"]["properties"]["decision"]["enum"], ["clarify"])
        self.assertEqual(payload["format"]["properties"]["candidate_id"]["enum"], ["none"])
        self.assertIsNone(result["candidate"])


if __name__ == "__main__":
    unittest.main()
