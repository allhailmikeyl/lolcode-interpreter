# CMSC 124 - ST-5L PROJECT
# Runs every .lol file in the tests folder through analyze() and reports PASS or FAIL
# A file named fail_something.lol must produce an error; every other file must parse with no error
# WAIT means a parser rule is not written yet, so that file cannot be judged

import os # os lets us list the files in the tests folder
from analyzer import analyze

def main():
    passed = 0
    failed = 0
    waiting = 0

    for name in sorted(os.listdir("tests")):
        if not name.endswith(".lol"):
            continue

        with open(os.path.join("tests", name)) as f:
            source = f.read()

        error = analyze(source)["error"] # None, or (kind, line, message)

        # A rule nobody has written yet: do not count it either way
        if error is not None and "not written yet" in error[2]:
            waiting += 1
            print("WAIT  " + name.ljust(34) + error[2])
            continue

        should_fail = name.startswith("fail_")
        did_fail = error is not None

        if did_fail == should_fail:
            passed += 1
            label = "PASS  "
        else:
            failed += 1
            label = "FAIL  "

        if error is None:
            detail = "parses"
        else:
            detail = error[0] + " (line " + str(error[1]) + "): " + error[2]
        print(label + name.ljust(34) + detail)

    print()
    print(str(passed) + " passed, " + str(failed) + " failed, " + str(waiting) + " waiting")

if __name__ == "__main__":
    main()
