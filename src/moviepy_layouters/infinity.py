
from typing import TypeGuard

class Infinity:
    """
    A non-float class representing a conceptual positive infinity.

    This object behaves as being greater than any other object (except itself),
    and when involved in basic arithmetic (addition, multiplication) with
    finite numbers, it remains infinity.
    """

    def __init__(self):
        # We use a trick to ensure only one instance of this object exists
        # by checking if a global instance already exists upon creation.
        # This makes it a singleton.
        if hasattr(Infinity, '__instance'):
            raise RuntimeError("Use the 'INF' constant instead of instantiating directly.")
        Infinity.__instance = self

    # --- Comparison Methods ---

    def __lt__(self, other):
        """Less than: Infinity is never less than anything."""
        return False

    def __le__(self, other):
        """Less than or equal: True only if the other is also infinity."""
        return self is other

    def __eq__(self, other):
        """Equal: True only if the other is the same infinity instance."""
        return self is other

    def __ne__(self, other):
        """Not equal: Inverse of __eq__."""
        return not (self is other)

    def __gt__(self, other):
        """Greater than: Infinity is greater than everything else."""
        # It is always greater than 'other' unless 'other' is also this instance
        return not (self is other)

    def __ge__(self, _):
        """Greater than or equal: Always true."""
        return True

    # --- Arithmetic Methods (Basic Infinity Arithmetic) ---

    def __add__(self, other):
        """Infinity + X = Infinity (unless X is negative infinity)"""
        # For simplicity, we assume we only deal with positive finite numbers
        return self

    def __radd__(self, other):
        """Handles X + Infinity."""
        return self

    def __sub__(self, other):
        """Infinity - X = Infinity"""
        return self

    def __rsub__(self, other):
        """X - Infinity = Negative Infinity (conceptually)"""
        # Since we are not defining a NegativeInfinity class, we will raise an
        # error to avoid mixing types, or return the standard float('-inf')
        # if the user wants an answer, but to stick to the rule of not using
        # float, we'll indicate it's not supported by this simple class.
        raise TypeError("Cannot subtract infinity from a finite number with this object.")

    def __mul__(self, other):
        """Infinity * X = Infinity (if X > 0) or -Infinity (if X < 0)"""
        if other == 0:
            raise ValueError("Infinity * 0 is undefined.")
        if other > 0:
            return self
        # Since we only defined Positive Infinity, we raise an error here
        raise TypeError("Multiplication by negative numbers not supported by this single-sided Infinity class.")

    def __rmul__(self, other):
        return self.__mul__(other)

    def __truediv__(self, other):
        """Infinity / X = Infinity (if X > 0)"""
        if other == 0:
            raise ZeroDivisionError("Cannot divide by zero.")
        if other == self:
            raise ValueError("Infinity / Infinity is undefined.")
        if other > 0:
            return self
        raise TypeError("Division by negative numbers not supported by this single-sided Infinity class.")

    def __abs__(self):
        """The absolute value of positive infinity is itself."""
        return self

    # --- Representation ---

    def __repr__(self):
        return "INF"

    def __str__(self):
        return "∞"

    # --- Hashing for use in sets/dictionary keys ---
    def __hash__(self):
        return hash("Infinity_Object")

# Create a single, globally accessible instance
INF = Infinity()



def is_inf(v) -> TypeGuard[Infinity]:
    return v is INF

def is_finite[T](v: T | Infinity) -> TypeGuard[T]:
    return v is not INF
