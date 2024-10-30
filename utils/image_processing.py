import cv2
import numpy as np
import pandas as pd


def rotate_image(image, angle, center):
    """
    Rotates an image around a specified center point by a given angle.

    Args:
        image (ndarray): The original image to be rotated.
        angle (float): The angle (in degrees) by which to rotate the image.
        center (tuple): A tuple (x, y) representing the center of rotation.

    Returns:
        ndarray: The rotated image with the same dimensions as the input.
    """
    (h, w) = image.shape[:2]
    rot_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(image, rot_matrix, (w, h))


def calculate_window(row, h_pad, v_pad, image_shape):
    """
    Calculates a bounding box window around points `C1` and `C11` in the image and determines the rotation angle.

    Args:
        row (pd.Series): Data row containing 'C1' and 'C11' as points for calculating angle and bounding box.
        h_pad (int): Horizontal padding to apply on either side of the bounding box.
        v_pad (int): Vertical padding to apply on top and bottom of the bounding box.
        image_shape (tuple): Shape of the image as (height, width) used for centering rotation.

    Returns:
        tuple or None: Contains:
            - x_min (int): Minimum x-bound of the bounding box with padding.
            - x_max (int): Maximum x-bound of the bounding box with padding.
            - y_min (int): Minimum y-bound of the bounding box with padding.
            - y_max (int): Maximum y-bound of the bounding box with padding.
            - angle (float): Calculated rotation angle in degrees.
        Returns `None` if `C1` or `C11` data is missing.
    """
    if pd.isna(row["C1"]) or pd.isna(row["C11"]):
        return None

    c1, c11 = eval(row["C1"].replace(";", ",")), eval(row["C11"].replace(";", ","))
    angle = np.degrees(np.arctan2(c11[1] - c1[1], c11[0] - c1[0]))
    image_center = (image_shape[1] // 2, image_shape[0] // 2)

    def rotate_point(point, angle, center):
        """
        Rotates a point around a specified center by a given angle.

        Args:
            point (tuple): Coordinates of the point to rotate.
            angle (float): Angle in degrees for rotation.
            center (tuple): Center point for rotation.

        Returns:
            ndarray: Transformed coordinates after rotation.
        """
        rot_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        return np.dot(rot_matrix, np.array([point[0], point[1], 1]))

    rotated_c1, rotated_c11 = rotate_point(c1, angle, image_center), rotate_point(c11, angle, image_center)
    x_min = int(rotated_c1[0] - h_pad)
    x_max = int(rotated_c11[0] + h_pad)
    y_min = int(rotated_c1[1] - v_pad)
    y_max = int(rotated_c11[1] + v_pad)

    return x_min, x_max, y_min, y_max, angle
