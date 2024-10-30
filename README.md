
# Image Annotation Tool

This project is an annotation and validation tool for labeling images and storing positional data. The application provides a GUI to validate, adjust, and save annotated data for images in a specified directory. It includes features for applying filters to images to make characters more visible, saving progress, and managing files to streamline the annotation process.

## Project Structure

```plaintext
.
├── .venv                    # Virtual environment for dependencies
├── data
│   ├── images               # Folder for all images to be annotated
│   └── to_label             # Folder containing Excel files with data for annotation
│       ├── serial_numbers.xlsx
│       ├── serial_numbers_test.xlsx
│       └── updated_serial_numbers_<timestamp>.xlsx  # Saved annotated data
├── utils                    # Utility scripts for UI, file handling, and image processing
│   ├── __init__.py
│   ├── file_handling.py
│   ├── image_processing.py
│   ├── tkinter_ui.py
│   └── ui_helpers.py
├── .gitignore
├── annotate_helper.ipynb    # Jupyter notebook for initial processing
├── config.yaml              # Configuration file with file paths and GUI settings
├── main.py                  # Main script to launch the annotation UI
├── README.md                # Documentation file (this file)
└── requirements.txt         # Python dependencies for the project
```

## Setup and Installation

1. **Environment Setup**:
   - Make sure you have Python installed.
   - Create a virtual environment (recommended):
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate  # On Windows: .venv\Scripts\activate
     ```
   
2. **Install Dependencies**:
   - Install required packages listed in `requirements.txt`:
     ```bash
     pip install -r requirements.txt
     ```
   
3. **Configuration**:
   - Check `config.yaml` for paths and settings:
     - `data_dir`: Directory for input/output data files.
     - `images_dir`: Directory containing images.
     - `input_file`: Name of the Excel file with initial data.
     - `output_file_prefix`: Prefix for the output file name, appended with a timestamp.
     - GUI and cropping parameters (optional): Customize window size and padding.

## Usage

### Step 1: Prepare Files for Annotation

- Place images that need annotation in the `data/images` directory.
- Ensure the annotation file (`serial_numbers.xlsx`) is in `data/to_label`. This file should contain data fields like `C1`, `C11`, and `serial_number` required for annotation.
- If you need to preprocess data, open and run the `annotate_helper.ipynb` notebook. This will synchronize the latest annotated data with the `serial_numbers.xlsx` file. This step is optional and mostly required only while data is incomplete.

### Step 2: Launch the Annotation Tool

1. **Run the main program**:
   ```bash
   python main.py
   ```
   This will open a GUI window that displays each image along with its annotations.

2. **Using the Interface**:
   - **Navigate through images**: Each image is displayed one by one with options to review or modify annotations.
   - **Validation**:
     - Click **"Sure"** if the annotation is correct.
     - Click **"Unsure"** if the data is uncertain. This opens two filtered views of the image to help validate character positions. If still unsure, clicking **"Still Unsure"** will log the entry as uncertain.
   - **Modify Annotations**: Adjust character positions if needed and then click **"Sure"** or **"Unsure"**.
   - **Save Progress**:
     - Click **"Save and Quit"** to save progress and exit without finishing all images.
     - **Skipping to File**: You can jump to a specific image number by entering the number in the provided field. This allows you to resume progress easily.

### Step 3: Saving Data

- Once you’ve validated all images, the tool will save the annotated data in a new file in `data/to_label/`. The filename follows the pattern: `updated_serial_numbers_<timestamp>.xlsx`.
- **Overwrite and Backup**:
  - If you re-run the tool, it will save updates to the original file (`serial_numbers.xlsx`) while creating a timestamped backup of previous data, ensuring no data loss.

## Notes and Limitations

- **GUI Compatibility**: The dimensions of the GUI window may vary by device. If the window does not display correctly on your screen, you may need to adjust window dimensions in `config.yaml`.
- **Incomplete Annotation**: If the tool is run multiple times before all images are annotated, ensure to use the `annotate_helper.ipynb` notebook to keep data synchronized.
- **Config File**: Adjust settings in `config.yaml` as per your needs. This file contains paths, window dimensions, and padding values that affect image display and cropping.

## Dependencies

- **Python Libraries** (from `requirements.txt`):
  - `opencv-python`: Image processing library for rotations and filters.
  - `pandas`: Data manipulation library for handling annotation data.
  - `Pillow`: Image handling library, especially for GUI compatibility with Tkinter.
  - `xlsxwriter`: Library to manage Excel files.
  - `pyyaml`: For reading and writing YAML configuration files.
