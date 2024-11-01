from .roller import roll


class __D_BASE:
  def __mul__(self, other):
    return roll(other)

  def __rmul__(self, other):
    return self.D_WITH_LEFT(left=other)

  class D_WITH_LEFT:
    def __init__(self, left):
      self.left = left

    def __mul__(self, other):
      return roll(self.left, other)


D = __D_BASE()
