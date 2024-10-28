import os
from datetime import datetime


def save_data(old_df, new_df, output_file_path, input_file_path):
    # Copy the input file into output file path with timestamp
    final_new_file_path = input_file_path
    new_df['serial_number'] = new_df['serial_number'].astype(str).replace('nan', '')
    new_df.to_excel(final_new_file_path, index=False)
    # Replace input file with output file
    final_old_file_path = f"{output_file_path}_{datetime.now().strftime('%d-%m_%Hh_%Mm_%Ss')}.xlsx"
    old_df.to_excel(final_old_file_path, index=False)
    print("Corrected data saved.")
