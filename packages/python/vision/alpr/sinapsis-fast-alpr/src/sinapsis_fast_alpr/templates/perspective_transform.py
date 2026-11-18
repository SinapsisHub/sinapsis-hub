# -*- coding: utf-8 -*-
import cv2
import numpy as np
from sinapsis.data_transport import BoundingBox, DataContainer, ImageAnnotations, OrientedBoundingBox
from sinapsis.template import Template, TemplateAttributes, TemplateAttributeType


class DetectionPerspectiveTransformAttributes(TemplateAttributes):
    """
    source_points (list(list(int))): quadrilateral that represents the main points of the road in the image
    filter_detections_roi (bool): True to keep only detection near the source points area
    """

    source_points: list[list[int]]
    filter_detections_roi: bool = True


class DetectionPerspectiveTransform(Template):
    """Template to receive the points of the road and transform the bbox coordinates using cv2 PerspectiveTransform

    Example agent:

    agent:
        name: my_test_agent
    templates:
    - template_name: InputTemplate
    class_name: InputTemplate
    attributes: {}
    - template_name: DetectionPerspectiveTransform
    class_name: DetectionPerspectiveTransform
    template_input: InputTemplate
    attributes:
        source_points: '`replace_me:list[list[int]]`'
        filter_detections_roi: true

    """

    AttributesBaseModel = DetectionPerspectiveTransformAttributes
    attributes: DetectionPerspectiveTransformAttributes

    def __init__(self, attributes: TemplateAttributeType) -> None:
        super().__init__(attributes)
        source_points_np = np.asarray(self.attributes.source_points, dtype=np.float32)
        target_points_np = np.asarray(self.get_target_points(self.attributes.source_points), dtype=np.float32)
        self.matrix = cv2.getPerspectiveTransform(source_points_np, target_points_np)

    @staticmethod
    def get_anchor_coordinates(bbox: BoundingBox) -> np.ndarray:
        """Transform the bbox base model into coordinates for the square's points

        Args:
            bbox (BoundingBox): bounding box base model

        Returns:
            list[list[str]]: bounding box points
        """
        return np.asarray(
            [
                [
                    [bbox.x, bbox.y],
                    [bbox.x + bbox.w, bbox.y],
                    [bbox.x + bbox.w, bbox.y + bbox.h],
                    [bbox.x, bbox.y + bbox.h],
                ]
            ]
        )

    @staticmethod
    def get_oriented_bbox(points: np.ndarray) -> OrientedBoundingBox:
        """Transforms points into an OrientedBoundingBox base model

        Args:
            points (np.ndarray): input points

        Returns:
            OrientedBoundingBox: base model for oriented bbox
        """
        return OrientedBoundingBox(
            x1=points[0][0],
            y1=points[0][1],
            x2=points[1][0],
            y2=points[1][1],
            x3=points[2][0],
            y3=points[2][1],
            x4=points[3][0],
            y4=points[3][1],
        )

    def check_annotation(self, annotation: ImageAnnotations) -> bool:
        """Check if the detection's bounding box is in the area of interest

        Args:
            annotation (ImageAnnotations): image annotations

        Returns:
            bool: True if the detection is in Region of Interest
        """
        MARGIN = 0.1
        margin_x = abs(self.attributes.source_points[0][0] - self.attributes.source_points[1][0]) * MARGIN
        margin_y = abs(self.attributes.source_points[0][1] - self.attributes.source_points[2][1]) * MARGIN
        if annotation.bbox is not None:
            if not self.attributes.filter_detections_roi:
                return True
            center = [annotation.bbox.x + annotation.bbox.w / 2, annotation.bbox.y + annotation.bbox.h / 2]

            if (
                self.attributes.source_points[0][0] - margin_x
                <= center[0]
                <= self.attributes.source_points[1][0] + margin_x
                and self.attributes.source_points[0][1] - margin_y
                <= center[1]
                <= self.attributes.source_points[2][1] + margin_y
            ):
                return True
        return False

    @staticmethod
    def get_target_points(points: list[list[int]]) -> list[list[int]]:
        """Get the square that encloses a given quadrilateral

        Args:
            points (list[list[int]]): source quadrilateral

        Returns:
            list[list[int]]: target points
        """
        x1 = min(points[0][0], points[3][0])
        y1 = min(points[0][1], points[1][1])
        x2 = min(points[1][0], points[2][0])
        y2 = min(points[2][1], points[3][1])
        return [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]

    def execute(self, container: DataContainer) -> DataContainer:
        """Runs perspective transform on detections and filters detections if attribute is true

        Args:
            container (DataContainer): data container

        Returns:
            DataContainer: data container
        """
        for image_packet in container.images:
            annotations: list[ImageAnnotations] = []
            for annotation in image_packet.annotations:
                add_to_annotations = self.check_annotation(annotation)
                if add_to_annotations and annotation.bbox is not None:
                    anchors = self.get_anchor_coordinates(annotation.bbox)
                    transformed_pts = cv2.perspectiveTransform(anchors, self.matrix)
                    annotation.oriented_bbox = self.get_oriented_bbox(transformed_pts[0])
                    annotations.append(annotation)
            if self.attributes.filter_detections_roi:
                image_packet.annotations = annotations

        return container
