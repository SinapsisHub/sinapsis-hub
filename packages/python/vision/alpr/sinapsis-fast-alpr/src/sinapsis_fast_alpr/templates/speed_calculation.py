# -*- coding: utf-8 -*-

from collections import defaultdict, deque

from sinapsis.data_transport import DataContainer, OrientedBoundingBox
from sinapsis.template import Template, TemplateAttributes, TemplateAttributeType

OVER = "Over limit"


class ObjectSpeedCalculationTemplateAttributes(TemplateAttributes):
    """
    fps (int): frames per second of the video
    meters_per_pixel (float): value of approximate meters per pixel in the image
    speed_limit (int): speed limit to set for identifying detections going over
    """

    fps: int
    meters_per_pixel: float
    speed_limit: int


class ObjectSpeedCalculation(Template):
    """Template that takes oriented bounding boxes of detections and approximates a speed based on
    the attributes

    Example agent:

    agent:
        name: my_test_agent
    templates:
    - template_name: InputTemplate
    class_name: InputTemplate
    attributes: {}
    - template_name: ObjectSpeedCalculation
    class_name: ObjectSpeedCalculation
    template_input: InputTemplate
    attributes:
        fps: '`replace_me:<class ''int''>`'
        meters_per_pixel: '`replace_me:<class ''float''>`'
        speed_limit: '`replace_me:<class ''int''>`'

    """

    AttributesBaseModel = ObjectSpeedCalculationTemplateAttributes
    attributes: ObjectSpeedCalculationTemplateAttributes

    def __init__(self, attributes: TemplateAttributeType) -> None:
        super().__init__(attributes)
        self.coords: dict[int, deque] = defaultdict(lambda: deque(maxlen=self.attributes.fps))
        self.raw_speeds: dict[int, deque] = defaultdict(lambda: deque(maxlen=self.attributes.fps))
        self.over_limit: dict[int, bool] = defaultdict(bool)

    @staticmethod
    def get_anchor_coordinate(bbox: OrientedBoundingBox) -> int:
        """Get the center bottom y-coordinate of a detection

        Args:
            bbox (OrientedBoundingBox): oriented bounding box model

        Returns:
            int: y- coordinate of the bottom center of detection
        """
        return int((bbox.y3 + bbox.y4) / 2)

    def calculate_raw_speed(self, tracker_id: int) -> None:
        """Calculate the raw speed of a detection based on the coordinates and video characteristics

        Args:
            tracker_id (int): tracker ID of the detection
        """
        if len(self.coords[tracker_id]) >= self.attributes.fps // 2:
            dist_px = abs(self.coords[tracker_id][-1] - self.coords[tracker_id][0])
            self.raw_speeds[tracker_id].append(
                (dist_px * self.attributes.meters_per_pixel)
                / (len(self.coords[tracker_id]) / self.attributes.fps)
                * 3.6
            )

    def calculate_smoothed_speed(self, tracker_id: int) -> float:
        """Smooths the raw speed between frames

        Args:
            tracker_id (int): tracker ID of the detection

        Returns:
            float: smoothed speed
        """
        speed = 0.0
        if self.raw_speeds[tracker_id]:
            speed = sum(self.raw_speeds[tracker_id]) / len(self.raw_speeds[tracker_id])
            if speed > self.attributes.speed_limit:
                self.over_limit[tracker_id] = True
        return speed

    def execute(self, container: DataContainer) -> DataContainer:
        """Calculates speed of transformed detections

        Args:
            container (DataContainer): data container

        Returns:
            DataContainer: data container
        """
        for image_packet in container.images:
            for annotation in image_packet.annotations:
                extra_labels = annotation.extra_labels if annotation.extra_labels else {}
                if annotation.oriented_bbox is not None:
                    tracker_id = int(extra_labels.get("ID", -1))
                    self.coords[tracker_id].append(self.get_anchor_coordinate(annotation.oriented_bbox))

                    self.calculate_raw_speed(tracker_id)
                    speed = int(self.calculate_smoothed_speed(tracker_id))
                    extra_labels["Speed(km/h)"] = speed
                    if tracker_id in self.over_limit:
                        extra_labels[OVER] = speed
        return container
