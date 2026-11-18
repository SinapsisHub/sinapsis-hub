# -*- coding: utf-8 -*-
import argparse
import math
from typing import Any, Tuple

import cv2
import numpy as np
from sinapsis.logging import sinapsis_logger


def args_parser() -> argparse.Namespace:
    """
    Arg parser for the Sinapsis Diarization CLI.
    """
    cli_parser = argparse.ArgumentParser(description="Sinapsis Fast ALPR Coordinates")

    cli_parser.add_argument("video", type=str, help="Path to image", metavar="VIDEO_PATH")
    return cli_parser.parse_args()


def sort_source_points(points: list[list[int]]) -> list[list[int]]:
    """Sort the points of a quadrilateral from top left -> top right
    -> bottom right -> bottom left

    Args:
        points (list[list[int]]): unsorted quadrilateral points

    Returns:
        list[list[int]]: sorted quadrilateral points
    """
    sorted_points = sorted(points, key=lambda pts: pts[1])
    tops = sorted_points[:2]
    bottoms = sorted_points[2:]
    sorted_tops = sorted(tops, key=lambda pts: pts[0])
    sorted_bottoms = sorted(bottoms, key=lambda pts: pts[0])
    return [sorted_tops[0], sorted_tops[1], sorted_bottoms[1], sorted_bottoms[0]]


def calculate_ratio(point_one: Tuple[int, int], point_two: Tuple[int, int], distance: int) -> float:
    """Calculate the meters per pixel based on two points and meter distance

    Args:
        point_one (list[int]): first point coordinates
        point_two (list[int]): second point coordinates
        distance (int): _description_

    Returns:
        float: _description_
    """
    pixel_distance = math.sqrt(math.pow(point_one[0] - point_two[0], 2) + math.pow(point_one[1] - point_two[1], 2))
    ratio = distance / pixel_distance
    return ratio


key_digit = {
    ord("0"): 0,
    ord("1"): 1,
    ord("2"): 2,
    ord("3"): 3,
    ord("4"): 4,
    ord("5"): 5,
    ord("6"): 6,
    ord("7"): 7,
    ord("8"): 8,
    ord("9"): 9,
}


def check_key_digits(key: int) -> int:
    """Return the digit number for a key input from keyboard

    Args:
        key (int): key received

    Returns:
        int: digit
    """
    if key in key_digit:
        num = key_digit[key]
        return num
    return -1


def midpoint(point_one: list[int], point_two: list[int]) -> Tuple[int, int]:
    """Calculate the middle point between two points in coordinates

    Args:
        point_one (list[int]): first point coordinates
        point_two (list[int]): second point coordinates

    Returns:
        Tuple[int, int]: coordinates of the middle point
    """
    x = int((point_one[0] + point_two[0]) / 2)
    y = int((point_one[1] + point_two[1]) / 2)
    return (x, y)


def draw_text(
    img: np.ndarray,
    text: str,
    font: int = cv2.FONT_HERSHEY_SIMPLEX,
    pos: Tuple[int, int] = (0, 0),
    font_scale: int = 1,
    font_thickness: int = 2,
    text_color: Tuple[int, int, int] = (0, 0, 255),
    text_color_bg: Tuple[int, int, int] = (0, 0, 0),
) -> None:
    """Draw text with background on an image

    Args:
        img (np.ndarray): image
        text (str): text to draw
        font (int, optional): Font type. Defaults to cv2.FONT_HERSHEY_SIMPLEX.
        pos (Tuple[int, int], optional): Position of the text (x, y). Defaults to (0, 0).
        font_scale (int, optional): Scale of the font. Defaults to 1.
        font_thickness (int, optional): Thickness of the font. Defaults to 2.
        text_color (Tuple[int, int, int], optional):
            Color of the font in BGR. Defaults to (0, 0, 255).
        text_color_bg (Tuple[int, int, int], optional):
            Color of the background in BGR _description_. Defaults to (0, 0, 0).

    Returns:
        _type_: _description_
    """
    x, y = pos
    text_size, _ = cv2.getTextSize(text, font, font_scale, font_thickness)
    text_w, text_h = text_size
    cv2.rectangle(img, pos, (x + text_w, y + text_h), text_color_bg, -1)
    cv2.putText(img, text, (x, y + text_h + font_scale - 1), font, font_scale, text_color, font_thickness)


