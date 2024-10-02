from randvar import Seq


def test_at_num():
    assert Seq(2, 3) @ 1234 == 5
