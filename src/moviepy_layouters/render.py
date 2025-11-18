from typing import override
from moviepy import VideoClip

from moviepy_layouters.clips.base import Constraints, LayouterClip


class LayouterRenderer(VideoClip):
    def __init__(self, clip: LayouterClip, size: tuple[int, int], duration=None):
        self.clip = clip
        super().__init__(None, False, duration or clip.duration, True)
        self.frame_function = lambda t: self.clip.frame_function(t)[:,:,:3]

        self.clip.calculate_size(Constraints(*size, *size))
        self.size = self.clip.size

        self.mask = VideoClip(None, True, self.duration, True)
        self.mask.frame_function = lambda t: self.clip.frame_function(t)[:,:,3]/255
        self.mask.size = self.clip.size


        if clip.debug_clip_info: clip.debug_clip_info()
        
