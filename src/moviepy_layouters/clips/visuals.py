from dataclasses import dataclass
from typing import Optional, override

from moviepy.video.VideoClip import VideoClip
from moviepy_layouters.clips.base import Constraints, LayouterClip, SingleChildLayouterClip
from moviepy_layouters.infinity import INF, is_finite
import numpy as np

# ==== Layouts ====
class Box(SingleChildLayouterClip):
    "A box"
    def __init__(self, size: Optional[tuple[int, int]] = None, child: Optional[LayouterClip] = None, duration=None, has_constant_size=True):
        super().__init__(child, duration, has_constant_size)
        self._size = size

    @override
    def calculate_size(self, constraints: Constraints):
        if self._size:
            constraints = self.merge_constraints(
                constraints, Constraints(*self._size, *self._size)
            )
            self.size = (constraints.min_width, constraints.min_height)
            return self.size
        else:
            return super().calculate_size(constraints)

class ColoredBox(Box):
    "A colored box"
    def __init__(self, color: tuple[int,int,int,int], size: Optional[tuple[int,int]] = None, child: Optional[LayouterClip] = None, duration=None, has_constant_size=True):
        super().__init__(size, child, duration, has_constant_size)
        self.color = color

    @override
    def frame_function(self, t: float):
        return np.full((self.size[1],self.size[0],4), self.color) 


@dataclass
class EdgeInsets:
    top: int
    left: int
    bottom: int
    right: int

    @staticmethod
    def all(inset: int):
        return EdgeInsets(inset,inset,inset,inset)

class Padding(SingleChildLayouterClip):
    child: LayouterClip # type: ignore
    "yuh"
    def __init__(self, child: LayouterClip, padding: EdgeInsets, duration=None, has_constant_size=True):
        super().__init__(child, duration, has_constant_size)
        self.padding = padding

    @override
    def calculate_size(self, constraints: Constraints):
        child_constraints = Constraints(
            max(0, constraints.min_width - (self.padding.left + self.padding.right)),
            max(0, constraints.min_height - (self.padding.top + self.padding.bottom)),
            max(0, constraints.max_width - (self.padding.left + self.padding.right)) if is_finite(constraints.max_width) else INF,
            max(0, constraints.max_height - (self.padding.top + self.padding.bottom)) if is_finite(constraints.max_height) else INF
        )

        self.child.calculate_size(child_constraints)
        return LayouterClip.calculate_size(self,constraints)

    @override
    def frame_function(self, t: float):
        child_frame = self.child.frame_function(t)
        frame = np.zeros((self.size[1], self.size[0], 4), dtype=np.uint8)
        frame[self.padding.top:self.padding.top+child_frame.shape[0],
              self.padding.left:self.padding.left+child_frame.shape[1]] = child_frame
        return frame

@dataclass
class Offset:
    dx: float 
    dy: float 

class Offseted(SingleChildLayouterClip):
    child: LayouterClip # type: ignore
    def __init__(self, child: LayouterClip, offset: Offset, duration=None, has_constant_size=True):
        super().__init__(child, duration, has_constant_size)
        self.offset = offset

    @override
    def calculate_size(self, constraints: Constraints):
        self.size = self.child.calculate_size(constraints)
        return self.size
    
    @override
    def frame_function(self, t: float):
        frame = super().frame_function(t)
        offset_pixels = (
            (self.size[0]*self.offset.dx).__floor__(),
            (self.size[1]*self.offset.dy).__floor__()
        )

        frame = np.roll(frame, offset_pixels, (1,0))

        empty = [0,0,0,0]

        clear_range = (
            (0,offset_pixels[0]),
            (0,offset_pixels[1])
        )

        if (offset_pixels[0] < 0):
            clear_range = (
                (self.size[0]+offset_pixels[0],self.size[0]),
                clear_range[1]
            )
        if (offset_pixels[1] < 0):
            clear_range = (
                clear_range[0],
                (self.size[1]+offset_pixels[1],self.size[1])
            )
        
        if clear_range[0][1] - clear_range[0][0] != 0:
            frame[:, clear_range[0][0]:clear_range[0][1]] = empty
        
        if clear_range[1][1] - clear_range[1][0] != 0:
            frame[clear_range[1][0]:clear_range[1][1], :] = empty

        return frame





class VideoClipAdapter(LayouterClip):
    def __init__(self, clip: VideoClip):
        super().__init__(clip.duration, clip.has_constant_size)
        self.clip = clip

    def calculate_size(self, _): # type: ignore
        self.size = self.clip.size
        return self.size

    def frame_function(self, t: float) -> np.ndarray:
        frame = self.clip.get_frame(t)

        if self.clip.mask is not None:
            mask = 255 * self.clip.mask.get_frame(t)
            if mask.dtype != "uint8":
                mask = mask.astype("uint8")
            frame = np.dstack([frame, mask])
        else:
            frame = np.dstack([frame, np.full((self.size[1], self.size[0]),255)])
        return frame
