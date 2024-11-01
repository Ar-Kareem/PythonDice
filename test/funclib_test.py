
import pytest

from dice_calc import anydice_casting, roll, RV, Seq, settings_reset


@pytest.fixture(autouse=True)
def settings_reset_fixture():
    settings_reset()


from dice_calc.funclib import absolute
def test_absolute():
    assert absolute(-3) == 3, 'abs [in docs]'
    a = RV((2, 1, 0, 1, 2, 3), (1, 1, 1, 1, 1, 1))
    assert RV.dices_are_equal(absolute(roll(6) - 3), a) and RV.dices_are_equal(abs(roll(6) - 3), a), 'abs [in docs]'  # type: ignore
    a = RV((0, 1, 2, 3, 4, 5), (3, 5, 4, 3, 2, 1))
    assert RV.dices_are_equal(abs(roll(6) - roll(6)), a) and RV.dices_are_equal(absolute(roll(6) - roll(6)), a), 'abs [in docs]'  # type: ignore

from dice_calc.funclib import contains
def test_contains():
    assert contains(Seq(range(1, 7)), 3), 'contains [in docs]'
    assert RV.dices_are_equal(contains(roll(3, 6), 6), RV((0, 1), (125, 91))), 'contains [in docs]'  # type: ignore
    assert RV.dices_are_equal(contains(Seq(1, 2, 3), roll(6)), RV((0, 1), (1, 1))), 'contains [in docs]'  # type: ignore

from dice_calc.funclib import count_in
def test_count_in():
    assert RV.dices_are_equal(count_in(Seq(1, 2), Seq(range(1, 7))), RV((2, ), (1, ))), "funclib count_in, 'obviously 2 matches' [in docs]"
    assert RV.dices_are_equal(count_in(3, roll(3, 6)), RV((0, 1, 2, 3), (125, 75, 15, 1))), "funclib count_in, 'rolling 3s on 3d6' [in docs]"  # type: ignore
    assert RV.dices_are_equal(count_in(Seq(2, 4, 6), roll(2, 6)), RV((0, 1, 2), (1, 2, 1))), "funclib count_in, 'rolling evens on 2d6' [in docs]"  # type: ignore
    assert RV.dices_are_equal(count_in(Seq(range(4, 7), 6), roll(6)), RV((0, 1, 2), (3, 2, 1))), "funclib count_in, 'rolling above 3 on a d6, counting 6s double' [in docs]"  # type: ignore

from dice_calc.funclib import reverse_VANILLA_SLOW as reverse
def test_reverse_vanilla():
    assert 1 @ Seq(range(1, 7)) == 1, 'reverse [in docs]'
    assert 1 @ reverse(Seq(range(1, 7))) == 6, 'reverse [in docs]'
    assert RV.dices_are_equal(reverse(roll(2, 6)), roll(2, 6)), 'reverse [in docs]'  # type: ignore

from dice_calc.funclib import reverse
def test_reverse():
    assert 1 @ Seq(range(1, 7)) == 1, 'reverse [in docs]'
    assert 1 @ reverse(Seq(range(1, 7))) == 6, 'reverse [in docs]'
    assert RV.dices_are_equal(reverse(roll(2, 6)), roll(2, 6)), 'reverse [in docs]'  # type: ignore

    assert RV.dices_are_equal(reverse(roll(6)), roll(6))  # type: ignore
    assert RV.dices_are_equal(1@roll(6), roll(6))
    assert RV.dices_are_equal(1@reverse(roll(6)), roll(6))  # type: ignore

def test2_reverse():
    @anydice_casting()
    def f(DIE:RV):
        return reverse(Seq(DIE))+1
    assert f(roll(6)) == 22

def test3_reverse():
    @anydice_casting()
    def f(DIE:RV):
        return 1@reverse(Seq(DIE))
    assert f(roll(6)) == 6
    assert f(roll(4, 6)) == 24

from dice_calc.funclib import maximum_of
def test_maximum_of():
    assert maximum_of(roll(6)) == 6, 'maximum_of [in docs]'
    assert maximum_of(roll(3, 6)) == 18, 'maximum_of [in docs]'
    assert maximum_of(roll(4, 6)) == 24
    assert maximum_of(roll(4, 6) + 1) == 25

