
from typing import TYPE_CHECKING, override


if TYPE_CHECKING:
    from _typeshed import SupportsAllComparisons
import numpy as np

def clamp[T: SupportsAllComparisons](v: T, begin: T, end: T):
    assert(end >= begin)
    if (v < begin): v = begin
    if (v > end): v = end
    return v

class Curve():
    def __call__(self, t: float) -> float:
        return self.transform(clamp(t,0,1))
    def transform(self, t:float) -> float:
        raise NotImplementedError


class Linear(Curve):
    def transform(self, t: float) -> float:
        return t

class Interval(Curve):
    """
    A curve that is 0.0 until [begin], then curved (according to [curve]) from
    0.0 at [begin] to 1.0 at [end], then remains 1.0 past [end].
   
    An [Interval] can be used to delay an animation. For example, a six second
    animation that uses an [Interval] with its [begin] set to 0.5 and its [end]
    set to 1.0 will essentially become a three-second animation that starts
    three seconds later.
   
    """
    def __init__(self, begin: float, end: float, curve: Curve):
        self.begin = begin
        self.end = end
        self.curve = curve

    def transform(self, t: float) -> float:
        return self.curve.transform(clamp((t-self.begin)/(self.end-self.begin), 0,1))


class Cubic(Curve):
    def __init__(self, x1,y1, x2,y2) -> None:
        self.x1, self.y1, self.x2, self.y2 = x1, y1, x2, y2

    def _eval_cubic(self, a: float, b: float, m: float):
        return 3 * a * (1 - m) * (1 - m) * m + 3 * b * (1 - m) * m * m + m * m * m

    @override
    def transform(self, t: float) -> float:
        start = 0.0
        end = 1.0
        while True:
            midpoint = (start + end) / 2
            estimate = self._eval_cubic(self.x1, self.x2, midpoint);
            if ((t - estimate).__abs__() < 0.001):
                return clamp(self._eval_cubic(self.y1, self.y2, midpoint),0,1)
            if (estimate < t):
                start = midpoint
            else:
                end = midpoint
        



