# Image Review and Annotation Tool

This project provides a GUI to review and update serial numbers associated with images and an annotation helper for marking digit positions within images.

## Features

- **Image Review and Update**: A Tkinter interface displays images one by one for reviewing and updating serial numbers.
- **Annotation Helper**: A Jupyter notebook lets you label images by clicking on the position of each digit in a serial number before entering the serial number.
- **Data Export**: Saves updated serial numbers and digit coordinates to a timestamped Excel file or CSV.

## Setup

1. **Requirements**:
   - Python 3.6+
   - `opencv-python`, `pandas`, `Pillow`, `xlsxwriter`, `tkinter`
   - Install with:
     ```bash
     pip install opencv-python pandas pillow xlsxwriter
     ```

2. **Project Structure**:
   - `main.py`: Run this to start the Tkinter GUI for serial number review.
   - `utils/`: Contains helper functions for file handling, image processing, and UI.
   - `annotate_helper.ipynb`: Jupyter notebook for marking digit positions in images.

3. **Running the App**:
   - **Review Tool**: Run `python main.py`. Use "Agree" or "Edit" to review serial numbers.
   - **Annotation Helper**: Run cells in `annotate_helper.ipynb` to capture coordinates for each image.

## Example Data Format

- **Excel File**: `serial_number`, `image`, `C1` to `C11`
- **CSV Output**: `image`, `serial_number`, `C1` to `C11` for digit coordinates
