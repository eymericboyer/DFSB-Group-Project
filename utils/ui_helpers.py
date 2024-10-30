import cv2
import numpy as np
from PIL import ImageTk, Image, ImageEnhance, ImageFilter
from matplotlib import pyplot as plt

from utils.image_processing import rotate_image


def get_rotate_parameters(window_data, image):
    x_min, x_max, y_min, y_max, angle = window_data
    center = (image.shape[1] // 2, image.shape[0] // 2)
    rotated_image = rotate_image(image, angle, center)
    x_min, x_max = max(0, x_min), min(rotated_image.shape[1], x_max)
    y_min, y_max = max(0, y_min), min(rotated_image.shape[0], y_max)
    return x_min, y_min, x_max, y_max, angle, center, rotated_image


def get_rotated_positions_and_check_all_inside(row, center, angle, x_min, y_min, x_max, y_max):
    # Determine coordinates for C1 to C11
    c_positions = [eval(row[f'C{i}'].replace(";", ",")) for i in range(1, 12)]

    # Rotate coordinates for C1 to C11 using the positive angle
    rotated_positions = []
    for (x, y) in c_positions:
        # Apply the rotation to get the original coordinates relative to the center
        rot_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated_point = np.dot(rot_matrix, np.array([x, y, 1]))
        rotated_positions.append((rotated_point[0], rotated_point[1]))

    # Check if all points are within the cropped image
    all_inside = all(y_min <= y <= y_max and x_min <= x <= x_max for x, y in rotated_positions)

    return rotated_positions, all_inside


def calculate_ratio(character_image, cropped_image):
    return 2 * cropped_image.shape[1] / character_image.shape[1]


def get_images(rotated_image, all_inside, x_min, y_min, x_max, y_max):
    # Cropped Image
    cropped_image = rotated_image[y_min:y_max, x_min:x_max]

    # Character Image
    if all_inside:
        character_image = cropped_image.copy()  # Use cropped image for overlay
        ratio_of_images = calculate_ratio(character_image, cropped_image)
        target_width = character_image.shape[1] * 2  # Double the width of the cropped image
        target_height = int(character_image.shape[0] * ratio_of_images)
        font_scale = int(0.8 * (target_height / 100))  # 80% of the size of the cropped window
    else:
        character_image = rotated_image.copy()  # Show the whole image
        ratio_of_images = calculate_ratio(character_image, cropped_image)
        target_width = cropped_image.shape[1] * 2
        ratio_of_images = target_width / character_image.shape[1]
        target_height = int(character_image.shape[0] * ratio_of_images)
        font_scale = int(
            0.4 * (character_image.shape[0] / 100)) * ratio_of_images  # Reduce if showing the whole image
    return character_image, cropped_image, target_height, target_width, font_scale


def overlay_characters(character_image, rotated_positions, row, all_inside, font_scale, x_min, y_min):
    for i, (x, y) in enumerate(rotated_positions):
        char = row['serial_number'][i]  # Get the corresponding character

        # Determine coordinates based on which image is being displayed
        if all_inside:
            text_size = cv2.getTextSize(char, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 3)[0]

            # Adjust coordinates for the cropped image
            adjusted_x = int(x) - x_min - text_size[0]
            adjusted_y = int(y) - y_min + text_size[1]
            cv2.putText(character_image, char, (adjusted_x, adjusted_y), cv2.FONT_HERSHEY_SIMPLEX,
                        2 * font_scale,
                        (0, 0, 255), 2)

        else:
            # Use original coordinates for the big image
            text_size = cv2.getTextSize(char, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 3)[0]
            adjusted_x = int(x) - text_size[0] // 2
            adjusted_y = int(y) + text_size[1] // 2
            cv2.putText(character_image, char, (adjusted_x, adjusted_y), cv2.FONT_HERSHEY_SIMPLEX, font_scale,
                        (0, 0, 255),
                        3)


def convert_image_to_tkinter(image, target_height, target_width):
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image_pil = Image.fromarray(image_rgb)

    # Resize the cropped image to double its size right before showing it
    image_pil = image_pil.resize((target_width, target_height), Image.LANCZOS)
    image_tk = ImageTk.PhotoImage(image_pil)

    return image_tk


def update_labels(row, unsure_text_var, character_image_label, tk_character_image, cropped_image_label,
                  tk_cropped_image, serial_var, file_name_var, progress_var, unsure_var, current_index, corrected_df):
    # Show unsure message if unsure
    try:
        if str(int(row['unsure'])) == '1':
            unsure_text_var.set("The accuracy of this image has been labeled as unsure.")
        elif str(int(row['unsure'])) == '0':
            unsure_text_var.set("The accuracy of this image has been labeled as sure.")
        else:
            unsure_text_var.set("The accuracy of this image has not been labeled yet.")
    except KeyError:
        print(f"The file had no 'unsure' column.")
        unsure_text_var.set("The accuracy of this image has not been labeled yet.")
    except ValueError:
        unsure_text_var.set("The accuracy of this image has not been labeled yet.")

    # Update the character_image_label with the character image
    character_image_label.config(image=tk_character_image)
    character_image_label.image = tk_character_image  # Ensure reference is stored

    # Update the Label widget with the new cropped image and keep the reference
    cropped_image_label.config(image=tk_cropped_image)
    cropped_image_label.image = tk_cropped_image  # Ensure reference is stored

    # Update serial number in the entry field
    serial_var.set(row['serial_number'])
    file_name_var.set(row['image'])
    progress_var.set(f"{current_index + 1}/{len(corrected_df)}")
    unsure_var.set("Unsure")


def enhance_contrast(photo_image, factor=2.0):
    """
    Converts a Tkinter PhotoImage to a PIL Image, enhances the contrast, and converts back.
    """
    # Convert PhotoImage to PIL Image
    pil_image = ImageTk.getimage(photo_image)

    # Apply contrast enhancement
    enhancer = ImageEnhance.Contrast(pil_image)
    enhanced_image = enhancer.enhance(factor)

    # Convert back to PhotoImage
    return ImageTk.PhotoImage(enhanced_image)


def detect_edges(photo_image):
    """
    Converts a Tkinter PhotoImage to a PIL Image, applies edge detection, and converts back.
    """
    # Convert PhotoImage to PIL Image
    pil_image = ImageTk.getimage(photo_image)

    # Ensure image is in RGB mode (or grayscale) for consistent edge detection
    if pil_image.mode != 'RGB':
        pil_image = pil_image.convert('RGB')

    # Convert image to grayscale
    grayscale_image = pil_image.convert("L")

    # Apply edge detection filter
    edge_image = grayscale_image.filter(ImageFilter.FIND_EDGES)

    # Convert back to PhotoImage for Tkinter display
    return ImageTk.PhotoImage(edge_image)


def draw_filtered_images(cropped_label, character_label):
    new_cropped_image = enhance_contrast(detect_edges(cropped_label.image), 5)
    new_character_image = enhance_contrast(cropped_label.image)
    character_label.config(image=new_character_image)
    character_label.image = new_character_image
    cropped_label.config(image=new_cropped_image)
    cropped_label.image = new_cropped_image
    return



