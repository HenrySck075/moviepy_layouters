from dataclasses import dataclass
from typing import Optional, final, override
from moviepy import VideoClip
from moviepy_layouters.infinity import INF, Infinity
import numpy as np


ENABLE_DEBUGGING = True

@dataclass
class Constraints:
    min_width: int = 0
    min_height: int = 0
    max_width: int | Infinity = INF
    max_height: int | Infinity = INF


    def __repr__(self) -> str:
        return f"[{self.min_width}x{self.max_height}|{self.max_width}x{self.max_height}]"

# Mostly base identifiers or smth
class LayouterClip():
    size: tuple[int,int]
    "Base class for everything MoviePy Layouters"
    def __init__(self, duration: Optional[float]=None, has_constant_size=True):
        self.duration = duration
        self.size_constraints: Constraints
        self.parent: Optional[LayouterClip] = None

        # simple memoizing of the most recent call of frame_function
        self.memoized_t: float|None = None
        self.memoized_frame: np.ndarray|None = None

        if type(self) != LayouterClip and type(self).frame_function is LayouterClip.frame_function:
            print("[WARN] let me warn ya pls override frame_function if you directly uses LayouterClip because it returns empty image all the time")
            print("[WARN] but if you override it after init then pls ignore this")

        if not ENABLE_DEBUGGING: delattr(self, "debug_clip_info")

    def debug_clip_info(self, indent=0):
        print(" "*(indent*2)+f"{type(self).__name__}: {self.debug_clip_meta()}")
    def debug_clip_meta(self):
        return f"Size: {self.size}"

    @staticmethod
    def merge_constraints(one: Constraints, two: Constraints):
        mw = max(one.min_width, two.min_width)
        mh = max(one.min_height, two.min_height)
        return Constraints(
            mw, mh,
            max(mw, min(one.max_width, two.max_width)),
            max(mh, min(one.max_height, two.max_height))
        )

    def calculate_size(self, constraints: Constraints):
        """
        Subclasses should override this method to give the clip a final size for rendering.
        The default behavior is to set the size to the minimum constraint.

        This function is called after `setup_layout` on render so all necessary members are guaranteed to be initialized
        """
        
        self.size = (constraints.min_width, constraints.min_height)
        return self.size

    def frame_function(self, t: float) -> np.ndarray:
        "Returns a WxHx4 numpy array at a given t"
        return np.zeros((self.size[1], self.size[0], 4), dtype=np.uint8)
    
    @final
    def get_frame(self, t: float):
        """
        frame_function with several safeguards

        subclasses wanting to call get_frame inside frame_function from itself should instead call frame_function
        """
        if self.memoized_t == t and self.memoized_frame is not None:
            return self.memoized_frame
        self.memoized_t = t
        if (t < 0 or (self.duration and self.duration < t)):
            # Returns empty image if out of bounds
            return LayouterClip.frame_function(self, 0)
        self.memoized_frame = self.frame_function(t)
        return self.memoized_frame


class SingleChildLayouterClip(LayouterClip):
    def __init__(self, child: Optional[LayouterClip] = None, duration=None, has_constant_size=True):
        super().__init__(duration, has_constant_size)
        self._child = None
        self.child = child

    @property
    def child(self):
        return self._child
    @child.setter
    def child(self, c: LayouterClip|None):
        self._child = c
        if c: c.parent = self

    @override
    def debug_clip_info(self, indent=0):
        super().debug_clip_info(indent)
        if self.child: self.child.debug_clip_info(indent+1)

    @override
    def calculate_size(self, constraints: Constraints):
        if self.child:
            self.child.calculate_size(constraints) 
            self.size = self.child.size
            return self.size
        else:
            return super().calculate_size(constraints)

    @override
    def frame_function(self, t: float):
        return self.child.get_frame(t) if self.child else super().frame_function(t)

class MultiChildLayouterClip(LayouterClip):
    def __init__(self, children: list[LayouterClip] = [], duration=None, has_constant_size=True):
        super().__init__(duration, has_constant_size)
        self.children = children
        for c in children:
            c.parent = self

    @override
    def debug_clip_info(self, indent=0):
        super().debug_clip_info(indent)
        for child in self.children: 
            child.debug_clip_info(indent+1)

class ProxyLayouterClip(SingleChildLayouterClip):
    child: LayouterClip # type: ignore
    def __init__(self, child: LayouterClip, duration=None, has_constant_size=True):
        super().__init__(child, duration, has_constant_size)

    @override
    def calculate_size(self, constraints: Constraints):
        self.size = self.child.calculate_size(constraints)
        return self.size

    @override
    def frame_function(self, t: float):
        return self.child.frame_function(t)
    
