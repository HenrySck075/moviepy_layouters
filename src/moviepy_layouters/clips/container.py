
from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Protocol, Union, Tuple, assert_type, override
import numpy as np
from moviepy_layouters.infinity import INF, Infinity, is_finite, is_inf
from moviepy_layouters.clips.base import LayouterClip, Constraints, MultiChildLayouterClip

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
                    # Initially, set child constraints to a large value, 
                    # they will be properly merged in setup_layout
                    clip.size_constraints = Constraints(
                        max_width=INF, max_height=INF
                    )
    @override
    def debug_size_info(self, indent=0):
        super().debug_size_info(indent)
        for r_idx, row in enumerate(self.grid_children):
            print(" "*((indent+1)*2)+f"Row {r_idx}:")
            for c in row: c.debug_size_info(indent+2)

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
    
    @override
    def setup_layout(self):
        super().setup_layout()
        orig_constraint = self.size_constraints
        
        for r_idx, row in enumerate(self.grid_children):
            for c_idx, clip in enumerate(row):
                rs, cs = self.grid_size.row_heights[r_idx], self.grid_size.column_widths[c_idx]

                self.size_constraints = Constraints(
                    cs.get_pixel_value(orig_constraint.min_width) - cs.gap,
                    rs.get_pixel_value(orig_constraint.min_height) - rs.gap,
                    (cs.get_pixel_value(orig_constraint.max_width) - cs.gap) if is_finite(orig_constraint.max_width) else INF,
                    (rs.get_pixel_value(orig_constraint.max_height) - rs.gap) if is_finite(orig_constraint.max_height) else INF
                )
                clip.parent = self
                clip.setup_layout()
                if self.debug_size_info:
                    print(f"DEBUG (Grid): {orig_constraint} : {self.size_constraints} : {clip.size_constraints}")

                self.size_constraints = orig_constraint

    def calculate_final_size(self):
        """
        Calculates the final size of the grid clip based on grid_size.
        For simplicity, this example assumes the grid size completely dictates the clip's size.
        """
        # Calculate minimum required size based on pixel values
        """
        min_width = sum(
            c.get_pixel_value(self.size_constraints.min_width) 
            for c in self.grid_size.column_widths
        )

        min_height = sum(
            r.get_pixel_value(self.size_constraints.min_height) 
            for r in self.grid_size.row_heights
        )
        """

        # The final size is determined by the max of the calculated size 
        # and the minimum constraints
        final_width: int = self.size_constraints.min_width#max(min_width, self.size_constraints.min_width)
        final_height: int = self.size_constraints.min_height#max(min_height, self.size_constraints.min_height)

        # Apply max constraints if INF is not used
        if is_finite(self.size_constraints.max_width):
            final_width = min(final_width, self.size_constraints.max_width)
        if is_finite(self.size_constraints.max_height):
            final_height = min(final_height, self.size_constraints.max_height)
        
        self.size = (final_width, final_height)
        self.final_width = final_width
        self.final_height = final_height

        # Calculate final pixel dimensions for each cell
        self.final_col_widths = [
            c.get_pixel_value(final_width)+c.gap 
            for c in self.grid_size.column_widths
        ]
        self.final_row_heights = [
            r.get_pixel_value(final_height)+r.gap 
            for r in self.grid_size.row_heights
        ]

        # Call calculate_final_size on children now that parent size is known
        for row in self.grid_children:
            for clip in row:
                if clip:
                    # In a full layouter, you would also adjust the child's constraints
                    # based on the cell size *before* calling calculate_final_size.
                    # For this example, we skip constraint merging specific to grid cells
                    # and rely on the children to size themselves within the cell later.
                    clip.calculate_final_size()


    def frame_function(self, t: float):
        """
        Renders the grid by composing the frames of its children.
        """
        if self.size is None:
            # Should be set by calculate_final_size, but safety first
            self.calculate_final_size()

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
    def calculate_final_size(self):
        self.size = tuple(max(v) for v in zip(*[c.size for c in self.children]))

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
