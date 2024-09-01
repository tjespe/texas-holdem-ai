import unittest


loader = unittest.TestLoader()
suite = loader.discover("./", pattern="*_test.py")
print("Test cases:", suite.countTestCases())

runner = unittest.TextTestRunner()
runner.run(suite)
