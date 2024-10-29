import os
import cv2
from tkinter import Tk, Label, Button, Entry, StringVar, Frame
from PIL import Image, ImageTk
from matplotlib import pyplot as plt

from utils.image_processing import rotate_image, calculate_window
from utils.file_handling import save_data
import numpy as np


def initialize_ui(corrected_df, df, images_dir, output_file_path, input_file_path):
    def update_image_display():
        nonlocal current_index

        row = corrected_df.iloc[current_index]
        image_path = os.path.join(images_dir, str(row['image']))
        image = cv2.imread(image_path)
        if image is None:
            next_image()
            return

        window_data = calculate_window(row, 30, 40, image.shape)
        if window_data is None:
            next_image()
            return

        def get_rotate_parameters(window_data):
            x_min, x_max, y_min, y_max, angle = window_data
            center = (image.shape[1] // 2, image.shape[0] // 2)
            rotated_image = rotate_image(image, angle, center)
            x_min, x_max = max(0, x_min), min(rotated_image.shape[1], x_max)
            y_min, y_max = max(0, y_min), min(rotated_image.shape[0], y_max)
            return x_min, y_min, x_max, y_max, angle, center, rotated_image

        x_min, y_min, x_max, y_max, angle, center, rotated_image = get_rotate_parameters(window_data)

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

        rotated_positions, all_inside = get_rotated_positions_and_check_all_inside(row, center, angle, x_min, y_min,
                                                                                   x_max, y_max)

        def calculate_ratio(character_image, cropped_image):
            return 2 * cropped_image.shape[1] / character_image.shape[1]

        def get_images(rotated_image, all_inside):
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

        character_image, cropped_image, target_height, target_width, font_scale = get_images(rotated_image, all_inside)

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

        # Overlay the characters on the character image
        overlay_characters(character_image, rotated_positions, row, all_inside, font_scale, x_min, y_min)

        def convert_image_to_tkinter(image, target_height, target_width):
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            image_pil = Image.fromarray(image_rgb)

            # Resize the cropped image to double its size right before showing it
            image_pil = image_pil.resize((target_width, target_height), Image.LANCZOS)
            image_tk = ImageTk.PhotoImage(image_pil)

            return image_tk

        tk_cropped_image = convert_image_to_tkinter(cropped_image, cropped_image.shape[0] * 2,
                                                    cropped_image.shape[1] * 2)
        tk_character_image = convert_image_to_tkinter(character_image, target_height, target_width)


        def update_labels(row, unsure_text_var, character_image_label, tk_character_image, cropped_image_label, tk_cropped_image, serial_var, file_name_bar, progress_var, current_index, corrected_df):
            # Show unsure message if unsure
            try:
                if row['unsure'] == '1':
                    unsure_text_var.set("The accuracy of this image has been labeled as unsure.")
                elif row['unsure'] == '0':
                    unsure_text_var.set("The accuracy of this image has been labeled as sure.")
                else:
                    unsure_text_var.set("The accuracy of this image has not been labeled yet.")
            except KeyError:
                print(f"The file had no 'unsure' column.")
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

        update_labels(row, unsure_text_var, character_image_label, tk_character_image, cropped_image_label, tk_cropped_image, serial_var, file_name_var, progress_var, current_index, corrected_df)

        resize_window(tk_cropped_image, tk_character_image, root)

    def resize_window(image_pil, character_image_pil, root):
        # Resize the window if necessary
        total_height = image_pil.height() + character_image_pil.height() + 125
        total_width = int(character_image_pil.width() * 1.35)
        root.geometry(f"{total_width}x{total_height}")  # Add some extra height for buttons
        center_window()  # Center the window after updating the display

    def center_window():
        """Center the window on the screen."""
        root.update_idletasks()  # Ensures all widget sizes are computed
        window_width = root.winfo_width()
        window_height = root.winfo_height()
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x_cordinate = int((screen_width / 2) - (window_width / 2))
        y_cordinate = int((screen_height / 2) - (window_height / 2))
        root.geometry(f"{window_width}x{window_height}+{x_cordinate}+{y_cordinate}")

    def on_serial_change(*args):
        """Enable the edit button only if the serial number length is exactly 11 characters."""
        sure_button.config(state="normal" if len(serial_var.get()) == 11 else "disabled")
        unsure_button.config(state="normal" if len(serial_var.get()) == 11 else "disabled")

    def next_image():
        nonlocal current_index
        # Save the edited serial number if it's valid
        corrected_df.at[current_index, 'serial_number'] = serial_var.get()
        current_index += 1
        if current_index < len(corrected_df):
            update_image_display()
        else:
            save_data(corrected_df, df, output_file_path, input_file_path)
            root.quit()
            root.destroy()

    def on_sure():
        corrected_df.at[current_index, 'unsure'] = '0'
        next_image()

    def on_unsure():
        corrected_df.at[current_index, 'unsure'] = '1'
        next_image()

    def on_quit():
        save_data(corrected_df, df, output_file_path, input_file_path)
        root.destroy()

    root = Tk()
    root.title("Image Review")

    image_and_buttons_frame = Frame(root)
    image_and_buttons_frame.grid(row=20, column=10, padx=0, pady=0)

    image_frame = Frame(image_and_buttons_frame)
    image_frame.grid(row=10, column=10, padx=10, pady=10)

    title_frame = Frame(root)
    title_frame.grid(row=5, column=10, padx=10, pady=10)

    # Set up the UI without specifying a fixed size
    cropped_image_label = Label(image_frame)
    cropped_image_label.grid(row=20, column=10, padx=10, pady=10)  # Image label in first column, first row

    # New label for showing the characters
    character_image_label = Label(image_frame)
    character_image_label.grid(row=10, column=10, padx=10, pady=10)  # Character label in first column, second row

    # Define global variables
    current_index = 0

    serial_var = StringVar()  # StringVar to track the serial number in Entry
    file_name_var = StringVar()
    progress_var = StringVar()

    def update_colour(*args):
        text = unsure_text_var.get()
        if text.lower() == "the accuracy of this image has been labeled as unsure.":
            unsure_label.config(fg="red")
        elif text.lower() == "the accuracy of this image has been labeled as sure.":
            unsure_label.config(fg="green")
        else:
            unsure_label.config(fg="black")

    unsure_text_var = StringVar()
    unsure_text_var.trace_add("write", update_colour)

    unsure_label = Label(title_frame, textvariable=unsure_text_var)
    unsure_label.grid(row=5, column=10, padx=10, pady=10)

    buttons_frame = Frame(image_and_buttons_frame)
    buttons_frame.grid(row=10, column=20, padx=10, pady=10)

    # Text showing progress and file number
    file_name = Label(buttons_frame, textvariable=file_name_var)
    file_name.grid(row=5, column=10, padx=10, pady=10)
    progress = Label(buttons_frame, textvariable=progress_var)
    progress.grid(row=6, column=10, padx=10, pady=10)

    # Entry for serial number editing
    serial_entry = Entry(buttons_frame, textvariable=serial_var)
    serial_entry.grid(row=20, column=10, padx=10, pady=10)  # Place in the right column

    # Button definitions in the right column
    modifier_explanation_text = Label(buttons_frame, text="Enter Serial Number:")
    modifier_explanation_text.grid(row=15, column=10, padx=10, pady=10)
    sure_unsure_frame = Frame(buttons_frame)
    sure_unsure_frame.grid(row=30, column=10, padx=10, pady=10)
    sure_button = Button(sure_unsure_frame, text="Sure", command=on_sure, state="disabled")  # Initially disabled
    sure_button.grid(row=30, column=10, padx=10, pady=10)  # Edit button in the right column
    unsure_button = Button(sure_unsure_frame, text="Unsure", command=on_unsure, state="disabled")  # Initially disabled
    unsure_button.grid(row=30, column=11, padx=10, pady=10)  # Edit button in the right column
    quit_button = Button(buttons_frame, text="Save and Exit", command=on_quit)
    quit_button.grid(row=40, column=10, padx=10, pady=10)  # Quit button in the right column

    # Set up trace for real-time validation of serial number length
    serial_var.trace_add("write", on_serial_change)

    # Initialize display with the first image and serial number
    update_image_display()
    center_window()  # Center the window after initializing

    root.mainloop()
