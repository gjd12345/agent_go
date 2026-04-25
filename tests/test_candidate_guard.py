import unittest

from eoh_go.eoh_runner.candidate_guard import classify_candidate, select_best_candidate


class CandidateGuardTests(unittest.TestCase):
    def test_marks_abnormal_low_and_early_break_as_suspicious(self) -> None:
        code = """
func InsertShips(dispatch Dispatch, oris, dess []Station, total_ship int) Dispatch {
    for j := range oris {
        bestIndex := -1
        if bestIndex == -1 {
            break
        }
        _ = j
    }
    dispatch.RenewnTotalCost()
    return dispatch
}
"""
        status = classify_candidate(
            {"objective": 10.5, "code": code},
            seed_j=664.0,
            invalid_threshold=1e8,
            suspicious_low_ratio=0.3,
        )

        self.assertEqual(status["status"], "suspicious")
        self.assertIn("suspicious_low_objective", status["flags"])
        self.assertIn("early_break_after_failed_insert", status["flags"])

    def test_marks_penalty_objective_as_invalid(self) -> None:
        status = classify_candidate(
            {"objective": 1e9, "code": "func InsertShips(dispatch Dispatch, oris, dess []Station, total_ship int) Dispatch { return dispatch }"},
            seed_j=664.0,
            invalid_threshold=1e8,
        )

        self.assertEqual(status["status"], "invalid")
        self.assertIn("penalty_objective", status["flags"])

    def test_marks_missing_total_cost_refresh_as_suspicious(self) -> None:
        status = classify_candidate(
            {"objective": 600.0, "code": "func InsertShips(dispatch Dispatch, oris, dess []Station, total_ship int) Dispatch { return dispatch }"},
            seed_j=664.0,
            invalid_threshold=1e8,
        )

        self.assertEqual(status["status"], "suspicious")
        self.assertIn("missing_total_cost_refresh", status["flags"])

    def test_marks_negative_external_j_as_suspicious(self) -> None:
        code = """
func InsertShips(dispatch Dispatch, oris, dess []Station, total_ship int) Dispatch {
    dispatch.RenewnTotalCost()
    return dispatch
}
"""
        status = classify_candidate(
            {"objective": 500.0, "code": code},
            seed_j=80.0,
            candidate_j=-5.0,
            invalid_threshold=1e8,
        )

        self.assertEqual(status["status"], "suspicious")
        self.assertIn("negative_external_j", status["flags"])

    def test_selects_lowest_non_suspicious_candidate(self) -> None:
        good_code = """
func InsertShips(dispatch Dispatch, oris, dess []Station, total_ship int) Dispatch {
    dispatch.RenewnTotalCost()
    return dispatch
}
"""
        suspicious_code = """
func InsertShips(dispatch Dispatch, oris, dess []Station, total_ship int) Dispatch {
    if bestIndex == -1 { break }
    dispatch.RenewnTotalCost()
    return dispatch
}
"""
        population = [
            {"objective": 10.5, "code": suspicious_code},
            {"objective": 557.9, "code": good_code},
            {"objective": 594.0, "code": good_code},
        ]

        selected, statuses = select_best_candidate(
            population,
            seed_j=664.0,
            invalid_threshold=1e8,
            suspicious_low_ratio=0.3,
        )

        self.assertIs(selected, population[1])
        self.assertEqual(statuses[0]["status"], "suspicious")
        self.assertEqual(statuses[1]["status"], "valid")


if __name__ == "__main__":
    unittest.main()
