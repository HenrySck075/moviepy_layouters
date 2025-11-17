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
    def setup_layout(self):
        return super().setup_layout()

    @override
    def calculate_final_size(self):
        if self._size:
            self.size = self._size
        else:
            super().calculate_final_size()

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
    child: LayouterClip
    "yuh"
    def __init__(self, child: LayouterClip, padding: EdgeInsets, duration=None, has_constant_size=True):
        super().__init__(child, duration, has_constant_size)
        self.padding = padding

    @override
    def setup_layout(self):
        LayouterClip.setup_layout(self)
        orig_constraint = self.size_constraints

        self.size_constraints = Constraints(
            max(0, self.size_constraints.min_width - (self.padding.left + self.padding.right)),
            max(0, self.size_constraints.min_height - (self.padding.top + self.padding.bottom)),
            max(0, self.size_constraints.max_width - (self.padding.left + self.padding.right)) if is_finite(self.size_constraints.max_width) else INF,
            max(0, self.size_constraints.max_height - (self.padding.top + self.padding.bottom)) if is_finite(self.size_constraints.max_width) else INF
        )

        self.child.setup_layout()
        self.size_constraints = orig_constraint
        #self.use_child_constraints()


    @override
    def calculate_final_size(self):
        super().calculate_final_size()
        self.size = (self.size[0]+self.padding.left+self.padding.right, self.size[1]+self.padding.top+self.padding.bottom)

    @override
    def frame_function(self, t: float):
        child_frame = super().frame_function(t)
        frame = np.zeros((self.size[1], self.size[0], 4), dtype=np.uint8)
        frame[self.padding.top:self.padding.top+child_frame.shape[0],
              self.padding.left:self.padding.left+child_frame.shape[1]] = child_frame
        return frame

@dataclass
class Offset:
    dx: float 
    dy: float 

class Offseted(SingleChildLayouterClip):
    child: LayouterClip
    def __init__(self, child: LayouterClip, offset: Offset, duration=None, has_constant_size=True):
        super().__init__(child, duration, has_constant_size)
        self.offset = offset

    @override
    def setup_layout(self):
        return self.use_child_constraints()
    
    @override
    def frame_function(self, t: float):
        frame = super().frame_function(t)
        offset_pixels = (
            int(self.size[0]*self.offset.dx),
            int(self.size[1]*self.offset.dy)
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
        
        frame[:, clear_range[0][0]:clear_range[0][1]] = empty
        frame[clear_range[1][0]:clear_range[1][1], :] = empty

        return frame





class VideoClipAdapter(LayouterClip):
    def __init__(self, clip: VideoClip):
        super().__init__(clip.duration, clip.has_constant_size)
        self.clip = clip

    def calculate_final_size(self):
        return self.clip.size

    def frame_function(self, t: float) -> np.ndarray:
        frame = self.clip.get_frame(t)

        if self.clip.mask is not None:
            mask = 255 * self.clip.mask.get_frame(t)
            if mask.dtype != "uint8":
                mask = mask.astype("uint8")
            frame = np.dstack([frame, mask])
        return frame
