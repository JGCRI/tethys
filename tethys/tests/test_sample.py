import unittest

from tethys.sample import sum_ints


class TestSample(unittest.TestCase):

    def test_sum_ints(self):
        """Test to make sure `sum_ints` returns the expected value."""

        int_result = sum_ints(1, 2)

        # test equality for the output
        self.assertEqual(int_result, 3, msg="Tests not equal")


if __name__ == '__main__':
    unittest.main()
