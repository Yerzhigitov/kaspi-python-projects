import unittest

from logstats import analyze, percentile


class LogStatsTest(unittest.TestCase):
    def test_analyze(self):
        with open("sample.log", encoding="utf-8") as f:
            r = analyze(f)
        self.assertEqual(r["total"], 7)
        self.assertEqual(r["malformed"], 1)
        self.assertEqual(r["statuses"], {"2xx": 5, "5xx": 1, "4xx": 1})
        self.assertEqual(r["slowest"][0][0], "POST /api/pay")
        self.assertIn("GET /api/users/{id}", [s[0] for s in r["slowest"]])

    def test_percentile(self):
        vals = list(range(1, 101))
        self.assertEqual(percentile(vals, 50), 50)
        self.assertEqual(percentile(vals, 95), 95)
        self.assertEqual(percentile([], 95), 0)


if __name__ == "__main__":
    unittest.main()
