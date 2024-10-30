import os
import pandas as pd
import yaml
from utils.tkinter_ui import initialize_ui

# Load configuration
with open("config.yaml", "r") as config_file:
    config = yaml.safe_load(config_file)

# Paths from config
data_dir = config['paths']['data_dir']
images_dir = config['paths']['images_dir']
input_file_path = os.path.join(data_dir, config['paths']['input_file'])
output_file_path = os.path.join(data_dir, config['paths']['output_file_prefix'])


def main():
    """
    Main function to load data, set up paths, and initialize the Tkinter UI.

    This function performs the following steps:
    - Loads an Excel file specified in the configuration as a DataFrame.
    - Creates a copy of the DataFrame to track any corrections made in the UI.
    - Converts the `serial_number` column to string format to ensure consistency.
    - Launches the UI for reviewing and editing data.

    Args:
        None

    Returns:
        None
    """
    # Load the input Excel file
    df = pd.read_excel(input_file_path)
    corrected_df = df.copy()
    corrected_df['serial_number'] = corrected_df['serial_number'].astype(str)

    # Initialize the UI
    initialize_ui(corrected_df, df, images_dir, output_file_path, input_file_path)


if __name__ == "__main__":
    main()
