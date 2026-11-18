# -*- coding: utf-8 -*-
import argparse
import math
from typing import Any

import cv2


def args_parser() -> argparse.Namespace:
    cli_parser = argparse.ArgumentParser(description="Sinapsis Fast ALPR Coordinates")

    cli_parser.add_argument("video", type=str, help="Path to image", metavar="VIDEO_PATH")
    return cli_parser.parse_args()


def calculate_ratio(points: list[list[int]]) -> float:
    dist = math.sqrt(math.pow(points[0][0] - points[1][0], 2) + math.pow(points[0][1] - points[1][1], 2))
    return 1 / dist


def main():
    points = []

    def click_event(event, x, y, flags: Any, params: Any):
        _ = flags
        _ = params
        if event == cv2.EVENT_LBUTTONDOWN and len(points) < 2:
            points.append([x, y])
            cv2.circle(img, center=(x, y), radius=5, color=(0, 0, 255), thickness=-1)
            cv2.imshow("Meters Per Pixel", img)
            print(f"Point added: {x}, {y}")  # noqa: T201
        if len(points) == 2:
            meters_per_pixel = calculate_ratio(points)
            print(f"meters_per_pixel: {meters_per_pixel}")  # noqa: T201
            cv2.destroyAllWindows()

    args = args_parser()
    cap = cv2.VideoCapture(args.video)
    _, img = cap.read()
    cap.release()
    print("Click 2 points on the road that represent a meter and press 'q'.")  # noqa: T201
    cv2.imshow("Meters Per Pixel", img)
    cv2.setMouseCallback("Meters Per Pixel", click_event)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
