# OCR Templates

## Purpose
These packages extract text from images:
- `sinapsis-doctr` and `sinapsis-easyocr` are classic OCR engines that return word-level boxes.
- `sinapsis-deepseek-ocr` and `sinapsis-glm-ocr` are vision-language models that return page-level text (markdown, JSON or tables).

Citations are relative to `packages/python/vision/ocr/<package>/src/<module>/templates/`.

## Requirements

### Requirement: DocTR word OCR
`DocTROCRPrediction` SHALL detect and recognize words. For each word it SHALL extend the image annotations with a bbox, a confidence and the recognized text. (src: sinapsis-doctr doc_tr_ocr_prediction.py:73-279)

#### Scenario: Defaults
- **WHEN** the architecture attributes are omitted
- **THEN** `det_arch` SHALL be `fast_base`
- **AND** `reco_arch` SHALL be `crnn_vgg16_bn`, using pretrained weights

### Requirement: EasyOCR
`EasyOCR` SHALL extend the image annotations with a bbox, a confidence and the text, with accents stripped. When `get_full_text` is set, it SHALL also append one space-joined TextPacket. (src: sinapsis-easyocr easy_ocr.py:16-174)

#### Scenario: Full text output
- **GIVEN** an image containing "Hola Mundo"
- **WHEN** EasyOCR runs with `get_full_text: true` and default reader params
- **THEN** one TextPacket "Hola Mundo" SHALL be appended
- **AND** the reader SHALL use `lang_list ["en"]`, `gpu True` and the `craft` detector

### Requirement: DeepSeek OCR
`DeepSeekOCRInference` SHALL load `deepseek-ai/DeepSeek-OCR` on CUDA, which is required. With `enable_grounding` false it SHALL append one TextPacket per image. With grounding true it SHALL add bbox annotations instead, with coordinates denormalized from 0-999. (src: sinapsis-deepseek-ocr deepseek_ocr_inference.py:37-195)

#### Scenario: Grounded OCR
- **WHEN** DeepSeekOCRInference runs with `enable_grounding: true`
- **THEN** text regions SHALL be added as bbox annotations
- **AND** no TextPacket SHALL be produced

#### Scenario: Defaults
- **WHEN** `mode` and `prompt` are omitted
- **THEN** `mode` SHALL be `base`
- **AND** `prompt` SHALL be "OCR the image."

### Requirement: GLM OCR
`GLMOCRInference` and `GLMOCRBatchInference` SHALL load `zai-org/GLM-OCR` and append one TextPacket per image. (src: sinapsis-glm-ocr glm_ocr_base_inference.py:32)

#### Scenario: Defaults
- **WHEN** the generation attributes are omitted
- **THEN** the prompt SHALL be "Text Recognition:"
- **AND** `max_new_tokens` SHALL be 8192
