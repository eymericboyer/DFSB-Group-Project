import os
import cv2
from tkinter import Tk, Label, Button, Entry, StringVar, Frame
from PIL import Image, ImageTk
from utils.image_processing import rotate_image, calculate_window
from utils.file_handling import save_data
import numpy as np


def initialize_ui(corrected_df, df, images_dir, output_file_path, input_file_path):
    def update_image_display():
        nonlocal image_tk, character_tk, current_index

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

        rotated_c1, rotated_c11, x_min, x_max, y_min, y_max, angle = window_data
        center = (image.shape[1] // 2, image.shape[0] // 2)
        rotated_image = rotate_image(image, angle, center)

        x_min, x_max = max(0, x_min), min(rotated_image.shape[1], x_max)
        y_min, y_max = max(0, y_min), min(rotated_image.shape[0], y_max)
        cropped_image = rotated_image[y_min:y_max, x_min:x_max]

        # Convert OpenCV image to Tkinter-compatible format for the cropped image
        image_rgb = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2RGB)
        image_pil = Image.fromarray(image_rgb)

        # Resize the cropped image to double its size right before showing it
        image_pil = image_pil.resize((image_pil.width * 2, image_pil.height * 2), Image.LANCZOS)
        image_tk = ImageTk.PhotoImage(image_pil)

        # Update the Label widget with the new cropped image and keep the reference
        image_label.config(image=image_tk)
        image_label.image = image_tk  # Ensure reference is stored

        # Update serial number in the entry field
        serial_var.set(row['serial_number'])
        file_name_var.set(row['image'])
        progress_var.set(f"{current_index + 1}/{len(corrected_df)}")
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

        # Create a character image based on the condition
        if all_inside:
            character_image = cropped_image.copy()  # Use cropped image for overlay
        else:
            character_image = rotated_image.copy()  # Show the whole image

        # Calculate font size
        if all_inside:
            target_width = cropped_image.shape[1] * 2  # Double the width of the cropped image
            target_height = character_image.shape[0] * 2
            font_scale = int(0.8 * (image_pil.height / 100))  # 80% of the height of the cropped window
        else:
            target_width = cropped_image.shape[1] * 2  # Double the width of the cropped image
            ratio = target_width / character_image.shape[1]
            target_height = int(character_image.shape[0] * ratio)
            font_scale = int(0.4 * (image.shape[0] / 100)) * ratio  # Reduce if showing the whole image

        # Overlay the characters on the character image
        for i, (x, y) in enumerate(rotated_positions):
            char = row['serial_number'][i]  # Get the corresponding character

            # Determine coordinates based on which image is being displayed
            if all_inside:
                text_size = cv2.getTextSize(char, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 3)[0]

                # Adjust coordinates for the cropped image
                adjusted_x = int(x) - x_min - text_size[0]
                adjusted_y = int(y) - y_min + text_size[1]
                cv2.putText(character_image, char, (adjusted_x, adjusted_y), cv2.FONT_HERSHEY_SIMPLEX, 2 * font_scale,
                            (0, 0, 255), 2)

            else:
                # Use original coordinates for the big image
                text_size = cv2.getTextSize(char, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 3)[0]
                print(text_size)
                adjusted_x = int(x) - text_size[0] // 2
                adjusted_y = int(y) + text_size[1] // 2
                cv2.putText(character_image, char, (adjusted_x, adjusted_y), cv2.FONT_HERSHEY_SIMPLEX, font_scale,
                            (0, 0, 255),
                            3)

        # Convert the character image to Tkinter-compatible format
        character_image_rgb = cv2.cvtColor(character_image, cv2.COLOR_BGR2RGB)
        character_image_pil = Image.fromarray(character_image_rgb)

        # Resize the character image if it's the big image to match the cropped image width (doubled)
        character_image_pil = character_image_pil.resize((target_width, target_height), Image.LANCZOS)

        # Convert the resized character image to Tkinter-compatible format
        character_tk = ImageTk.PhotoImage(character_image_pil)

        # Update the character_label with the character image
        character_label.config(image=character_tk)
        character_label.image = character_tk  # Ensure reference is stored

        # Resize the window if necessary
        total_height = image_pil.height + character_image_pil.height + 125
        total_width = int(character_image_pil.width * 1.35)
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
    image_label = Label(image_frame)
    image_label.grid(row=20, column=10, padx=10, pady=10)  # Image label in first column, first row

    # New label for showing the characters
    character_label = Label(image_frame)
    character_label.grid(row=10, column=10, padx=10, pady=10)  # Character label in first column, second row

    # Define global variables
    image_tk = None
    character_tk = None
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
    modifier_explanation_text.grid(row = 15, column=10, padx=10, pady=10)
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
