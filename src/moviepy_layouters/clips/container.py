
from dataclasses import dataclass
from enum import Enum
from sys import version
from typing import Optional, List, Protocol, Union, Tuple, assert_type, override
import numpy as np
from moviepy_layouters.clips.visuals import Alignment
from moviepy_layouters.infinity import INF, Infinity, is_finite, is_inf
from moviepy_layouters.clips.base import LayouterClip, Constraints, MultiChildLayouterClip, ProxyLayouterClip


class AxisAlignment(Enum):
    Start = 0,
    Center = 1,
    End = 2

class Axis(Enum):
    Vertical = 1
    Horizontal = 0

class Flex(ProxyLayouterClip):
    def __init__(self, child: LayouterClip, flex=1, duration=None, has_constant_size=True):
        super().__init__(child, duration, has_constant_size)
        self.flex = flex

class ListView(MultiChildLayouterClip):
    def __init__(self, children: list[LayouterClip], axis = Axis.Vertical, gap: int = 0, main_axis_alignment = AxisAlignment.Start, cross_axis_alignment = AxisAlignment.Start, duration=None, has_constant_size=True):
        super().__init__(children, duration, has_constant_size)
        self.main_axis_alignment = main_axis_alignment
        self.cross_axis_alignment = cross_axis_alignment
        self.gap = gap
        self.axis = axis

    @override
    def calculate_size(self, constraints):
        flex_children: list[Flex] = []
        main_axis_size = 0
        cross_axis_size = 0

        con = Constraints(0,0, constraints.max_width, constraints.max_height)

        is_vertical = self.axis == Axis.Vertical

        # I'm well aware of the presence of getattr but we are focusing on speed here
        for c in self.children:
            if type(c) is Flex:
                flex_children.append(c)
            else:
                print(f"Constraints: {con}")
                cs = c.calculate_size(con)
                main_axis_size += cs[self.axis.value]
                cross_axis_size = min(con.max_width if is_vertical else con.max_height, max(cross_axis_size, cs[(self.axis.value+1)%2]))
                if is_vertical:
                    con.min_height = min(con.max_height, con.min_height+main_axis_size+self.gap) # type: ignore
                else:
                    con.min_width = min(con.max_width, con.min_width+main_axis_size+self.gap) # type: ignore

        if (
            len(flex_children) != 0 and 
            (constraints.max_height if is_vertical else constraints.max_width) is INF
        ):
            raise ValueError("The axis of the ListView has an infinite maximum size but a Flex child was found. Please set the maximum constraints to a finite number.")

        if len(flex_children) == 0:
            # just take the min constraints from con its the same as the total size
            self.size = (con.min_width, con.min_height)
        else:
            self.size: tuple[int, int] = (cross_axis_size, con.max_height) if is_vertical else (con.max_width, cross_axis_size) # type: ignore
            print(f"Size: {self.size}")
            remaining = self.size[self.axis.value] - main_axis_size
            piece = (remaining / len(flex_children)).__floor__() # type: ignore
            for c in flex_children:
                s: tuple[int, int] = (self.size[0], piece) if is_vertical else (piece, self.size[1])
                c.calculate_size(Constraints(*s, *s))
                remaining -= piece
                if abs(remaining) == 1: piece += remaining
                print(f"remaining={remaining}")

        return self.size

    @override
    def frame_function(self, t: float) -> np.ndarray:
        # Obtain an empty clip
        frame = LayouterClip.frame_function(self, 0)
        # This assumes the sizes were correctly calculated and that they dont change their mind after calculate_size
        # (that is theoretically fine but numpy doesnt agree so pls dont do that)
        x, y = 0,0
        is_vertical = self.axis == Axis.Vertical
        for i in self.children:
            f = i.frame_function(t)
            w,h = i.size
            frame[y:y+h, x:x+w] = f
            if is_vertical: y+=h
            else: x+=w
        
        return frame
              
         

@dataclass
class GridCellSize:
    """Defines the width or height of a single grid cell."""
    value: float  # The actual value (pixels or percentage)
    is_percentage: bool = False

    gap: int = 0

    def get_pixel_value(self, total_dimension: int) -> int:
        """Calculates the pixel value based on the total dimension (width/height)."""
        if self.is_percentage:
            # Ensure pixel value is an integer
            return int(self.value / 100 * total_dimension)
        return int(self.value)


@dataclass
class GridSize:
    """Defines the sizes for rows and columns."""
    column_widths: List[GridCellSize]
    row_heights: List[GridCellSize]

