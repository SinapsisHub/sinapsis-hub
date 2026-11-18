# -*- coding: utf-8 -*-

import os
import tempfile
from pathlib import Path
from typing import Any, Literal, cast

import cv2
import numpy as np
from openai._exceptions import APIConnectionError, BadRequestError
from openai.types import ImageModel
from sinapsis.data_transport import DataContainer, ImageColor, ImagePacket, Packet
from sinapsis.env_vars import SINAPSIS_BUILD_DOCS
from sinapsis.template import (
    BaseDynamicWrapperTemplate,
    OutputTypes,
    TemplateAttributes,
    TemplateAttributeType,
    UIPropertiesMetadata,
    WrapperEntryConfig,
    make_dynamic_template,
)
from sinapsis_generic_data_tools.helpers.encode_img_base64 import decode_base64_to_numpy, fetch_url_to_numpy

from sinapsis_openai.helpers.openai_env_var_keys import OpenAIEnvVars
from sinapsis_openai.helpers.openai_keys import OpenAIKeys
from sinapsis_openai.helpers.tags import Tags
from sinapsis_openai.templates.openai_base import ImagesResponse, OpenAIBase, OpenAICreateType

OpenAIImageUIProperties = OpenAIBase.UIProperties
if OpenAIImageUIProperties.tags is not None:
    OpenAIImageUIProperties.tags.extend([Tags.IMAGE, Tags.IMAGE_GENERATION, Tags.IMAGE_EDITION])


class OpenAIImageCreation(OpenAIBase):
    """
    Template that wraps the `OpenAI.images.generate` API endpoint to
    perform image generation tasks. This template excludes the `prompt`,
    `model`, and `response_format` attributes from the API caller and are
    set through static template attributes. In this way, the `prompt` is received
    as input (via the content of a packet) and the `model` and `response_format` are defined in
    the `AttributesBaseModel`.

    Usage example:

    agent:
      name: my_test_agent
    templates:
    - template_name: InputTemplate
      class_name: InputTemplate
      attributes: {}
    - template_name: OpenAIImageCreationWrapper
      class_name: OpenAIImageCreationWrapper
      template_input: InputTemplate
      attributes:
        model: 'dall-e-2'
        response_format: url
        openai_init:
          api_key: openai_api_key
          max_retries: 2
        generate:
          n: 1

    """

    WrapperEntry = WrapperEntryConfig(
        wrapped_object=OpenAIBase.CLIENT,
        template_name_suffix="ImageCreationWrapper",
        additional_callables_to_inspect=[
            WrapperEntryConfig(
                wrapped_object=OpenAIBase.CLIENT(api_key=str(OpenAIEnvVars.OPENAI_API_KEY.value)).images.generate,
                exclude_method_attributes=[OpenAIKeys.prompt, OpenAIKeys.model, OpenAIKeys.response_format],
            )
        ],
    )
    UIProperties = UIPropertiesMetadata(category="OpenAI", output_type=OutputTypes.IMAGE)

    class AttributesBaseModel(TemplateAttributes):
        """Attributes for the OpenAIImageCreation.

        Attributes:
            model (ImageModel): The image model to use for
            generating images.
            response_format (Literal["url", "b64_json"]):
                Specifies the format of the API response (default is "url").
        """

        model: ImageModel
        response_format: Literal["url", "b64_json"] = "url"

    attributes: AttributesBaseModel

    def __init__(self, attributes: TemplateAttributeType) -> None:
        super().__init__(attributes)

        self.create = self.openai.images.generate

    def unpack_create_items(self) -> dict:
        generate = getattr(self.attributes, "generate")
        return generate.model_dump()

    def parse_results(self, responses: list | dict | Any, container: DataContainer) -> DataContainer:
        """
        For each of the responses, creates an ImagePacket to be
        appended to the DataContainer

        Args:
            responses (list[str]): List of URL from the OpenAI responses.
            container (DataContainer): The original data container.

        Returns:
            DataContainer: The modified container with appended ImagePackets.
        """
        for response in responses:
            if response is not None:
                container.images.append(
                    ImagePacket(content=response, source=self.instance_name, color_space=ImageColor.RGB)
                )
        return container

    def return_create_response(self, content: str | list | bytes) -> OpenAICreateType:
        """
        Sends an image generation request to the API endpoint
        using the provided prompt.

        Args:
            content (str | list | bytes): The prompt extracted from the packet.

        Returns:
            OpenAICreateType: The raw response from the OpenAI image generation API.
        """
        content = cast(str, content)
        try:
            response = self.create(
                prompt=content,
                model=self.attributes.model,
                response_format=self.attributes.response_format,
                **self.not_not_given,
            )
        except BadRequestError:
            response = self.create(prompt=content, model=self.attributes.model, **self.not_not_given)

        return response

    def process_response(self, response: OpenAICreateType) -> Any:
        response = cast(ImagesResponse, response)
        if self.attributes.response_format == "b64_json":
            image = decode_base64_to_numpy(str(getattr(response, "data")[0].b64_json))
        else:
            image = fetch_url_to_numpy(str(getattr(response, "data")[0].url))

        return image


