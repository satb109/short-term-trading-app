import unittest
from unittest.mock import patch

import pandas as pd

import rsi_alert


class CheckTickerTests(unittest.TestCase):
    def test_check_ticker_handles_multiindex_close_column(self):
        index = pd.date_range("2024-01-01", periods=20, freq="D")
        values = [100 + i * 0.5 for i in range(20)]
        data = pd.DataFrame({("Close", "TITAN.NS"): values}, index=index)
        data.columns = pd.MultiIndex.from_tuples(
            [("Close", "TITAN.NS")], names=["Price", "Ticker"]
        )

        with patch.object(rsi_alert.yf, "download", return_value=data):
            result = rsi_alert.check_ticker("TITAN.NS")

        self.assertEqual(result["ticker"], "TITAN.NS")
        self.assertIn("prev_rsi", result)
        self.assertIn("curr_rsi", result)


if __name__ == "__main__":
    unittest.main()
