# -*- coding: utf-8 -*-
from collections import defaultdict
from dataclasses import dataclass
from typing import Literal

import numpy as np
from fast_alpr import ALPR
from sinapsis.data_transport import DataContainer, ImageAnnotations
from sinapsis.template import Template, TemplateAttributes, TemplateAttributeType

LICENSE_STR = "License"


DETECTOR_MODELS = Literal[
    "yolo-v9-s-608-license-plate-end2end",
    "yolo-v9-t-640-license-plate-end2end",
    "yolo-v9-t-512-license-plate-end2end",
    "yolo-v9-t-416-license-plate-end2end",
    "yolo-v9-t-384-license-plate-end2end",
    "yolo-v9-t-256-license-plate-end2end",
]

OCR_MODELS = Literal[
    "cct-s-v2-global-model", "cct-xs-v2-global-model", "cct-s-v1-global-model", "cct-xs-v1-global-model"
]


@dataclass
class LicensePlate:
    """License plate base model"""

    plate: str
    confidence: float


class FastALPRTemplateAttributes(TemplateAttributes):
    """
    detector_model (str): license plate detector model name for fast-alpr
    ocr_model (str): ocr_model name for fast-alpr
    detection_threshold (float): threshold for detection scores
    ocr_threshold (float): threshold for ocr scores
    alpr_y_threshold (float): threshold for starting license plate recognition where 0.0 represents top of the image
     and 1.0, the bottom
    """

    detector_model: DETECTOR_MODELS = "yolo-v9-s-608-license-plate-end2end"
    ocr_model: OCR_MODELS = "cct-xs-v1-global-model"
    detection_threshold: float = 0.5
    ocr_threshold: float = 0.5
    alpr_y_threshold: float = 0.7


class FastALPR(Template):
    """Template to run automatic license plate recognition with Fast ALPR and save the best prediction

    Example agent:

    agent:
      name: my_test_agent
    templates:
    - template_name: InputTemplate
    class_name: InputTemplate
    attributes: {}
    - template_name: FastALPR
    class_name: FastALPR
    template_input: InputTemplate
    attributes:
        detector_model: yolo-v9-s-608-license-plate-end2end
        ocr_model: cct-xs-v1-global-model
        detection_threshold: 0.5
        ocr_threshold: 0.5
        alpr_y_threshold: 0.7
    """

    AttributesBaseModel = FastALPRTemplateAttributes
    attributes: FastALPRTemplateAttributes

    def __init__(self, attributes: TemplateAttributeType):
        super().__init__(attributes)
        self.model = self._init_model()
        self.plates: dict[int, list[LicensePlate]] = defaultdict()

    def _init_model(self):
        """Initialize model"""
        model = ALPR(detector_model=self.attributes.detector_model, ocr_model=self.attributes.ocr_model)
        return model

    def check_conditions(self, image: np.ndarray, annotation: ImageAnnotations) -> bool:
        """Check for the detection's conditions before running ALPR

        Args:
            image (np.ndarray): image array
            annotation (ImageAnnotations): image's annotations

        Returns:
            bool: whether to run alpr on the detection
        """
        if annotation.bbox is not None and annotation.text is None:
            height = image.shape[0]
            y_norm = (annotation.bbox.y + annotation.bbox.h) / height
            return y_norm >= self.attributes.alpr_y_threshold
        return False

    def get_best_plate(self, tracker_id: int) -> str:
        """Get the best plate based on predictions across frames, based on count first, confidence
        second

        Args:
            tracker_id (int): ID of the tracked detection

        Returns:
            str: best plate predicted
        """
        plate_instances: dict[str, int] = defaultdict(int)
        confidences: dict[str, float] = defaultdict(float)
        for plate in self.plates[tracker_id]:
            if plate.plate not in plate_instances:
                plate_instances[plate.plate] = 1
                confidences[plate.plate] = plate.confidence
            else:
                plate_instances[plate.plate] += 1
                confidences[plate.plate] = confidences[plate.plate] + plate.confidence
        maxim = 0
        best_plate = ""
        for plate_key, num in plate_instances.items():
            if num > maxim:
                maxim = num
                best_plate = plate_key
        repeats: list[str] = []
        max_confs: list[float] = []
        for plate_key, num in plate_instances.items():
            if num == maxim:
                repeats.append(plate_key)
                max_confs.append(confidences[plate_key])
        if repeats:
            i = 0
            maxim_conf = 0.0
            for idx, conf in enumerate(max_confs):
                if conf > maxim_conf:
                    maxim_conf = conf
                    i = idx
            if maxim_conf > confidences[best_plate]:
                best_plate = repeats[i]

        return best_plate

    def add_plate(self, tracker_id: int, plate_str: str, confidence: float) -> None:
        """Add the predicted plate to the list of plates per tracker ID

        Args:
            tracker_id (int): tracker ID of the detection
            plate_str (str): predicted plate
            confidence (float): confidence score of the plate
        """
        self.plates[tracker_id].append(LicensePlate(plate_str, confidence))

    def run_inference(self, image: np.ndarray, tracker_id: int, annotation: ImageAnnotations) -> None:
        """Run inference on the detection

        Args:
            image (np.ndarray): image array
            tracker_id (int): tracker ID of the detection
            annotation (ImageAnnotations): annotations of the image
        """
        if annotation.bbox is not None:
            crop = image[
                int(annotation.bbox.y) : int(annotation.bbox.y + annotation.bbox.h),
                int(annotation.bbox.x) : int(annotation.bbox.x + annotation.bbox.w),
            ]
            plate_prediction = self.model.predict(crop)
            if len(plate_prediction) > 0:
                det_conf = plate_prediction[0].detection.confidence
                ocr_conf = plate_prediction[0].ocr.confidence
                if isinstance(ocr_conf, list):
                    ocr_conf = min(ocr_conf)
                if det_conf >= self.attributes.detection_threshold and ocr_conf >= self.attributes.ocr_threshold:
                    self.add_plate(tracker_id, plate_prediction[0].ocr.text, ocr_conf)

    def execute(self, container: DataContainer) -> DataContainer:
        """Executes Fast ALPR on the container and adds the prediction for license plate

        Args:
            container (DataContainer): data container

        Returns:
            DataContainer: data container
        """
        for image_packet in container.images:
            for annotation in image_packet.annotations:
                extra_labels = annotation.extra_labels if annotation.extra_labels is not None else {}
                tracker_id = int(extra_labels.get("ID", -1))
                if tracker_id not in self.plates:
                    self.plates[tracker_id] = []

                trigger_alpr = self.check_conditions(image_packet.content, annotation)
                if trigger_alpr:
                    self.run_inference(image_packet.content, tracker_id, annotation)

                if len(self.plates[tracker_id]) > 0:
                    annotation.text = self.get_best_plate(tracker_id)

        return container
