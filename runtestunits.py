"""Run test units."""
import os
import subprocess


def main(verbose=True, pathToPython="c:\\python27"):
    """Execute all test files inside tests folder."""
    # change directory to the file directory. The file should be in root directory
    _curdir = os.path.split(__file__)[0]
    os.chdir(_curdir)

    # find all files in tests folder
    testFiles = [f[:-3] for f in os.listdir('./tests') if f[-3:] == ".py" and f[0] != "_"]

    # edit __init__ file inside tests folder
    with open(os.path.join(_curdir, "tests/__init__.py"), "w") as initf:
        initf.write("import " + ",".join(testFiles))

    # execute each test file
    cmdBase = '%s\\python -m unittest -v tests.%s'
    if not verbose:
        cmdBase = cmdBase.replace("-v", "")

    for f in testFiles:
        print "running test for %s"%f
        cmd = cmdBase % (pathToPython, f)
        subprocess.Popen(cmd, shell=True)

if __name__ == "__main__":
    print "Running tests..."
    main(verbose=False)
