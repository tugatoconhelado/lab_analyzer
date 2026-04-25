from enum import IntFlag, auto

class AssetType(IntFlag):
    NONE = 0
    DATASET = auto()   # 1
    LINK = auto()      # 2
    TRACE = auto()     # 4
    FIT = auto()       # 8
    GROUP = auto()     # 16
    MODEL = auto()     # 32
    PLOT = auto()      # 64