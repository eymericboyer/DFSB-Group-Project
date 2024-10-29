import cv2
import numpy as np
import pandas as pd


def rotate_image(image, angle, center):
    (h, w) = image.shape[:2]
    rot_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(image, rot_matrix, (w, h))


def calculate_window(row, h_pad, v_pad, image_shape):
    if pd.isna(row["C1"]) or pd.isna(row["C11"]):
        return None

    c1, c11 = eval(row["C1"].replace(";", ",")), eval(row["C11"].replace(";", ","))
    angle = np.degrees(np.arctan2(c11[1] - c1[1], c11[0] - c1[0]))
    image_center = (image_shape[1] // 2, image_shape[0] // 2)

    def rotate_point(point, angle, center):
        rot_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        return np.dot(rot_matrix, np.array([point[0], point[1], 1]))

    rotated_c1, rotated_c11 = rotate_point(c1, angle, image_center), rotate_point(c11, angle, image_center)
    x_min = int(rotated_c1[0] - h_pad)
    x_max = int(rotated_c11[0] + h_pad)
    y_min = int(rotated_c1[1] - v_pad)
    y_max = int(rotated_c1[1] + v_pad)

    return x_min, x_max, y_min, y_max, angle