class Grid(LayouterClip):
    def __init__(
        self,
        grid_children: List[List[LayouterClip]],
        grid_size: GridSize,
        duration: Optional[float] = None,
        has_constant_size: bool = True
    ):
        super().__init__(duration=duration, has_constant_size=has_constant_size)

        self.grid_children = grid_children
        self.grid_size = grid_size
        self._validate_grid_shape()

        self.rows = len(grid_children)
        self.cols = len(grid_children[0]) if self.rows > 0 else 0

        # Set parents for children and merge constraints
        for r_idx, row in enumerate(self.grid_children):
            for c_idx, clip in enumerate(row):
                if clip:
                    clip.parent = self

    @override
    def debug_clip_info(self, indent=0):
        super().debug_clip_info(indent)
        for r_idx, row in enumerate(self.grid_children):
            print(" "*((indent+1)*2)+f"Row {r_idx}:")
            for c in row: c.debug_clip_info(indent+2)

    def _validate_grid_shape(self):
        """Checks if the grid_children is rectangular."""
        if not self.grid_children:
            return  # Empty grid is valid

        first_row_len = len(self.grid_children[0])
        for row in self.grid_children:
            if len(row) != first_row_len:
                raise ValueError("The grid_children list must be rectangular (all rows must have the same number of columns).")

        # Basic validation for grid_size
        if len(self.grid_size.row_heights) != len(self.grid_children):
             raise ValueError("Number of `row_heights` must match the number of rows in `grid_children`.")
        if len(self.grid_size.column_widths) != len(self.grid_children[0]):
             raise ValueError("Number of `column_widths` must match the number of columns in `grid_children`.")
   
    def calculate_size(self, constraints):
        """
        Calculates the final size of the grid clip and its children based on grid_size 
        and the parent's constraints.
        """

        # 1. Setup Layout (Calculate constraints for children)
        # Note: self.size_constraints is replaced by constraints (parent_constraints)
        for r_idx, row in enumerate(self.grid_children):
            for c_idx, clip in enumerate(row):
                rs, cs = self.grid_size.row_heights[r_idx], self.grid_size.column_widths[c_idx]

                # Calculate child constraints based on parent_constraints (constraints)
                child_constraints = Constraints(
                    cs.get_pixel_value(constraints.min_width) - cs.gap,
                    rs.get_pixel_value(constraints.min_height) - rs.gap,
                    (cs.get_pixel_value(constraints.max_width) - cs.gap) if is_finite(constraints.max_width) else INF,
                    (rs.get_pixel_value(constraints.max_height) - rs.gap) if is_finite(constraints.max_height) else INF
                )
                
                # Note: Setting clip.parent is done in __init__
                # clip.parent = self 
                
                # Recursively calculate the child's size based on its constraints
                clip.calculate_size(child_constraints) # Assuming LayouterClip has this new method

                # No need to reset self.size_constraints as it's not used/stored in self anymore

        # 2. Calculate Final Size of the Grid Clip (self)
        
        # In the original code, the grid's final size was essentially pinned to the 
        # parent's minimum constraint, clipped by the parent's maximum constraint.
        
        final_width: int = constraints.min_width
        final_height: int = constraints.min_height

        # Apply max constraints if INF is not used
        if is_finite(constraints.max_width):
            final_width = min(final_width, constraints.max_width)
        if is_finite(constraints.max_height):
            final_height = min(final_height, constraints.max_height)
        
        self.size = (final_width, final_height)
        self.final_width = final_width
        self.final_height = final_height

        # Calculate final pixel dimensions for each cell (including gap)
        # This is needed for the rendering phase (not requested, but essential data)
        self.final_col_widths = [
            c.get_pixel_value(final_width) + c.gap 
            for c in self.grid_size.column_widths
        ]
        self.final_row_heights = [
            r.get_pixel_value(final_height) + r.gap 
            for r in self.grid_size.row_heights
        ]

        # The function should return the newly calculated size of the Grid clip
        return self.size
    def frame_function(self, t: float):
        """
        Renders the grid by composing the frames of its children.
        """

        # Create an empty background image for the grid
        frame = np.zeros((self.size[1],self.size[0], 4), dtype=np.uint8)

        y_offset = 0
        for r_idx, row in enumerate(self.grid_children):
            row_height = self.final_row_heights[r_idx]
            x_offset = 0
            for c_idx, clip in enumerate(row):
                col_width = self.final_col_widths[c_idx]

                if clip:
                    # Get the child's frame
                    child_frame = clip.get_frame(t)

                    # Ensure the child frame fits into the cell (clipping/resizing logic would go here)
                    # For simplicity, we assume child.size <= (col_width, row_height)
                    child_w, child_h = clip.size
                    
                    # Calculate position within the grid (top-left corner of the cell)
                    # For a simple approach, we center the child within its cell
                    # Horizontal centering
                    x_start = x_offset + (col_width - child_w) // 2
                    x_end = x_start + child_w
                    
                    # Vertical centering
                    y_start = y_offset + (row_height - child_h) // 2
                    y_end = y_start + child_h

                    # Ensure bounds are within the main frame
                    if x_start < 0: x_start = 0
                    if y_start < 0: y_start = 0
                    if x_end > self.final_width: x_end = self.final_width
                    if y_end > self.final_height: y_end = self.final_height

                    # Composite the child frame onto the main frame
                    # This assumes simple overlay/replace (no blending)
                    #print(x_start, x_end, y_start, y_end, frame[y_start:y_end, x_start:x_end].shape, frame.shape, child_frame.shape)
                    frame[y_start:y_end, x_start:x_end] = child_frame

                x_offset += col_width
            y_offset += row_height

        return frame


