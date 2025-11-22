import numpy as np

def paste_image_array(canvas: np.ndarray, frame: np.ndarray, pos: tuple[int,int]):
    height, width, _ = canvas.shape
    child_h, child_w, _ = frame.shape
    x,y = pos

    # Use the alpha channel to blend the child frame onto the canvas
    # We assume a 4-channel (RGBA) format for blending.
    
    # Extract child's color and alpha channels
    child_rgb = frame[:, :, :3]
    child_alpha = frame[:, :, 3] / 255.0

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


