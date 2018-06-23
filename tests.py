import sys
import unittest

if __name__ == '__main__':
    # import test modules
    import tests.analysisperiod_test as analysisperiod_test
    import tests.epw_test as epw_test
    import tests.location_test as location_test
    import tests.sunpath_test as sunpath_test

    # initialise the test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # add the tests to the test TestSuite
    suite.addTests(loader.loadTestsFromModule(analysisperiod_test))
    suite.addTests(loader.loadTestsFromModule(epw_test))
    suite.addTests(loader.loadTestsFromModule(location_test))
    suite.addTests(loader.loadTestsFromModule(sunpath_test))

    # initialise a runner, pass it your suite and run it
    runner = unittest.TextTestRunner(verbosity=3)
    result = runner.run(suite)

    # return the results of the test to travis
    sys.exit(not result.wasSuccessful())