class OpenAIImageToImageGeneration(OpenAIImageCreation):
    """
    Template that wraps the `OpenAI.images.edit` API endpoint to
    perform image-to-image generation tasks.
    This template excludes the `image`, `prompt`, `model`, and
    `response_format` attributes from the API caller.
    Instead, the image is provided through the attribute `path_to_image`
    in the `AttributesBaseModel`.
    The PACKAET_TYPE_NAME indicates that this template processes packets stored in the
    image field of the DataContainer as the prompt
    Usage example:
    agent:
      name: my_test_agent
    templates:
    - template_name: InputTemplate
      class_name: InputTemplate
      attributes: {}
    - template_name: OpenAIImageToImageGenerationWrapper
      class_name: OpenAIImageToImageGenerationWrapper
      template_input: InputTemplate
      attributes:
        model: dall-e-2
        response_format: url
        path_to_image: '/path/to/image/to/be/edited'
        openai_init:
          api_key: openai_api_key
          max_retries: 2
        generate:
          n: 1
    """

    class AttributesBaseModel(OpenAIImageCreation.AttributesBaseModel):
        """
        Configuration attributes for the OpenAIImageToImageGeneration template.
        Attributes:
            model (Literal["dall-e-2", "gpt-image-1"]): The fixed image model used for
            image generation tasks.
            path_to_image (str): The file path of the original image to
            be used as input for image-to-image generation.
        """

        model: Literal["gpt-image-1"] = "gpt-image-1"

    attributes: AttributesBaseModel

    WrapperEntry = WrapperEntryConfig(
        wrapped_object=OpenAIBase.CLIENT,
        template_name_suffix="ImageToImageGenerationWrapper",
        additional_callables_to_inspect=[
            WrapperEntryConfig(
                wrapped_object=OpenAIBase.CLIENT(api_key=str(OpenAIEnvVars.OPENAI_API_KEY.value)).images.edit,
                exclude_method_attributes=[
                    OpenAIKeys.image,
                    OpenAIKeys.prompt,
                    OpenAIKeys.model,
                    OpenAIKeys.response_format,
                ],
            )
        ],
    )
    PACKET_TYPE_NAME = "texts"

    def __init__(self, attributes: TemplateAttributeType) -> None:
        super().__init__(attributes)
        self.create = self.openai.images.edit

    def unpack_create_items(self) -> dict:
        edit = getattr(self.attributes, "edit")
        return edit.model_dump()

    def return_create_response_paths(self, content: str | list | bytes, image_paths: list[Path]) -> OpenAICreateType:
        """
        Sends an image editing request to the API endpoint with the
        provided prompt.
        The image is taken from `path_to_image` and an optional
         mask from `path_to_mask` (if provided).
        These values are supplied exclusively via template attributes,
        which is why the corresponding API parameters are excluded.
        It is also expected that the image is in `png` format and,
        if a mask is used, that the mask matches the size of the
        original image.

        Args:
            content (str | list | bytes): The prompt for image editing,
            extracted from the packet.

        Returns:
            OpenAICreateType: The raw response from the OpenAI image editing API.
        """
        edit = getattr(self.attributes, "edit")
        result = self.create(  # ty: ignore[no-matching-overload]
            image=image_paths, prompt=content, model=self.attributes.model, **edit.model_dump()
        )
        return result

    def get_paths_from_image_packets(self, image_packets: list[ImagePacket]) -> list[Path]:
        file_paths: list[Path] = []
        for image_packet in image_packets:
            image_content = image_packet.content

            if image_packet.color_space == ImageColor.BGR:
                bgra_image = cv2.cvtColor(image_content, cv2.COLOR_BGR2BGRA)

            elif image_packet.color_space == ImageColor.RGB:
                bgra_image = cv2.cvtColor(image_content, cv2.COLOR_RGB2BGRA)

            elif image_packet.color_space == ImageColor.GRAY:
                bgr_image = cv2.cvtColor(image_content, cv2.COLOR_GRAY2BGR)
                bgra_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2BGRA)
            elif image_packet.color_space == ImageColor.RGBA:
                bgra_image = cv2.cvtColor(bgr_image, cv2.COLOR_RGBA2BGRA)
            else:
                self.logger.debug(f"Unsupported image packet color space: {image_packet.color_space}, skipping image.")
                continue

            fd, tmp_path = tempfile.mkstemp(suffix=".png")
            os.close(fd)
            cv2.imwrite(tmp_path, bgra_image)
            file_paths.append(Path(tmp_path))
        return file_paths

    @staticmethod
    def _cleanup_paths(paths: list[Path]) -> None:
        for p in paths:
            if p.exists():
                p.unlink()

    def generate_response_from_client_paths(self, packet: Packet, image_paths: list[Path]) -> Any:
        message = self.unpack_packet_content(packet)
        result = None

        try:
            response = self.return_create_response_paths(message, image_paths)
            result = self.process_response(response)
        except (APIConnectionError, BadRequestError) as err:
            self.logger.warning(f"Error processing request: {err}")

        return result

    def execute(self, container: DataContainer) -> DataContainer:
        """
        Executes the overall process of retrieving and processing
        OpenAI API responses. It iterates over each target packet in the DataContainer,
        sends the content of, so it can be processed by the API. Then, the response is
        gathered and processed using get_results. Finally, the processed responses are
        added to the container for downstream usage.

        Args:
            container (DataContainer): The container holding the input data packets.

        Returns:
            DataContainer: The updated container with responses from OpenAI.
        """

        img_paths = self.get_paths_from_image_packets(container.images)
        responses_from_openai: list[str | dict | Any] = []

        data_packet = getattr(container, self.PACKET_TYPE_NAME)

        for packet in data_packet:
            response_output = self.generate_response_from_client_paths(packet, img_paths)
            responses_from_openai.append(self.get_results(response_output))

        container = self.parse_results(responses_from_openai, container)
        self._cleanup_paths(img_paths)

        return container