# PREDEFINED CURVES
class Curves:
  ease = Cubic(0.25, 0.1, 0.25, 1.0);
  "A cubic animation curve that speeds up quickly and ends slowly."

  easeIn = Cubic(0.42, 0.0, 1.0, 1.0);
  "A cubic animation curve that starts slowly and ends quickly."

  easeInToLinear = Cubic(0.67, 0.03, 0.65, 0.09);
  """ 
  A cubic animation curve that starts slowly and ends linearly.
  
  The symmetric animation to [linearToEaseOut].
  """

  easeInSine = Cubic(0.47, 0.0, 0.745, 0.715);
  """
  A cubic animation curve that starts slowly and ends quickly. This is
  similar to [Curves.easeIn], but with sinusoidal easing for a slightly less
  abrupt beginning and end. Nonetheless, the result is quite gentle and is
  hard to distinguish from [Curves.linear] at a glance.
  
  Derived from Robert Penner’s easing functions.
  """

  easeInQuad = Cubic(0.55, 0.085, 0.68, 0.53);
  """
  A cubic animation curve that starts slowly and ends quickly. Based on a
  quadratic equation where `f(t) = t²`, this is effectively the inverse of
  [Curves.decelerate].
  
  Compared to [Curves.easeInSine], this curve is slightly steeper.
  
  Derived from Robert Penner’s easing functions.
  """

  easeInCubic = Cubic(0.55, 0.055, 0.675, 0.19);
  """
  A cubic animation curve that starts slowly and ends quickly. This curve is
  based on a cubic equation where `f(t) = t³`. The result is a safe sweet
  spot when choosing a curve for widgets animating off the viewport.
  
  Compared to [Curves.easeInQuad], this curve is slightly steeper.
  
  Derived from Robert Penner’s easing functions.
  """

  easeInQuart = Cubic(0.895, 0.03, 0.685, 0.22);
  """
  A cubic animation curve that starts slowly and ends quickly. This curve is"
  based on a quartic equation where `f(t) = t⁴`."
  ""
  Animations using this curve or steeper curves will benefit from a longer"
  duration to avoid motion feeling unnatural."
  ""
  Compared to [Curves.easeInCubic], this curve is slightly steeper."
  ""
  Derived from Robert Penner’s easing functions."
  """

  easeInQuint = Cubic(0.755, 0.05, 0.855, 0.06);
  """A cubic animation curve that starts slowly and ends quickly. This curve is
  based on a quintic equation where `f(t) = t⁵`.
  
  Compared to [Curves.easeInQuart], this curve is slightly steeper.
  
  Derived from Robert Penner’s easing functions.
  """

  easeInExpo = Cubic(0.95, 0.05, 0.795, 0.035);
  """
  A cubic animation curve that starts slowly and ends quickly. This curve is
  based on an exponential equation where `f(t) = 2¹⁰⁽ᵗ⁻¹⁾`.
  
  Using this curve can give your animations extra flare, but a longer
  duration may need to be used to compensate for the steepness of the curve
  
  Compared to [Curves.easeInQuint], this curve is slightly steeper.
  
  Derived from Robert Penner’s easing functions.
  """

  " A cubic animation curve that starts slowly and ends quickly. This curve is"
  " effectively the bottom-right quarter of a circle."
  ""
  " Like [Curves.easeInExpo], this curve is fairly dramatic and will reduce"
  " the clarity of an animation if not given a longer duration."
  ""
  " Derived from Robert Penner’s easing functions."
  ""
  " {@animation 464 192 https://flutter.github.io/assets-for-api-docs/assets/animation/curve_ease_in_circ.mp4}"
  easeInCirc = Cubic(0.6, 0.04, 0.98, 0.335);

  " A cubic animation curve that starts slowly and ends quickly. This curve"
  " is similar to [Curves.elasticIn] in that it overshoots its bounds before"
  " reaching its end. Instead of repeated swinging motions before ascending,"
  " though, this curve overshoots once, then continues to ascend."
  ""
  " Derived from Robert Penner’s easing functions."
  ""
  " {@animation 464 192 https://flutter.github.io/assets-for-api-docs/assets/animation/curve_ease_in_back.mp4}"
  easeInBack = Cubic(0.6, -0.28, 0.735, 0.045);

  " A cubic animation curve that starts quickly and ends slowly."
  ""
  " This is the same as the CSS easing function `ease-out`."
  ""
  " {@animation 464 192 https://flutter.github.io/assets-for-api-docs/assets/animation/curve_ease_out.mp4}"
  easeOut = Cubic(0.0, 0.0, 0.58, 1.0);

  " A cubic animation curve that starts linearly and ends slowly."
  ""
  " A symmetric animation to [easeInToLinear]."
  ""
  " {@animation 464 192 https://flutter.github.io/assets-for-api-docs/assets/animation/curve_linear_to_ease_out.mp4}"
  linearToEaseOut = Cubic(0.35, 0.91, 0.33, 0.97);

  " A cubic animation curve that starts quickly and ends slowly. This is"
  " similar to [Curves.easeOut], but with sinusoidal easing for a slightly"
  " less abrupt beginning and end. Nonetheless, the result is quite gentle and"
  " is hard to distinguish from [Curves.linear] at a glance."
  ""
  " Derived from Robert Penner’s easing functions."
  ""
  " {@animation 464 192 https://flutter.github.io/assets-for-api-docs/assets/animation/curve_ease_out_sine.mp4}"
  easeOutSine = Cubic(0.39, 0.575, 0.565, 1.0);

  " A cubic animation curve that starts quickly and ends slowly. This is"
  " effectively the same as [Curves.decelerate], only simulated using a cubic"
  " bezier function."
  ""
  " Compared to [Curves.easeOutSine], this curve is slightly steeper."
  ""
  " Derived from Robert Penner’s easing functions."
  ""
  " {@animation 464 192 https://flutter.github.io/assets-for-api-docs/assets/animation/curve_ease_out_quad.mp4}"
  easeOutQuad = Cubic(0.25, 0.46, 0.45, 0.94);

  " A cubic animation curve that starts quickly and ends slowly. This curve is"
  " a flipped version of [Curves.easeInCubic]."
  ""
  " The result is a safe sweet spot when choosing a curve for animating a"
  " widget's position entering or already inside the viewport."
  ""
  " Compared to [Curves.easeOutQuad], this curve is slightly steeper."
  ""
  " Derived from Robert Penner’s easing functions."
  ""
  " {@animation 464 192 https://flutter.github.io/assets-for-api-docs/assets/animation/curve_ease_out_cubic.mp4}"
  easeOutCubic = Cubic(0.215, 0.61, 0.355, 1.0);

  " A cubic animation curve that starts quickly and ends slowly. This curve is"
  " a flipped version of [Curves.easeInQuart]."
  ""
  " Animations using this curve or steeper curves will benefit from a longer"
  " duration to avoid motion feeling unnatural."
  ""
  " Compared to [Curves.easeOutCubic], this curve is slightly steeper."
  ""
  " Derived from Robert Penner’s easing functions."
  ""
  " {@animation 464 192 https://flutter.github.io/assets-for-api-docs/assets/animation/curve_ease_out_quart.mp4}"
  easeOutQuart = Cubic(0.165, 0.84, 0.44, 1.0);

  " A cubic animation curve that starts quickly and ends slowly. This curve is"
  " a flipped version of [Curves.easeInQuint]."
  ""
  " Compared to [Curves.easeOutQuart], this curve is slightly steeper."
  ""
  " Derived from Robert Penner’s easing functions."
  ""
  " {@animation 464 192 https://flutter.github.io/assets-for-api-docs/assets/animation/curve_ease_out_quint.mp4}"
  easeOutQuint = Cubic(0.23, 1.0, 0.32, 1.0);

  " A cubic animation curve that starts quickly and ends slowly. This curve is"
  " a flipped version of [Curves.easeInExpo]. Using this curve can give your"
  " animations extra flare, but a longer duration may need to be used to"
  " compensate for the steepness of the curve."
  ""
  " Derived from Robert Penner’s easing functions."
  ""
  " {@animation 464 192 https://flutter.github.io/assets-for-api-docs/assets/animation/curve_ease_out_expo.mp4}"
  easeOutExpo = Cubic(0.19, 1.0, 0.22, 1.0);

  " A cubic animation curve that starts quickly and ends slowly. This curve is"
  " effectively the top-left quarter of a circle."
  ""
  " Like [Curves.easeOutExpo], this curve is fairly dramatic and will reduce"
  " the clarity of an animation if not given a longer duration."
  ""
  " Derived from Robert Penner’s easing functions."
  ""
  " {@animation 464 192 https://flutter.github.io/assets-for-api-docs/assets/animation/curve_ease_out_circ.mp4}"
  easeOutCirc = Cubic(0.075, 0.82, 0.165, 1.0);

  " A cubic animation curve that starts quickly and ends slowly. This curve is"
  " similar to [Curves.elasticOut] in that it overshoots its bounds before"
  " reaching its end. Instead of repeated swinging motions after ascending,"
  " though, this curve only overshoots once."
  ""
  " Derived from Robert Penner’s easing functions."
  ""
  " {@animation 464 192 https://flutter.github.io/assets-for-api-docs/assets/animation/curve_ease_out_back.mp4}"
  easeOutBack = Cubic(0.175, 0.885, 0.32, 1.275);

  " A cubic animation curve that starts slowly, speeds up, and then ends"
  " slowly."
  ""
  " This is the same as the CSS easing function `ease-in-out`."
  ""
  " {@animation 464 192 https://flutter.github.io/assets-for-api-docs/assets/animation/curve_ease_in_out.mp4}"
  easeInOut = Cubic(0.42, 0.0, 0.58, 1.0);

  " A cubic animation curve that starts slowly, speeds up, and then ends"
  " slowly. This is similar to [Curves.easeInOut], but with sinusoidal easing"
  " for a slightly less abrupt beginning and end."
  ""
  " Derived from Robert Penner’s easing functions."
  ""
  " {@animation 464 192 https://flutter.github.io/assets-for-api-docs/assets/animation/curve_ease_in_out_sine.mp4}"
  easeInOutSine = Cubic(0.445, 0.05, 0.55, 0.95);

  " A cubic animation curve that starts slowly, speeds up, and then ends"
  " slowly. This curve can be imagined as [Curves.easeInQuad] as the first"
  " half, and [Curves.easeOutQuad] as the second."
  ""
  " Compared to [Curves.easeInOutSine], this curve is slightly steeper."
  ""
  " Derived from Robert Penner’s easing functions."
  ""
  " {@animation 464 192 https://flutter.github.io/assets-for-api-docs/assets/animation/curve_ease_in_out_quad.mp4}"
  easeInOutQuad = Cubic(0.455, 0.03, 0.515, 0.955);

  " A cubic animation curve that starts slowly, speeds up, and then ends"
  " slowly. This curve can be imagined as [Curves.easeInCubic] as the first"
  " half, and [Curves.easeOutCubic] as the second."
  ""
  " The result is a safe sweet spot when choosing a curve for a widget whose"
  " initial and final positions are both within the viewport."
  ""
  " Compared to [Curves.easeInOutQuad], this curve is slightly steeper."
  ""
  " Derived from Robert Penner’s easing functions."
  ""
  " {@animation 464 192 https://flutter.github.io/assets-for-api-docs/assets/animation/curve_ease_in_out_cubic.mp4}"
  easeInOutCubic = Cubic(0.645, 0.045, 0.355, 1.0);

  " A cubic animation curve that starts slowly, speeds up shortly thereafter,"
  " and then ends slowly. This curve can be imagined as a steeper version of"
  " [easeInOutCubic]."
  ""
  " The result is a more emphasized eased curve when choosing a curve for a"
  " widget whose initial and final positions are both within the viewport."
  ""
  " Compared to [Curves.easeInOutCubic], this curve is slightly steeper."
  ""
  " {@animation 464 192 https://flutter.github.io/assets-for-api-docs/assets/animation/curve_ease_in_out_cubic_emphasized.mp4}"
  """
  easeInOutCubicEmphasized = ThreePointCubic(
    Offset(0.05, 0),
    Offset(0.133333, 0.06),
    Offset(0.166666, 0.4),
    Offset(0.208333, 0.82),
    Offset(0.25, 1),
  );
  """

  " A cubic animation curve that starts slowly, speeds up, and then ends"
  " slowly. This curve can be imagined as [Curves.easeInQuart] as the first"
  " half, and [Curves.easeOutQuart] as the second."
  ""
  " Animations using this curve or steeper curves will benefit from a longer"
  " duration to avoid motion feeling unnatural."
  ""
  " Compared to [Curves.easeInOutCubic], this curve is slightly steeper."
  ""
  " Derived from Robert Penner’s easing functions."
  ""
  " {@animation 464 192 https://flutter.github.io/assets-for-api-docs/assets/animation/curve_ease_in_out_quart.mp4}"
  easeInOutQuart = Cubic(0.77, 0.0, 0.175, 1.0);

  " A cubic animation curve that starts slowly, speeds up, and then ends"
  " slowly. This curve can be imagined as [Curves.easeInQuint] as the first"
  " half, and [Curves.easeOutQuint] as the second."
  ""
  " Compared to [Curves.easeInOutQuart], this curve is slightly steeper."
  ""
  " Derived from Robert Penner’s easing functions."
  ""
  " {@animation 464 192 https://flutter.github.io/assets-for-api-docs/assets/animation/curve_ease_in_out_quint.mp4}"
  easeInOutQuint = Cubic(0.86, 0.0, 0.07, 1.0);

  " A cubic animation curve that starts slowly, speeds up, and then ends"
  " slowly."
  ""
  " Since this curve is arrived at with an exponential function, the midpoint"
  " is exceptionally steep. Extra consideration should be taken when designing"
  " an animation using this."
  ""
  " Compared to [Curves.easeInOutQuint], this curve is slightly steeper."
  ""
  " Derived from Robert Penner’s easing functions."
  ""
  " {@animation 464 192 https://flutter.github.io/assets-for-api-docs/assets/animation/curve_ease_in_out_expo.mp4}"
  easeInOutExpo = Cubic(1.0, 0.0, 0.0, 1.0);

  " A cubic animation curve that starts slowly, speeds up, and then ends"
  " slowly. This curve can be imagined as [Curves.easeInCirc] as the first"
  " half, and [Curves.easeOutCirc] as the second."
  ""
  " Like [Curves.easeInOutExpo], this curve is fairly dramatic and will reduce"
  " the clarity of an animation if not given a longer duration."
  ""
  " Compared to [Curves.easeInOutExpo], this curve is slightly steeper."
  ""
  " Derived from Robert Penner’s easing functions."
  ""
  " {@animation 464 192 https://flutter.github.io/assets-for-api-docs/assets/animation/curve_ease_in_out_circ.mp4}"
  easeInOutCirc = Cubic(0.785, 0.135, 0.15, 0.86);

  " A cubic animation curve that starts slowly, speeds up, and then ends"
  " slowly. This curve can be imagined as [Curves.easeInBack] as the first"
  " half, and [Curves.easeOutBack] as the second."
  ""
  " Since two curves are used as a basis for this curve, the resulting"
  " animation will overshoot its bounds twice before reaching its end - first"
  " by exceeding its lower bound, then exceeding its upper bound and finally"
  " descending to its final position."
  ""
  " Derived from Robert Penner’s easing functions."
  ""
  " {@animation 464 192 https://flutter.github.io/assets-for-api-docs/assets/animation/curve_ease_in_out_back.mp4}"
  easeInOutBack = Cubic(0.68, -0.55, 0.265, 1.55);

  " A curve that starts quickly and eases into its final position."
  ""
  " Over the course of the animation, the object spends more time near its"
  " final destination. As a result, the user isn’t left waiting for the"
  " animation to finish, and the negative effects of motion are minimized."
  ""
  " {@animation 464 192 https://flutter.github.io/assets-for-api-docs/assets/animation/curve_fast_out_slow_in.mp4}"
  ""
  " See also:"
  ""
  "  * [Easing.legacy], the name for this curve in the Material specification."
  fastOutSlowIn = Cubic(0.4, 0.0, 0.2, 1.0);

  " A cubic animation curve that starts quickly, slows down, and then ends"
  " quickly."
  ""
  " {@animation 464 192 https://flutter.github.io/assets-for-api-docs/assets/animation/curve_slow_middle.mp4}"
  slowMiddle = Cubic(0.15, 0.85, 0.85, 0.15);