class Sequential(MultiChildLayouterClip):
    """
    A clip that plays clips in sequential order.

    Requires all clips to have duration.

    :param duration: Duration of the clips. If there's no clip at a specific time (happens if duration is longer than total duration of clips), an empty frame is returned
    """

    def __init__(self, children: list[LayouterClip], alignment:Alignment, duration=None, has_constant_size=True):
        assert(all(child.duration != None for child in children))
        if duration is None:
            duration = sum(child.duration for child in children) # type: ignore
        super().__init__(children, duration, has_constant_size)
        self.alignment = alignment

    @override
    def calculate_size(self, constraints):
        self.size = tuple(max(v) for v in zip(*[c.calculate_size(constraints) for c in self.children]))
        return self.size

    @override
    def frame_function(self, t: float):
        "Returns a WxHx4 numpy array at a specified t"        
        current_time = 0.0
        active_child = None
        
        # 1. Determine the active child clip and the relative time t'
        t_prime = 0
        for child in self.children:
            # Check if 't' falls within the current child's time segment
            child_duration: float = child.duration  # Assuming duration is not None as per assert in __init__ # type: ignore
            
            if t < current_time + child_duration:
                active_child = child
                # t_prime is the relative time within the active child
                t_prime = t - current_time
                break
            
            current_time += child_duration
        
        # This should theoretically not happen if duration is correct, but as a safeguard:
        if active_child is None:
            W, H = self.size
            return np.zeros((H, W, 4), dtype=np.uint8) # Return empty frame
            
        # 2. Get the frame from the active child clip
        child_frame = active_child.get_frame(t_prime)
        
        # Get dimensions
        W, H = self.size
        child_H, child_W, _ = child_frame.shape
        
        # Calculate padding/offset based on alignment
        dx = 0 # Horizontal offset
        dy = 0 # Vertical offset
        
        # --- Calculate horizontal offset (dx) ---
        if self.alignment in {Alignment.TopRight, Alignment.Right, Alignment.BottomRight}:
            dx = W - child_W # Align right
        elif self.alignment in {Alignment.Top, Alignment.Center, Alignment.Bottom}:
            dx = (W - child_W) // 2 # Center horizontally
        # Else: dx remains 0 (Align left)
        
        # --- Calculate vertical offset (dy) ---
        if self.alignment in {Alignment.BottomLeft, Alignment.Bottom, Alignment.BottomRight}:
            dy = H - child_H # Align bottom
        elif self.alignment in {Alignment.Left, Alignment.Center, Alignment.Right}:
            dy = (H - child_H) // 2 # Center vertically
        # Else: dy remains 0 (Align top)

        # 3. Create the final frame and place the child frame onto it
        final_frame = np.zeros((H, W, 4), dtype=np.uint8) # The canvas for the combined clip
        
        # Place the child frame onto the final frame using the calculated offsets
        # Note: final_frame slice is [row_start:row_end, col_start:col_end]
        final_frame[dy : dy + child_H, dx : dx + child_W] = child_frame
        
        return final_frame


