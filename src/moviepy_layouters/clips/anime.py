from typing import Optional, override
from moviepy_layouters.clips.base import LayouterClip, SingleChildLayouterClip
from moviepy_layouters.clips.curves import Curve

from moviepy_layouters.clips.visuals import Offseted, Offset

class AnimatedClip(SingleChildLayouterClip):
    duration: float
    "Base class for animated clips"
    def __init__(self, duration: float, curve: Curve, has_constant_size=True):
        "child (Optional[LayouterClip]): This parameter may be used by subclasses"
        super().__init__(None, duration, has_constant_size)
        self.curve = curve
    
    def frame_anim_function(self, at: float, t: float):
        return super().frame_function(0)
    @override
    def frame_function(self, t: float):
        return self.frame_anim_function(self.curve(t/self.duration), t)


class AnimatedSlide(AnimatedClip):
    def __init__(self, child: LayouterClip, start: Offset, end: Offset, duration: float, curve: Curve, has_constant_size=True):
        super().__init__(duration, curve, has_constant_size)
        self.slider = self.child = Offseted(child, start, duration, has_constant_size)
        self.start = start
        self.end = end

    def frame_anim_function(self, at: float, t: float):
        self.slider.offset.dx = self.start.dx + (self.end.dx - self.start.dx)*at
        self.slider.offset.dy = self.start.dy + (self.end.dy - self.start.dy)*at
        return self.slider.frame_function(t)


