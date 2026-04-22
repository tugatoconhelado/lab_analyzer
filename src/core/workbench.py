import numpy as np
import os
import sys
from dataclasses import dataclass
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.core.structures import DataResult


class Workbench:

    def __init__(self) -> None:
        pass

    def load_to_workbench(self, data: DataResult):

        self.__setattr__(data.name, data)



if __name__ == '__main__':

    d1 = DataResult(
        name="test1"
    )
    d2 = DataResult(
        name="test2"
    )
    d3 = DataResult(
        name="test3"
    )
    d1.lala = 123
    bench = Workbench()
    bench.load_to_workbench(d1)
    bench.load_to_workbench(d2)
    bench.load_to_workbench(d3)
    print(vars(bench))
    print(bench.test2)
    print(bench)