class Stack(MultiChildLayouterClip):
    """
    A LayouterClip that stacks all its children on top of each other.
    The size of the stack is the largest size of its children.
    Each child's position is determined by the alignment property.
    """
    def __init__(self, children: list[LayouterClip] = [], alignment: Alignment = Alignment.TopLeft, duration=None, has_constant_size=True):
        super().__init__(children, duration, has_constant_size)
        self.alignment = alignment
        # Stores (x, y) offset for each child after size calculation
        self._child_offsets: list[tuple[int, int]] = []

    def calculate_size(self, constraints: Constraints):
        """
        1. Calculate the size for all children first, using the parent's constraints.
        2. Determine the stack's size as the max width and height of all children's calculated sizes.
        3. Determine the (x, y) offset for each child based on the stack's final size and the alignment.
        """
        # 1. Calculate the size for all children
        # We pass the parent's constraints down, as children may want to fill the available space.
        child_sizes = []
        child_constraints = Constraints(0,0,constraints.max_width,constraints.max_height)
        for child in self.children:
            child_size = child.calculate_size(child_constraints)
            child_sizes.append(child_size)

        # 2. Determine the stack's size (max width and height of all children)
        max_w = max([w for w, h in child_sizes] + [constraints.min_width])
        max_h = max([h for w, h in child_sizes] + [constraints.min_height])

        # Clamp the calculated size within max constraints
        self.size = ( # type: ignore # would never be inf
            min(max_w, constraints.max_width),
            min(max_h, constraints.max_height)
        ) 
        final_width, final_height = self.size

        # 3. Determine the (x, y) offset for each child
        self._child_offsets = []
        for child_w, child_h in child_sizes:
            x_offset, y_offset = self._get_offset(final_width, final_height, child_w, child_h)
            self._child_offsets.append((x_offset, y_offset))

        return self.size

    def _get_offset(self, parent_w: int, parent_h: int, child_w: int, child_h: int) -> tuple[int, int]:
        """Calculates the top-left (x, y) offset based on the parent/stack size and child size."""
        # Calculate horizontal (x) position
        if self.alignment in [Alignment.TopLeft, Alignment.Left, Alignment.BottomLeft]:
            x = 0
        elif self.alignment in [Alignment.Top, Alignment.Center, Alignment.Bottom]:
            x = (parent_w - child_w) // 2
        else: # TopRight, Right, BottomRight
            x = parent_w - child_w

        # Calculate vertical (y) position
        if self.alignment in [Alignment.TopLeft, Alignment.Top, Alignment.TopRight]:
            y = 0
        elif self.alignment in [Alignment.Left, Alignment.Center, Alignment.Right]:
            y = (parent_h - child_h) // 2
        else: # BottomLeft, Bottom, BottomRight
            y = parent_h - child_h

        return x, y

    def frame_function(self, t: float) -> np.ndarray:
        """
        Renders the frame by drawing each child clip onto a blank canvas
        at its calculated offset, starting from the first child.
        """
        if not self.children:
            return super().frame_function(t) # Returns an empty frame of the calculated size

        width, height = self.size
        # Create a blank, transparent canvas (WxHx4)
        canvas = LayouterClip.frame_function(self, t) 
        
        # Draw each child frame onto the canvas
        for i, child in enumerate(self.children):
            child_frame = child.get_frame(t)
            child_h, child_w, _ = child_frame.shape
            x, y = self._child_offsets[i]

            # Use the alpha channel to blend the child frame onto the canvas
            # We assume a 4-channel (RGBA) format for blending.
            
            # Extract child's color and alpha channels
            child_rgb = child_frame[:, :, :3]
            child_alpha = child_frame[:, :, 3] / 255.0

            # Region of the canvas to draw on (clamped to ensure it's within bounds)
            y_start = y
            y_end = min(y + child_h, height)
            x_start = x
            x_end = min(x + child_w, width)

            # Corresponding region in the child frame (in case it was clipped)
            child_y_end = y_end - y_start
            child_x_end = x_end - x_start
            
            # Slice the child frame and alpha to the size of the drawing region
            draw_rgb = child_rgb[:child_y_end, :child_x_end]
            draw_alpha = child_alpha[:child_y_end, :child_x_end]
            
            # Slice the canvas region
            canvas_region = canvas[y_start:y_end, x_start:x_end]

            # Weighted average for blending: new_color = (1-alpha)*old_color + alpha*new_color
            # Perform blending only on the area where the child frame is actually drawn
            for c in range(3): # RGB channels
                # Multiply alpha channel to make it (H, W, 1) for broadcasting
                # no
                # alpha_channel = draw_alpha[:, :, np.newaxis]
                
                # Blend the color (preserving the existing background if alpha < 1)
                old_color = canvas_region[:, :, c]
                new_color = draw_rgb[:, :, c]
                
                blended_color = (1.0 - draw_alpha) * old_color + draw_alpha * new_color
                canvas_region[:, :, c] = blended_color.astype(np.uint8)

            # Update the alpha channel of the canvas (max of current alpha and new alpha)
            old_alpha = canvas_region[:, :, 3] / 255.0
            new_canvas_alpha = old_alpha + draw_alpha * (1.0 - old_alpha)
            canvas_region[:, :, 3] = (new_canvas_alpha * 255).astype(np.uint8)

        return canvas
