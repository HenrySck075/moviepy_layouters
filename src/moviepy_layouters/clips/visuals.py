from dataclasses import dataclass
from enum import Enum
from typing import Optional, override

from moviepy.video.VideoClip import VideoClip
from moviepy_layouters.clips.base import Constraints, LayouterClip, ProxyLayouterClip, SingleChildLayouterClip
from moviepy_layouters.infinity import INF, is_finite
from moviepy_layouters.utils import paste_image_array
import numpy as np

type BoxSize = Optional[tuple[int|None, int|None]]
# ==== Layouts ====
class Box(SingleChildLayouterClip):
    "A box"
    def __init__(self, *, size: BoxSize = None, use_max=False, child: Optional[LayouterClip] = None, duration=None):
        super().__init__(child=child, duration=duration)
        self._size = size
        self._use_max_constraints = use_max

    @override
    def calculate_size(self, constraints: Constraints):
        if self._size:
            c = Constraints(
                self._size[0] if self._size[0] else constraints.min_width,
                self._size[1] if self._size[1] else constraints.min_height,
                self._size[0] if self._size[0] else constraints.max_width,
                self._size[1] if self._size[1] else constraints.max_height,
            )
            constraints = self.merge_constraints(
                constraints, c 
            )
            if self.child: 
                self.size = self.child.calculate_size(constraints)
                return self.size
            self.size = (
                constraints.max_width if self._use_max_constraints and is_finite(constraints.max_width) else constraints.min_width, 
                constraints.max_height if self._use_max_constraints and is_finite(constraints.max_height) else constraints.min_height # type: ignore
            ) #type: ignore
            return self.size
        else:
            return super().calculate_size(constraints)

class ColoredBox(Box):
    "A colored box"
    def __init__(self, *, color: tuple[int,int,int,int], size: BoxSize = None, use_max=False, child: Optional[LayouterClip] = None, duration=None):
        super().__init__(size=size, use_max=use_max, child=child, duration=duration)
        self.color = color

    @override
    def frame_function(self, t: float):
        f = np.full((self.size[1],self.size[0],4), self.color) 
        if self.child:
            paste_image_array(f, self.child.get_frame(t), (0,0))
        return f

class ConstrainedBox(Box):
    "Impose additional constraints to the clips"
    def __init__(self, *, constraints: Constraints, use_max=False, child: Optional[LayouterClip] = None, duration=None):
        super().__init__(size=None, use_max=use_max, child=child, duration=duration)
        self.constraints = constraints

    def calculate_size(self, constraints: Constraints):
        return super().calculate_size(self.merge_constraints(constraints, self.constraints))

class ClippedBox(Box):
    child: LayouterClip # type: ignore
    # Override __init__ to require a child
    def __init__(self, *, child: LayouterClip, size: BoxSize = None, use_max=False, duration: Optional[float] = None):
            
        # Temporarily call base init without child to avoid setting it before the custom setter is active
        super().__init__(size=size, use_max=use_max, child=child, duration=duration) 

    @override
    def calculate_size(self, constraints: Constraints):
        """
        The ClippedBox size is set by the input constraints.
        The child is calculated with maximum possible constraints (INF) to determine its desired size.
        """
        # 1. ClippedBox size is determined by the constraints passed to it.
        # Following LayouterClip.calculate_size default, we use min constraints as size 
        # (This is typical if the clip wants to fit inside the parent's area)
        self.size = (constraints.min_width, constraints.min_height)
        
        # 2. Pass max constraints to the child so it can decide its 'natural' size.
        # Assuming Constraints has INF defined for max_width/height
        max_constraints = Constraints()
        
        # The child's calculated size will be stored in self.child.size
        # The return value is the ClippedBox's size
        self.child.calculate_size(max_constraints) 
        return self.size

    @override
    def frame_function(self, t: float) -> np.ndarray:
        """
        Gets the child's frame and clips it to the ClippedBox's size (self.size).
        Position is always top-left.
        """
        # Get the child's frame, which could be larger than self.size
        child_frame: np.ndarray = self.child.get_frame(t)
        
        # The size of the ClippedBox
        clip_width, clip_height = self.size
        
        # Clip the child frame: [height_slice, width_slice, color_channel_slice]
        # Since position is always top-left, the slice starts at 0 for both height and width.
        # The resulting frame will have the dimensions (clip_height, clip_width, 4)
        
        clipped_frame = child_frame[:clip_height, :clip_width, :]
        
        # Check if the clipped_frame is smaller than the required clip_size (due to child being smaller)
        # If the child frame is smaller, it needs to be padded with transparent pixels (zeros).
        if clipped_frame.shape[0] < clip_height or clipped_frame.shape[1] < clip_width:
            
            # Create a blank transparent image of the correct final size
            final_frame = np.zeros((clip_height, clip_width, 4), dtype=np.uint8)
            
            # Place the clipped frame (which might be smaller) into the top-left of the final frame
            h, w, _ = clipped_frame.shape
            final_frame[:h, :w, :] = clipped_frame
            return final_frame
            
        return clipped_frame



