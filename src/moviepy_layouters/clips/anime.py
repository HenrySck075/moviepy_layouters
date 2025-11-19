from typing import Optional, override
from moviepy_layouters.clips.base import LayouterClip, SingleChildLayouterClip
from moviepy_layouters.clips.curves import Curve, clamp

from moviepy_layouters.clips.visuals import Offseted, Offset

class AnimatedClip(SingleChildLayouterClip):
    duration: float
    "Base class for animated clips"
    def __init__(self, duration: float, curve: Curve, has_constant_size=True):
        "child (Optional[LayouterClip]): This parameter may be used by subclasses"
        super().__init__(None, duration, has_constant_size)
        self.curve = curve

    @override
    def debug_clip_meta(self):
        return super().debug_clip_meta() + f" | Duration: {self.duration} | Curve: {self.curve}"
    
    def frame_anim_function(self, at: float, t: float):
        return super().frame_function(t)
    @override
    def frame_function(self, t: float):
        return self.frame_anim_function(clamp(self.curve(t/self.duration),0,1), t)


class AnimatedSlide(AnimatedClip):
    def __init__(self, child: LayouterClip, start: Offset, end: Offset, duration: float, curve: Curve, has_constant_size=True):
        super().__init__(duration, curve, has_constant_size)
        self.slider = self.child = Offseted(child, start, duration, has_constant_size)
        self.startdx = start.dx
        self.startdy = start.dy
        self.enddx = end.dx
        self.enddy = end.dy
        self.dx = end.dx - start.dx
        self.dy = end.dy - start.dy

    def frame_anim_function(self, at: float, t: float):
        self.slider.offset.dx = self.startdx + self.dx*at if at < 1 else self.enddx
        self.slider.offset.dy = self.startdy + self.dy*at if at < 1 else self.enddy
        return self.slider.frame_function(t)


