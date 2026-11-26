# Object Detection and Anomaly Detection Templates

## Purpose
These packages provide object detection, segmentation, pose estimation, oriented-bounding-box (OBB) detection, classification and anomaly detection. They cover training, validation, inference and export, and write their results as `ImagePacket.annotations`.

| Package | Models |
|---|---|
| `sinapsis-ultralytics` | YOLO, YOLOWorld, SAM, FastSAM, NAS, RTDETR |
| `sinapsis-rfdetr` | RF-DETR base and large |
| `sinapsis-dfine` | D-FINE, loaded via Hugging Face |
| `sinapsis-anomalib` | Anomalib |

Citations are relative to `packages/python/vision/<group>/<package>/src/<module>/`.

## Requirements

### Requirement: Ultralytics model selection
All Ultralytics templates SHALL require `model_class` and `model`. `model_class` SHALL be one of YOLO, YOLOWorld, SAM, FastSAM, NAS or RTDETR. (src: sinapsis-ultralytics templates/ultralytics_base.py:53-60)

#### Scenario: Missing model_class
- **WHEN** UltralyticsPredict is configured without `model_class`
- **THEN** attribute validation SHALL fail

### Requirement: Ultralytics training, validation and export
`UltralyticsTrain` SHALL write `{metrics, trained_model_path}` to `generic_data`. `UltralyticsVal` SHALL write `{metrics, results_path}` to `generic_data`. `UltralyticsExport` SHALL export the model. (src: sinapsis-ultralytics templates/ultralytics_train.py:16; ultralytics_val.py:16; ultralytics_export.py:17; helpers/params.py:7-30)

#### Scenario: Defaults
- **WHEN** params are omitted
- **THEN** training SHALL use epochs 100, batch 16 and imgsz 640
- **AND** validation SHALL use conf 0.001 and iou 0.7
- **AND** export SHALL use format torchscript

### Requirement: Ultralytics prediction
`UltralyticsPredict` SHALL extend each image's annotations with the results for its task:
- detection: bounding boxes, plus masks and keypoints when present
- OBB: oriented boxes
- classification: the top-1 label, with the top-5 in `extra_labels`

(src: sinapsis-ultralytics helpers/ultralytics_predict_helpers.py:235-256)

#### Scenario: YOLO detection
- **WHEN** UltralyticsPredict runs with `model_class: YOLO` and default params
- **THEN** each image SHALL gain bbox annotations for detections with confidence of at least 0.25 (iou 0.7)

#### Scenario: SAM without prompts
- **WHEN** a SAM or FastSAM model runs with `use_detections_as_sam_prompt` false
- **THEN** no annotations SHALL be produced

### Requirement: RF-DETR inference
`RFDETRInference` and `RFDETRLargeInference` SHALL optimize the model for inference at init. They SHALL extend annotations with bbox, label, label_str and confidence for detections at or above `threshold`. Class names SHALL come from `annotations_path` (COCO) if set, otherwise from COCO_CLASSES. (src: sinapsis-rfdetr helpers/rfdetr_helpers.py:31-79)

#### Scenario: Below threshold
- **WHEN** a detection scores 0.3 and `threshold` is left at its default of 0.5
- **THEN** no annotation SHALL be added for it

### Requirement: RF-DETR training and export
`RFDETR*Train` SHALL write its per-epoch history to `generic_data` as a DataFrame. `RFDETR*Export` SHALL export the model to ONNX and SHALL NOT write anything to the container. (src: sinapsis-rfdetr templates/rfdetr_train.py:19; templates/rfdetr_export.py:26)

#### Scenario: Export
- **WHEN** RFDETRExport runs with `export_params.output_dir`
- **THEN** an ONNX model SHALL be written to that directory

### Requirement: D-FINE inference
`DFINEInference` SHALL load `model_path` and run in batches of `batch_size`. It SHALL extend annotations for detections at or above the required `threshold`. (src: sinapsis-dfine templates/dfine_base.py:31-34; templates/dfine_inference.py:27)

#### Scenario: Defaults and auto device
- **GIVEN** a machine without CUDA
- **WHEN** DFINEInference runs with default `model_path`, `device` and `batch_size`
- **THEN** it SHALL load `ustc-community/dfine-nano-coco`
- **AND** it SHALL run on CPU with batches of 8

### Requirement: D-FINE training
`DFINETraining` SHALL fine-tune the model on `dataset_path` and save the model and processor to `save_dir`. By default, `ALLOW_UNVETTED_DATASETS` is True, which skips the dataset license check. (src: sinapsis-dfine templates/dfine_training.py:53; helpers/env_var_keys.py:11-21)

#### Scenario: Defaults
- **WHEN** the optional training attributes are omitted
- **THEN** the validation split SHALL be 0.15
- **AND** the image size SHALL be 640x640

### Requirement: Anomalib dynamic templates
`sinapsis-anomalib` SHALL generate `<Model>Train` and `<Model>Export` templates for each `anomalib.models` model, except EfficientAd, VlmAd, Cfa, Dfkde, Fastflow, Supersimplenet and AiVad. (src: sinapsis-anomalib templates/anomalib_base.py:30-137)

#### Scenario: Excluded model
- **WHEN** an Agent references `CfaTrain`
- **THEN** template resolution SHALL fail

### Requirement: Anomalib training and export
Anomalib training SHALL require `folder_attributes` (`name` and `normal_dir`) and SHALL write `{metrics, checkpoint_path}` to `generic_data`. Export SHALL use `ckpt_path` if given, otherwise the checkpoint from training. (src: sinapsis-anomalib templates/anomalib_train.py:72-121; anomalib_export.py:150-160)

#### Scenario: Train then export
- **GIVEN** `PatchcoreTrain` followed by `PatchcoreExport` with no `ckpt_path`
- **WHEN** the Agent runs
- **THEN** the export SHALL use the checkpoint produced by training
- **AND** training SHALL default to the cpu accelerator with 1-5 epochs

### Requirement: Anomalib inference
`AnomalibTorchInference` and `AnomalibOpenVINOInference` SHALL replace each image's annotations with the result:
- If there is no anomaly mask, a single classification annotation: anomalous or normal, with confidence = score × 100.
- If there is a mask, one bbox plus `Segmentation` annotation for each contour whose area is at least `anomaly_area_threshold`.

(src: sinapsis-anomalib templates/anomalib_base_inference.py:145-171)

#### Scenario: Mask contours
- **WHEN** the anomaly mask has one contour of area 500 and `anomaly_area_threshold` is at its default of 100
- **THEN** exactly one bbox+segmentation annotation SHALL be produced
