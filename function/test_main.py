import unittest
from main import visitor_count


class TestFunction(unittest.TestCase):
    def test_cloud_function(self):
        self.assertEqual(visitor_count("test")[1],200)

if __name__ == '__main__':
    unittest.main()