from dice_calc.funclib import explode
def test_explode():
    assert RV.dices_are_equal(explode(roll(6), depth=1), RV.from_rvs((roll(range(6*0+1, 6*1)), roll(range(6*1+1, 6*2+1))), (5, 1))), 'explode depth 1 [in docs]'
    assert RV.dices_are_equal(explode(roll(6)), RV.from_rvs((roll(range(1, 6)), 6+roll(range(1, 6)), 6*2+roll(range(1, 6+1))), (30, 5, 1))), 'explode depth 2 [in docs]'
    a = RV(roll(2, 6).vals[:-1], roll(2, 6).probs[:-1])
    a = RV.from_rvs((a, 6*2+a, 6*4+roll(2, 6)), (6**4-6**2, 6**2-1, 1))
    assert RV.dices_are_equal(explode(roll(2, 6)), a), 'explode [in docs]'
    assert RV.dices_are_equal(roll(2, explode(roll(6))), explode(roll(6))+explode(roll(6))), 'explode [in docs]'
    a = RV.from_rvs((roll(range(1, 6)), 6+roll(range(1, 6)), 6*2+roll(range(1, 6+1))), (30, 5, 1))  # explode(roll(6))
    a = a+a  # rolling it twice
    assert RV.dices_are_equal(roll(2, explode(roll(6))), a), 'explode [in docs]'

# TODO complete these test
from dice_calc.funclib import highest_N_of_D
def test_highest_N_of_D():
    highest_N_of_D(3, roll(4, 6)), 'highest_N_of_D [in docs]'
    highest_N_of_D(roll(4), roll(4, 6)), 'highest_N_of_D [in docs]'  # type: ignore

# TODO complete these test
from dice_calc.funclib import lowest_N_of_D
def test_lowest_N_of_D():
    lowest_N_of_D(3, roll(4, 6)), 'lowest_N_of_D [in docs]'
    lowest_N_of_D(roll(4), roll(4, 6)), 'lowest_N_of_D [in docs]'  # type: ignore

# TODO complete these test
from dice_calc.funclib import middle_N_of_D
def test_middle_N_of_D():
    middle_N_of_D(1, roll(3, 6)), "middle_N_of_D [in docs] '2nd die'"
    middle_N_of_D(2, roll(3, 6)), "middle_N_of_D [in docs] '1st and 2nd die'"
    middle_N_of_D(1, roll(4, 6)), "middle_N_of_D [in docs] '2nd die'"
    middle_N_of_D(2, roll(4, 4)), "middle_N_of_D [in docs] '2nd and 3rd die'"
    middle_N_of_D(3, roll(4, 6)), "middle_N_of_D [in docs] '1st, 2nd and 3rd die'"

# TODO complete these test
from dice_calc.funclib import highest_of_N_and_N
def test_highest_of_N_and_N():
    highest_of_N_and_N(2, 3)
    highest_of_N_and_N(roll(6), 4)  # type: ignore
    highest_of_N_and_N(roll(4), roll(6))  # type: ignore

# TODO complete these test
from dice_calc.funclib import lowest_of_N_and_N
def test_lowest_of_N_and_N():
    lowest_of_N_and_N(2, 3)
    lowest_of_N_and_N(roll(6), 4)  # type: ignore
    lowest_of_N_and_N(roll(4), roll(6))  # type: ignore

from dice_calc.funclib import sort_VANILLA_SLOW, sort
def test_sort_vanilla():
    assert sort_VANILLA_SLOW(Seq(1, 2, 4, 6, 5, 3)) == Seq(6, 5, 4, 3, 2, 1), 'sort [in docs]'

def test_sort():
    assert sort(Seq(1, 2, 4, 6, 5, 3)) == Seq(6, 5, 4, 3, 2, 1), 'sort [in docs]'

def test_double_N_if_above_N():
    @anydice_casting()
    def double_N_if_above_N(A:int, B:int):
        if A > B: 
            return A + A
        return A
    assert RV.dices_are_equal(double_N_if_above_N(roll(6), 3), RV((1, 2, 3, 8, 10, 12), (1, 1, 1, 1, 1, 1))), "func [in doct] '(1, 2, 3, 8, 10, 12)'"  # type: ignore

def test_S_count_fives_and_above_and_subtract_ones():
    @anydice_casting()
    def S_count_fives_and_above_and_subtract_ones(ROLL:Seq):
        return (ROLL >= 5) - (ROLL == 1)
    assert RV.dices_are_equal(S_count_fives_and_above_and_subtract_ones(roll(3, 6)), RV(range(-3, 4), (1, 9, 33, 63, 66, 36, 8))), "func [in docs] '-3 .. 3'"  # type: ignore