class OpenAIImageInpainting(OpenAIImageToImageGeneration):
    """
    Template that wraps the `OpenAI.images.edit` API endpoint to perform
    image edition tasks.
    This template excludes the `image`, `mask`, `response_format`, `model`,
    and `prompt` attributes from the API caller.
    Instead, the image is provided through the attribute `path_to_image`
    and an optional mask through `path_to_mask` in the `AttributesBaseModel`.
    Additionally, the original image must be in `png` format,
    and, if a mask is provided, it must have the same dimensions as the original
    image.
    The PACKAET_TYPE_NAME indicates that this template processes packets stored in the
    text field of the DataContainer as the prompt

    Usage example:

    agent:
      name: my_test_agent
    templates:
    - template_name: InputTemplate
      class_name: InputTemplate
      attributes: {}
    - template_name: OpenAIImageEditionWrapper
      class_name: OpenAIImageEditionWrapper
      template_input: InputTemplate
      attributes:
        model: dall-e-2
        response_format: url
        openai_init:
          api_key: openai_api_key
          max_retries: 2
        edit:
          n: 1
    """

    class AttributesBaseModel(OpenAIImageToImageGeneration.AttributesBaseModel):
        """
        Configuration attributes for the OpenAIImageEdition template.

        Attributes:
            model (Literal["dall-e-2", "gpt-image-1"]): The fixed image model used for
            image edition tasks.
        """

        model: Literal["dall-e-2", "gpt-image-1"] = "gpt-image-1"

    attributes: AttributesBaseModel

    WrapperEntry = WrapperEntryConfig(
        wrapped_object=OpenAIBase.CLIENT,
        template_name_suffix="ImageInpaintingWrapper",
        additional_callables_to_inspect=[
            WrapperEntryConfig(
                wrapped_object=OpenAIBase.CLIENT(api_key=str(OpenAIEnvVars.OPENAI_API_KEY.value)).images.edit,
                exclude_method_attributes=[
                    OpenAIKeys.image,
                    OpenAIKeys.mask,
                    OpenAIKeys.response_format,
                    OpenAIKeys.model,
                    OpenAIKeys.prompt,
                ],
            )
        ],
    )
    PACKET_TYPE_NAME = "texts"

    def return_create_response_from_client(
        self, content: str | list | bytes, image_path: Path, mask_path: Path
    ) -> OpenAICreateType:
        """
        Sends an image editing request to the API endpoint with the
        provided prompt.
        The image is taken from `path_to_image` and an optional
         mask from `path_to_mask` (if provided).
        These values are supplied exclusively via template attributes,
        which is why the corresponding API parameters are excluded.
        It is also expected that the image is in `png` format and,
        if a mask is used, that the mask matches the size of the
        original image.

        Args:
            content (str | list | bytes): The prompt for image editing,
            extracted from the packet.

        Returns:
            OpenAICreateType: The raw response from the OpenAI image editing API.
        """
        edit = getattr(self.attributes, "edit")
        result = self.create(  # ty: ignore[no-matching-overload]
            image=image_path, mask=mask_path, prompt=content, model=self.attributes.model, **edit.model_dump()
        )
        return result

    def generate_response(self, packet: Packet, image_paths: list[Path], mask_paths: list[Path]) -> list:
        message = self.unpack_packet_content(packet)
        results = []
        for image_path, mask_path in zip(image_paths, mask_paths):
            self.logger.info(
                f"image_path={image_path},exists={image_path.exists()},mask_path={mask_path},exists={mask_path.exists()}"
            )
            try:
                response = self.return_create_response_from_client(message, image_path, mask_path)
                result = self.process_response(response)

            except (APIConnectionError, BadRequestError) as err:
                self.logger.warning(f"Error processing request: {err}")
                result = None
            results.append(result)

        return results

    @staticmethod
    def mask_to_image(mask: Any) -> np.ndarray:
        """Transform a binary mask into BGRA image
        Face (mask==1) will be transparent (edited area)
        Background (mask==0) will be opaque (preserved area)
        """
        mask = mask.astype(np.uint8)

        h, w = mask.shape
        bgra_image = np.zeros((h, w, 4), dtype=np.uint8)

        bgra_image[:, :, :3] = 255

        bgra_image[:, :, 3] = np.where(mask == 1, 0, 255)

        return bgra_image

    def get_mask_paths_from_image_packets(self, image_packets: list[ImagePacket]) -> list[Path]:
        """Find the first mask annotation for each image and save as paths

        Args:
            image_packets (ImagePacket): image packets

        Returns:
            list[str]: list of file paths
        """
        file_paths: list[Path] = []
        for image_packet in image_packets:
            annot = next((a for a in image_packet.annotations if a.segmentation), None)
            if annot is None or annot.segmentation is None:
                self.logger.debug("No segmentation annotation found, skipping image.")
                continue
            image = self.mask_to_image(annot.segmentation.mask)

            fd, tmp_path = tempfile.mkstemp(suffix=".png")
            os.close(fd)
            cv2.imwrite(tmp_path, image)
            file_paths.append(Path(tmp_path))
        return file_paths

    def execute(self, container: DataContainer) -> DataContainer:
        """
        Executes the overall process of retrieving and processing
        OpenAI API responses. It iterates over each target packet in the DataContainer,
        sends the content of, so it can be processed by the API. Then, the response is
        gathered and processed using get_results. Finally, the processed responses are
        added to the container for downstream usage.

        Args:
            container (DataContainer): The container holding the input data packets.

        Returns:
            DataContainer: The updated container with responses from OpenAI.
        """
        img_paths = self.get_paths_from_image_packets(container.images)
        mask_paths = self.get_mask_paths_from_image_packets(container.images)
        responses_from_openai: list[str | dict | Any] = []

        data_packet = getattr(container, self.PACKET_TYPE_NAME)

        for packet in data_packet:
            response_output_list = self.generate_response(packet, img_paths, mask_paths)
            responses_from_openai = [self.get_results(response_output) for response_output in response_output_list]

        container = self.parse_results(responses_from_openai, container)
        self._cleanup_paths(img_paths + mask_paths)

        return container


def __getattr__(name: str) -> type[BaseDynamicWrapperTemplate] | None:
    """
    Only create a template if it's imported, this avoids creating all
    the base models for all templates and potential import errors due
    to not available packages.
    """
    if name in OpenAIImageCreation.WrapperEntry.module_att_names:
        return make_dynamic_template(name, OpenAIImageCreation)
    if name in OpenAIImageInpainting.WrapperEntry.module_att_names:
        return make_dynamic_template(name, OpenAIImageInpainting)
    if name in OpenAIImageToImageGeneration.WrapperEntry.module_att_names:
        return make_dynamic_template(name, OpenAIImageToImageGeneration)


__all__ = (
    OpenAIImageCreation.WrapperEntry.module_att_names
    + OpenAIImageInpainting.WrapperEntry.module_att_names
    + OpenAIImageToImageGeneration.WrapperEntry.module_att_names
)

if SINAPSIS_BUILD_DOCS:
    dynamic_templates = [__getattr__(template_name) for template_name in __all__]
    for template in dynamic_templates:
        globals()[getattr(template, "__name__")] = template
        del template
