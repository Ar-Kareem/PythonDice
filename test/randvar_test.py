import randvar
from randvar import RV, roll

def test_RV_init():
    assert roll(1) == roll(1)