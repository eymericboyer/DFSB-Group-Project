import os
import cv2
from tkinter import Tk, Label, Button, Entry, StringVar, Frame
from PIL import Image, ImageTk

from utils.image_processing import rotate_image, calculate_window
from utils.file_handling import save_data
import numpy as np

from utils.ui_helpers import get_rotate_parameters, get_rotated_positions_and_check_all_inside, get_images, \
    overlay_characters, convert_image_to_tkinter, update_labels, draw_filtered_images


def initialize_ui(corrected_df, df, images_dir, output_file_path, input_file_path):
    """
    Initializes the graphical user interface for image review and editing.

    Args:
        corrected_df (pd.DataFrame): DataFrame containing corrected data entries.
        df (pd.DataFrame): Original DataFrame.
        images_dir (str): Directory containing the images.
        output_file_path (str): Path for saving the output file.
        input_file_path (str): Path to the input file.
    """

    def go_to_index():
        """
        Navigates to the image at the index specified in the index entry box.
        Handles input validation and ensures the index is within range.
        """
        try:
            new_index = int(index_entry.get()) - 1
            if 0 <= new_index < len(corrected_df):
                nonlocal current_index
                current_index = new_index
                update_image_display(current_index)
            else:
                print("Index out of range")
        except ValueError:
            print("Invalid index entered")

    def update_image_display(index):
        """
        Updates the image display and associated information based on the specified index.

        Args:
            index (int): Index of the image to display.
        """
        row = corrected_df.iloc[index]
        index_entry.delete(0, "end")
        index_entry.insert(0, str(index + 1))

        image_path = os.path.join(images_dir, str(row['image']))
        image = cv2.imread(image_path)
        if image is None:
            next_image()
            return

        window_data = calculate_window(row, 30, 40, image.shape)
        if window_data is None:
            next_image()
            return

        x_min, y_min, x_max, y_max, angle, center, rotated_image = get_rotate_parameters(window_data, image)

        rotated_positions, all_inside = get_rotated_positions_and_check_all_inside(row, center, angle, x_min, y_min,
                                                                                   x_max, y_max)

        character_image, cropped_image, target_height, target_width, font_scale = get_images(rotated_image, all_inside,
                                                                                             x_min, y_min, x_max, y_max)

        # Overlay the characters on the character image
        overlay_characters(character_image, rotated_positions, row, all_inside, font_scale, x_min, y_min)

        tk_cropped_image = convert_image_to_tkinter(cropped_image, cropped_image.shape[0] * 2,
                                                    cropped_image.shape[1] * 2)
        tk_character_image = convert_image_to_tkinter(character_image, target_height, target_width)

        update_labels(row, unsure_text_var, character_image_label, tk_character_image, cropped_image_label,
                      tk_cropped_image, serial_var, file_name_var, progress_var, unsure_var, current_index,
                      corrected_df)

        resize_window(tk_cropped_image, tk_character_image, root)

        return

    def resize_window(image_pil, character_image_pil, root):
        """
        Resizes the application window based on the current image dimensions.

        Args:
            image_pil (ImageTk.PhotoImage): PIL image of the cropped image.
            character_image_pil (ImageTk.PhotoImage): PIL image of the character overlay.
            root (Tk): Root Tkinter window.
        """
        total_height = image_pil.height() + character_image_pil.height() + 125
        total_width = int(character_image_pil.width() * 1.35)
        root.geometry(f"{total_width}x{total_height}")  # Add some extra height for buttons
        center_window()  # Center the window after updating the display

    def center_window():
        """Centers the main application window on the screen."""
        root.update_idletasks()  # Ensures all widget sizes are computed
        window_width = root.winfo_width()
        window_height = root.winfo_height()
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x_cordinate = int((screen_width / 2) - (window_width / 2))
        y_cordinate = int((screen_height / 2) - (window_height / 2))
        root.geometry(f"{window_width}x{window_height}+{x_cordinate}+{y_cordinate}")

    def on_serial_change(*args):
        """Enables or disables the sure/unsure buttons based on serial number length."""
        sure_button.config(state="normal" if len(serial_var.get()) == 11 else "disabled")
        unsure_button.config(state="normal" if len(serial_var.get()) == 11 else "disabled")

    def next_image():
        """
        Advances to the next image, saving any edits made to the serial number field.
        Ends the program if the last image is reached.
        """
        nonlocal current_index
        corrected_df.at[current_index, 'serial_number'] = serial_var.get()
        current_index += 1
        if current_index < len(corrected_df):
            update_image_display(current_index)
        else:
            save_data(corrected_df, df, output_file_path, input_file_path)
            root.quit()
            root.destroy()

    def on_sure():
        """Marks the current image as 'Sure' and moves to the next image."""
        corrected_df.at[current_index, 'unsure'] = float(0)
        next_image()

    def on_unsure():
        """Toggles the unsure status for the current image and updates UI accordingly."""
        if unsure_var.get() == "Unsure":
            unsure_var.set("Still Unsure")
            draw_filtered_images(cropped_image_label, character_image_label)
        else:
            corrected_df.at[current_index, 'unsure'] = float(1)
            next_image()

    def on_quit():
        """Saves the current data and exits the application."""
        save_data(df, corrected_df, output_file_path, input_file_path)
        root.destroy()

    def update_colour(*args):
        """Changes the color of the unsure label based on its text content."""
        text = unsure_text_var.get()
        if text.lower() == "the accuracy of this image has been labeled as unsure.":
            unsure_label.config(fg="red")
        elif text.lower() == "the accuracy of this image has been labeled as sure.":
            unsure_label.config(fg="green")
        else:
            unsure_label.config(fg="black")

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
    unsure_var = StringVar()

    unsure_text_var = StringVar()
    unsure_text_var.trace_add("write", update_colour)

    unsure_label = Label(title_frame, textvariable=unsure_text_var)
    unsure_label.grid(row=5, column=10, padx=10, pady=10)

    buttons_frame = Frame(image_and_buttons_frame)
    buttons_frame.grid(row=10, column=20, padx=10, pady=10)

    # Frame for index and navigation
    navigation_frame = Frame(buttons_frame)
    navigation_frame.grid(row=5, column=10, padx=10, pady=10)

    # Editable index entry
    index_entry = Entry(navigation_frame, width=5, justify='center')
    index_entry.insert(0, str(current_index + 1))
    index_entry.pack(side="left")

    # Label showing the total number of files
    total_label = Label(navigation_frame, text=f"/{len(corrected_df)}")
    total_label.pack(side="left")

    # Button to navigate to the specified index
    go_button = Button(navigation_frame, text="Go", command=go_to_index)
    go_button.pack(side="left")

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
    unsure_button = Button(sure_unsure_frame, textvariable=unsure_var, command=on_unsure,
                           state="disabled")  # Initially disabled
    unsure_button.grid(row=30, column=11, padx=10, pady=10)  # Edit button in the right column
    quit_button = Button(buttons_frame, text="Save and Exit", command=on_quit)
    quit_button.grid(row=40, column=10, padx=10, pady=10)  # Quit button in the right column

    # Set up trace for real-time validation of serial number length
    serial_var.trace_add("write", on_serial_change)

    # Initialize display with the first image and serial number
    update_image_display(current_index)
    center_window()  # Center the window after initializing

    root.mainloop()