def draw_quadrilateral(image: np.ndarray, points: list[list[int]]) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    """Draw a quadrilateral based on 4 points of input and draw the middle line from top to bottom

    Args:
        image (np.ndarray): image
        points (list[list[int]]): points of the quadrilateral

    Returns:
        Tuple[Tuple[int, int], Tuple[int, int]]: coordinates of the top center and bottom center points
    """
    cv2.line(image, points[0], points[1], (0, 0, 255), 3)
    cv2.line(image, points[1], points[2], (0, 0, 255), 3)
    cv2.line(image, points[2], points[3], (0, 0, 255), 3)
    cv2.line(image, points[3], points[0], (0, 0, 255), 3)
    center_top = midpoint(points[0], points[1])
    center_bottom = midpoint(points[2], points[3])
    cv2.line(image, center_top, center_bottom, (0, 0, 255), 5)
    return center_top, center_bottom


def process_digit(
    input_digit: int, first_num: int, second_num: int, image: np.ndarray, dist: int
) -> Tuple[int, int, int]:
    """Get the digit represented by a keyboard input and return the distance represented by
    the digits.

    Args:
        input_digit (int): key that was received
        first_num (int): first digit
        second_num (int): second digit
        image (np.ndarray): image
        dist (int): distance of

    Returns:
        Tuple[int, int, int]: _description_
    """
    if input_digit >= 0:
        if first_num < 0:
            first_num = input_digit
            draw_text(image, str(first_num), pos=(40, 120))
            dist = first_num
        elif second_num < 0:
            second_num = input_digit
            draw_text(image, str(second_num), pos=(60, 120))
            dist = first_num * 10 + second_num
        cv2.imshow("Point Picker", image)

    return dist, first_num, second_num


def main():
    """Receives 4 points on an image and one or two digits for the distance of the middle line.
    Returns the meters per pixel and the cooordinates for the points."""
    source_points = []
    sorted_points = []
    center_top = []
    center_bottom = []
    first = -1
    second = -1
    distance = -1

    def click_event(event, x, y, flags: Any, params: Any):
        _ = flags
        _ = params
        if event == cv2.EVENT_LBUTTONDOWN and len(source_points) < 4:
            source_points.append([x, y])
            cv2.circle(img, center=(x, y), radius=5, color=(0, 0, 255), thickness=-1)
            cv2.imshow("Point Picker", img)
            sinapsis_logger.info(f"Point added: {x}, {y}")

    args = args_parser()
    cap = cv2.VideoCapture(args.video)
    _, img = cap.read()
    cap.release()
    draw_text(img, "Click 4 points on the road (forming a quadrilateral)", pos=(40, 40))
    cv2.imshow("Point Picker", img)
    cv2.setMouseCallback("Point Picker", click_event)
    center_top: Tuple[int, int] = (0, 0)
    center_bottom: Tuple[int, int] = (0, 0)
    while True:
        if len(source_points) == 4 and not sorted_points:
            sorted_points.extend(sort_source_points(source_points))
            center_top, center_bottom = draw_quadrilateral(img, sorted_points)
            draw_text(
                img,
                "Input the distance in meters corresponding to the center line, then press Enter, q or Esc:",
                pos=(40, 80),
            )
            cv2.imshow("Point Picker", img)

        key = cv2.waitKey(1) & 0xFF
        digit = check_key_digits(key)
        distance, first, second = process_digit(digit, first, second, img, distance)

        if key == 27 or key == ord("q") or key == 13:
            sinapsis_logger.info(f"Distance entered: {distance} meters")
            print(f"source_points: {sorted_points}")  # noqa: T201
            print(f"Meters per pixel: {calculate_ratio(center_top, center_bottom, distance)}")  # noqa: T201
            cv2.destroyAllWindows()
            break
