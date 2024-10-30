import os
from datetime import datetime


def save_data(old_df, new_df, output_file_path, input_file_path):
    """
    Saves the modified data by overwriting the input file with updated data and creating a timestamped backup of the old data.

    Args:
        old_df (pd.DataFrame): Original DataFrame containing the data prior to modifications.
        new_df (pd.DataFrame): Modified DataFrame with updates.
        output_file_path (str): Directory path and prefix for saving the backup file of the old data.
        input_file_path (str): File path for overwriting the original data with the updated data.

    Returns:
        None
    """
    # Copy the input file into output file path with timestamp
    final_new_file_path = input_file_path
    new_df['serial_number'] = new_df['serial_number'].astype(str).replace('nan', '')
    new_df.to_excel(final_new_file_path, index=False)
    # Replace input file with output file
    final_old_file_path = f"{output_file_path}_{datetime.now().strftime('%d-%m_%Hh_%Mm_%Ss')}.xlsx"
    old_df.to_excel(final_old_file_path, index=False)
    print("Corrected data saved.")
