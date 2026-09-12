import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chains.robinhood import run_loop

if __name__ == "__main__":
    run_loop()