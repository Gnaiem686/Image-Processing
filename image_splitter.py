from PIL import Image, ImageDraw
import numpy as np
import os
import re
import time

def split_page_to_lines(image_path, output_dir, padding=5, min_line_gap=5, intensity_threshold=150):
    image = Image.open(image_path).convert("L") 
    image_array = np.array(image)

    row_sums = np.sum(image_array < intensity_threshold, axis=1)  

    lines = []
    in_line = False
    for i, value in enumerate(row_sums):
        if value > 15 and not in_line:  
            start = i
            in_line = True
        elif value <= 15 and in_line: 
            end = i
            in_line = False
            lines.append((start, end))

    merged_lines = []
    previous_start, previous_end = None, None

    for start, end in lines:
        if previous_end is not None and start - previous_end < min_line_gap:
            previous_end = end
        else:
            if previous_start is not None:
                merged_lines.append((previous_start, previous_end))
            previous_start, previous_end = start, end

    if previous_start is not None:
        merged_lines.append((previous_start, previous_end))
    lines = merged_lines

    os.makedirs(output_dir, exist_ok=True)

    debug_image = image.copy().convert("RGB")
    draw = ImageDraw.Draw(debug_image)

    line_images = []
    for idx, (start, end) in enumerate(lines):
        padded_start = max(0, start - padding)
        padded_end = min(image.height, end + padding)
        line_image = image.crop((0, padded_start, image.width, padded_end))
        line_path = os.path.join(output_dir, f"line_{idx + 1}.png")
        line_image.save(line_path)
        line_images.append(line_path)

        draw.rectangle([0, padded_start, image.width, padded_end], outline="red")

    debug_image.save("debug_lines.png")
    print(f"Saved debug image as debug_lines.png")
    print(f"Saved {len(line_images)} lines to {output_dir}")

    # Delete the image.png file after processing
    if os.path.exists(image_path):
        os.remove(image_path)
        print(f"Deleted {image_path}")

    return line_images

def get_next_page_dir(current_dir):
    # Extract the numeric part of the directory name
    match = re.search(r'\d+', current_dir)
    if match:
        page_number = int(match.group())
        next_page_number = page_number + 1
        # Replace the numeric part with the next page number
        next_dir = re.sub(r'\d+', str(next_page_number), current_dir)
        return next_dir
    else:
        # If no numeric part is found, append "_1" to the directory name
        return current_dir + "_1"

def watch_for_image(image_path, output_dir):
    while True:
        if os.path.exists(image_path):
            print(f"Found {image_path}, processing...")
            split_page_to_lines(image_path, output_dir)
            output_dir = get_next_page_dir(output_dir)
            print(f"Next output directory will be: {output_dir}")
        else:
            print(f"Waiting for {image_path}...")
        time.sleep(5)  # Check every 5 seconds

# Initial page directory
output_dir = "page1"

# Watch for image.png and process it automatically
image_path = "image.png"
watch_for_image(image_path, output_dir)
