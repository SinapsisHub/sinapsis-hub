# -*- coding: utf-8 -*-
from sinapsis.data_transport import DataContainer
from sinapsis.template import Template, TemplateAttributes, TemplateAttributeType

VEHICLES = ["car", "truck", "motorcycle", "bus"]


class ClassFilterAttributes(TemplateAttributes):
    """
    classes_to_keep (list(str)): list of classes names to keep
    """

    classes_to_keep: list[str] = VEHICLES


class ClassFilter(Template):
    """Template to filter detections based on their class label

    Example agent:

    agent:
      name: my_test_agent
    templates:
    - template_name: InputTemplate
    class_name: InputTemplate
    attributes: {}
    - template_name: ClassFilter
    class_name: ClassFilter
    template_input: InputTemplate
    attributes:
        classes_to_keep:
        - car
        - truck
        - motorcycle
        - bus

    """

    AttributesBaseModel = ClassFilterAttributes
    attributes: ClassFilterAttributes

    def __init__(self, attributes: TemplateAttributeType) -> None:
        super().__init__(attributes)

    def execute(self, container: DataContainer) -> DataContainer:
        for image_packet in container.images:
            annotations = [
                annotation
                for annotation in image_packet.annotations
                if annotation.label_str in self.attributes.classes_to_keep
            ]
            image_packet.annotations = annotations

        return container