@dataclass
class EdgeInsets:
    top: int
    left: int
    bottom: int
    right: int

    @staticmethod
    def all(inset: int):
        return EdgeInsets(inset,inset,inset,inset)

    @staticmethod
    def symmetric(vertical: int = 0, horizontal: int = 0):
        return EdgeInsets(vertical, horizontal, vertical, horizontal)

class Padding(SingleChildLayouterClip):
    child: LayouterClip # type: ignore
    "yuh"
    def __init__(self, *, child: LayouterClip, padding: EdgeInsets, duration=None):
        super().__init__(child=child, duration=duration)
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
        self.size = (
            self.child.size[0]+self.padding.left+self.padding.right,
            self.child.size[1]+self.padding.top+self.padding.bottom
        )
        return self.size 

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

def rigged_round(v: float):
    return v.__floor__() if v < 0 else v.__ceil__()

class Offseted(SingleChildLayouterClip):
    child: LayouterClip # type: ignore
    def __init__(self, *, child: LayouterClip, offset: Offset, duration=None):
        super().__init__(child=child, duration=duration)
        self.offset = offset

    @override
    def calculate_size(self, constraints: Constraints):
        self.size = self.child.calculate_size(constraints)
        return self.size
    
    @override
    def frame_function(self, t: float):
        if (abs(self.offset.dx)>=1 or abs(self.offset.dy)>=1):
            return LayouterClip.frame_function(self, t)
        frame = super().frame_function(t)
        if (self.offset.dx==0 and self.offset.dy==0):
            return frame
        offset_pixels = (
            rigged_round(self.size[0]*self.offset.dx),
            rigged_round(self.size[1]*self.offset.dy)
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




class Alignment(Enum):
    TopLeft = 0
    Top = 1
    TopRight = 2

    Left = 3
    Center = 4
    Right = 5

    BottomLeft = 6
    Bottom = 7
    BottomRight = 8

class Aligned(SingleChildLayouterClip):
    """
    Positions a (possibly smaller sized) child's frame according to an Alignment enum.
    The size of the Aligned clip itself is determined by constraints imposed during layout.
    """
    def __init__(self, *, child: Optional[LayouterClip] = None, alignment: Alignment = Alignment.Center, duration=None):
        super().__init__(child=child, duration=duration)
        self.alignment = alignment

    # Note: calculate_size is inherited from SingleChildLayouterClip which, by default,
    # sets the size equal to the child's size, or to the minimum constraints if no child.
    # For alignment, typically the Aligned clip takes the available space (from parent constraints),
    # but for simplicity, we keep the base behavior unless overridden here.
    # If it *should* take the parent's size, it would be:
    @override
    def calculate_size(self, constraints: Constraints):
        if self.child:
            self.child.calculate_size(Constraints(0,0,constraints.max_width,constraints.max_height)) # Child takes constraints
        is_finite_w = is_finite(constraints.max_width)
        is_finite_h = is_finite(constraints.max_height)
        self.size = ( # type: ignore
            constraints.max_width if is_finite_w else self.child.size[0] if self.child else constraints.min_width, 
            constraints.max_height if is_finite_h else self.child.size[1] if self.child else constraints.min_height
        ) # Aligned takes the max available space
        return self.size
    # --- For this implementation, we rely on the parent or user setting the size via constraints ---

    @override
    def frame_function(self, t: float) -> np.ndarray:
        # Get the dimensions of the Aligned clip (self) and the child clip
        aligned_w, aligned_h = self.size
        child_frame = self.child.get_frame(t) if self.child else super().frame_function(t)
        child_h, child_w, child_depth = child_frame.shape

        # Create a blank canvas (our frame) with the Aligned clip's size
        # Assuming the base LayouterClip.frame_function returns a transparent image (WxHx4)
        frame = LayouterClip.frame_function(self,t)

        # Calculate the top-left (x, y) coordinates for positioning the child
        x, y = self._get_position(aligned_w, aligned_h, child_w, child_h)

        # Ensure the coordinates are non-negative integers
        x, y = int(max(0, x)), int(max(0, y))

        # Determine the slice where the child frame will be placed
        # We need to account for the possibility of the child being larger than the parent
        # This implementation assumes the child frame is simply clipped if it's too large.

        # Slice of the background/parent frame where the child will be inserted
        bg_slice_y_end = min(y + child_h, aligned_h)
        bg_slice_x_end = min(x + child_w, aligned_w)
        
        # Slice of the child frame to use (if it's larger than the available space)
        child_slice_h = bg_slice_y_end - y
        child_slice_w = bg_slice_x_end - x
        
        # Insert the child's frame into the background/parent frame
        frame[y:bg_slice_y_end, x:bg_slice_x_end] = child_frame[:child_slice_h, :child_slice_w]

        return frame

    def _get_position(self, parent_w, parent_h, child_w, child_h) -> tuple[float, float]:
        """Calculates the top-left (x, y) coordinates for the child based on alignment."""
        
        xidx = self.alignment.value % 3
        # x-coordinate
        match xidx:
        #if self.alignment in [Alignment.TopLeft, Alignment.Left, Alignment.BottomLeft]:
            case 0: x = 0
        #elif self.alignment in [Alignment.Top, Alignment.Center, Alignment.Bottom]:
            case 1: x = (parent_w - child_w) / 2
        #elif self.alignment in [Alignment.TopRight, Alignment.Right, Alignment.BottomRight]:
            case 2: x = parent_w - child_w

        # y-coordinate
        yidx = self.alignment.value // 3
        match yidx:
        #if self.alignment in [Alignment.TopLeft, Alignment.Top, Alignment.TopRight]:
            case 0: y = 0
        #elif self.alignment in [Alignment.Left, Alignment.Center, Alignment.Right]:
            case 1: y = (parent_h - child_h) / 2
        #elif self.alignment in [Alignment.BottomLeft, Alignment.Bottom, Alignment.BottomRight]:
            case 2: y = parent_h - child_h
        #else: # Default to CENTER
            case _: y = (parent_h - child_h) / 2

        return x, y


class Delayed(ProxyLayouterClip):
    def __init__(self, *, child: LayouterClip, delay: float, duration=None):
        super().__init__(child=child, duration=duration)
        self.delay = delay
        if self.duration: self.duration += self.delay

    def frame_function(self, t: float):
        t -= self.delay
        if t < 0: t = 0
        return super().frame_function(t)


class VideoClipAdapter(LayouterClip):
    def __init__(self, *, clip: VideoClip):
        super().__init__(duration=clip.duration)
        self.clip = clip
        self.size = self.clip.size

    def calculate_size(self, _): # type: ignore
        return self.size

    def frame_function(self, t: float) -> np.ndarray:
        frame = self.clip.get_frame(t)

        if self.clip.mask is not None:
            mask = 255 * self.clip.mask.get_frame(t) # type: ignore
            if mask.dtype != "uint8":
                mask = mask.astype("uint8")
            frame = np.dstack([frame, mask]) # type: ignore
        else:
            frame = np.dstack([frame, np.full((self.size[1], self.size[0]),255)]) # type: ignore
        return frame
