import cv2
import numpy as np
from PIL import ImageTk, Image, ImageEnhance, ImageFilter
from matplotlib import pyplot as plt

from utils.image_processing import rotate_image


def get_rotate_parameters(window_data, image):
    """
    Calculates rotation parameters and crops boundaries for the image.

    Args:
        window_data (tuple): Contains `x_min`, `x_max`, `y_min`, `y_max`, and `angle` for defining cropping area.
        image (ndarray): Original image to be rotated.

    Returns:
        tuple: Contains:
            - x_min (int): Minimum x-boundary for cropping.
            - y_min (int): Minimum y-boundary for cropping.
            - x_max (int): Maximum x-boundary for cropping.
            - y_max (int): Maximum y-boundary for cropping.
            - angle (float): Angle for rotation.
            - center (tuple): Center coordinates of the image (x, y).
            - rotated_image (ndarray): Rotated version of the original image.
    """
    x_min, x_max, y_min, y_max, angle = window_data
    center = (image.shape[1] // 2, image.shape[0] // 2)
    rotated_image = rotate_image(image, angle, center)
    x_min, x_max = max(0, x_min), min(rotated_image.shape[1], x_max)
    y_min, y_max = max(0, y_min), min(rotated_image.shape[0], y_max)
    return x_min, y_min, x_max, y_max, angle, center, rotated_image


def get_rotated_positions_and_check_all_inside(row, center, angle, x_min, y_min, x_max, y_max):
    """
    Rotates and checks if character coordinates (C1 to C11) fall within the specified image boundaries.

    Args:
        row (pd.Series): Data row containing character position coordinates `C1` to `C11`.
        center (tuple): Center point of rotation (x, y).
        angle (float): Rotation angle in degrees.
        x_min, y_min, x_max, y_max (int): Minimum and maximum x and y boundaries for cropping.

    Returns:
        tuple: Contains:
            - rotated_positions (list): List of rotated (x, y) positions for each character.
            - all_inside (bool): `True` if all characters are within boundaries, `False` otherwise.
    """
    c_positions = [eval(row[f'C{i}'].replace(";", ",")) for i in range(1, 12)]
    rotated_positions = []
    for (x, y) in c_positions:
        rot_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated_point = np.dot(rot_matrix, np.array([x, y, 1]))
        rotated_positions.append((rotated_point[0], rotated_point[1]))

    all_inside = all(y_min <= y <= y_max and x_min <= x <= x_max for x, y in rotated_positions)
    return rotated_positions, all_inside


def calculate_ratio(character_image, cropped_image):
    """
    Calculates the ratio between the widths of character and cropped images.

    Args:
        character_image (ndarray): Image with characters overlaid.
        cropped_image (ndarray): Cropped section of the original image.

    Returns:
        float: Ratio of the cropped image width to character image width.
    """
    return 2 * cropped_image.shape[1] / character_image.shape[1]


def get_images(rotated_image, all_inside, x_min, y_min, x_max, y_max):
    """
    Generates character and cropped images with scaling and font parameters.

    Args:
        rotated_image (ndarray): Rotated version of the original image.
        all_inside (bool): Indicator if all characters fit within cropped region.
        x_min, y_min, x_max, y_max (int): Boundaries for cropping.

    Returns:
        tuple: Contains:
            - character_image (ndarray): Image with characters overlaid, cropped or full.
            - cropped_image (ndarray): Cropped section of the rotated image.
            - target_height (int): Desired height for character image.
            - target_width (int): Desired width for character image.
            - font_scale (float): Font scale for character labels.
    """
    cropped_image = rotated_image[y_min:y_max, x_min:x_max]
    if all_inside:
        character_image = cropped_image.copy()
        ratio_of_images = calculate_ratio(character_image, cropped_image)
        target_width = character_image.shape[1] * 2
        target_height = int(character_image.shape[0] * ratio_of_images)
        font_scale = int(0.8 * (target_height / 100))
    else:
        character_image = rotated_image.copy()
        ratio_of_images = calculate_ratio(character_image, cropped_image)
        target_width = cropped_image.shape[1] * 2
        ratio_of_images = target_width / character_image.shape[1]
        target_height = int(character_image.shape[0] * ratio_of_images)
        font_scale = int(0.4 * (character_image.shape[0] / 100)) * ratio_of_images
    return character_image, cropped_image, target_height, target_width, font_scale


def overlay_characters(character_image, rotated_positions, row, all_inside, font_scale, x_min, y_min):
    """
    Overlays serial number characters on the image at rotated positions.

    Args:
        character_image (ndarray): Image for character overlay.
        rotated_positions (list): List of rotated (x, y) coordinates for characters.
        row (pd.Series): Data row containing serial number for labeling.
        all_inside (bool): Indicator if characters fit within cropped image.
        font_scale (float): Scale for font size in overlay.
        x_min, y_min (int): Minimum x and y boundaries for cropping adjustments.
    """
    for i, (x, y) in enumerate(rotated_positions):
        char = row['serial_number'][i]
        if all_inside:
            text_size = cv2.getTextSize(char, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 3)[0]
            adjusted_x = int(x) - x_min - text_size[0]
            adjusted_y = int(y) - y_min + text_size[1]
            cv2.putText(character_image, char, (adjusted_x, adjusted_y), cv2.FONT_HERSHEY_SIMPLEX,
                        2 * font_scale, (0, 0, 255), 2)
        else:
            text_size = cv2.getTextSize(char, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 3)[0]
            adjusted_x = int(x) - text_size[0] // 2
            adjusted_y = int(y) + text_size[1] // 2
            cv2.putText(character_image, char, (adjusted_x, adjusted_y), cv2.FONT_HERSHEY_SIMPLEX, font_scale,
                        (0, 0, 255), 3)


def convert_image_to_tkinter(image, target_height, target_width):
    """
    Converts an OpenCV image to a Tkinter-compatible format with resizing.

    Args:
        image (ndarray): OpenCV image to be converted.
        target_height (int): Desired image height in pixels.
        target_width (int): Desired image width in pixels.

    Returns:
        PhotoImage: Tkinter-compatible image for display.
    """
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image_pil = Image.fromarray(image_rgb)
    image_pil = image_pil.resize((target_width, target_height), Image.LANCZOS)
    image_tk = ImageTk.PhotoImage(image_pil)
    return image_tk


def update_labels(row, unsure_text_var, character_image_label, tk_character_image, cropped_image_label,
                  tk_cropped_image, serial_var, file_name_var, progress_var, unsure_var, current_index, corrected_df):
    """
    Updates the Tkinter interface with labels and image references for the current image.

    Args:
        row (pd.Series): Data row containing metadata for the image.
        unsure_text_var (StringVar): Tkinter variable for unsure status message.
        character_image_label (Label): Tkinter label to display character overlay image.
        tk_character_image (PhotoImage): Tkinter-compatible character overlay image.
        cropped_image_label (Label): Tkinter label to display cropped image.
        tk_cropped_image (PhotoImage): Tkinter-compatible cropped image.
        serial_var (StringVar): Tkinter variable for serial number.
        file_name_var (StringVar): Tkinter variable for image filename.
        progress_var (StringVar): Tkinter variable for progress status.
        unsure_var (StringVar): Tkinter variable for unsure button status.
        current_index (int): Current index of the image being displayed.
        corrected_df (pd.DataFrame): DataFrame containing corrected image data.
    """
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

    character_image_label.config(image=tk_character_image)
    character_image_label.image = tk_character_image

    cropped_image_label.config(image=tk_cropped_image)
    cropped_image_label.image = tk_cropped_image

    serial_var.set(row['serial_number'])
    file_name_var.set(row['image'])
    progress_var.set(f"{current_index + 1}/{len(corrected_df)}")
    unsure_var.set("Unsure")


def enhance_contrast(photo_image, factor=2.0):
    """
    Enhances contrast of a Tkinter PhotoImage for display.

    Args:
        photo_image (PhotoImage): Tkinter-compatible image to enhance.
        factor (float): Contrast enhancement factor.

    Returns:
        PhotoImage: Contrast-enhanced image for Tkinter display.
    """
    pil_image = ImageTk.getimage(photo_image)
    enhancer = ImageEnhance.Contrast(pil_image)
    enhanced_image = enhancer.enhance(factor)
    return ImageTk.PhotoImage(enhanced_image)


def detect_edges(photo_image):
    """
    Applies edge detection filter to a Tkinter PhotoImage.

    Args:
        photo_image (PhotoImage): Tkinter-compatible image for edge detection.

    Returns:
        PhotoImage: Image with edges detected for Tkinter display.
    """
    pil_image = ImageTk.getimage(photo_image)
    if pil_image.mode != 'RGB':
        pil_image = pil_image.convert('RGB')
    grayscale_image = pil_image.convert("L")
    edge_image = grayscale_image.filter(ImageFilter.FIND_EDGES)
    return ImageTk.PhotoImage(edge_image)


def draw_filtered_images(cropped_label, character_label):
    """
    Applies contrast enhancement and edge detection to cropped and character images.

    Args:
        cropped_label (Label): Tkinter label for displaying the cropped image.
        character_label (Label): Tkinter label for displaying the character overlay image.

    Returns:
        None
    """
    new_cropped_image = enhance_contrast(detect_edges(cropped_label.image), 5)
    new_character_image = enhance_contrast(cropped_label.image)
    character_label.config(image=new_character_image)
    character_label.image = new_character_image
    cropped_label.config(image=new_cropped_image)
    cropped_label.image = new_cropped_image
    return
