# Tracking, Speed Estimation and ALPR Templates

## Purpose
These packages follow objects across video frames and build traffic analytics on top of the tracks:
- `sinapsis-supervision`: ByteTrack.
- `sinapsis-rf-trackers`: SORT and DeepSORT.
- `sinapsis-cotracker`: dense point tracking with Meta CoTracker3.
- `sinapsis-fast-alpr`: license-plate recognition, speed estimation with perspective correction, and class filtering.

The shipped speed-camera agent chains these templates: VideoReaderCV2 → RFDETRInference → ClassFilter → ByteTrack → DetectionPerspectiveTransform → ObjectSpeedCalculation → FastALPR → BBoxDrawer → VideoWriterCV2.

Citations are relative to `packages/python/vision/<group>/<package>/src/<module>/templates/`.

## Requirements

### Requirement: ByteTrack tracking
`ByteTrack` SHALL replace each image's annotations with bbox, label, label_str and `extra_labels["ID"]`, where the ID is the track id. Confidence and masks are dropped. (src: sinapsis-supervision byte_track.py:53-186)

#### Scenario: Stable IDs
- **GIVEN** a car detected in consecutive frames
- **WHEN** ByteTrack runs with default attributes
- **THEN** the car SHALL carry the same `extra_labels["ID"]` in every frame
- **AND** the defaults SHALL be activation threshold 0.20, lost buffer 30, matching threshold 0.7 and frame rate 30

### Requirement: SORT and DeepSORT tracking
`SORTTrackerInference` and `DeepSORTTrackerInference` SHALL replace each image's annotations with bbox, label, label_str, confidence and `extra_labels["ID"]`. Images with no annotations SHALL be skipped and SHALL NOT update the tracker. (src: sinapsis-rf-trackers rf_tracker_base.py:50-193)

#### Scenario: Defaults
- **WHEN** the tracker attributes are omitted
- **THEN** activation SHALL be 0.25, lost buffer 30, minimum consecutive frames 3 and minimum IoU 0.3
- **AND** DeepSORT SHALL use the re-identification model `tf_efficientnet_b1.in1k`, cosine distance and appearance threshold 0.7

### Requirement: Dense point tracking
`CoTrackerOffline`, `CoTrackerOnline` and `CoTrackerOfflineLarge` SHALL download the CoTracker3 checkpoint from `huggingface.co/facebook/cotracker3` into `model_cache_dir`. They SHALL write `{tracks (B,T,N,2), visibilities (B,T,N)}` to `generic_data`. `device` and `model_variant` are required. (src: sinapsis-cotracker co_tracker_base.py:86-120)

#### Scenario: Offline grid tracking
- **WHEN** CoTrackerOffline runs on a clip with `grid_size: 10`
- **THEN** tracks for the grid points SHALL be written to generic_data

#### Scenario: Online buffering
- **WHEN** CoTrackerOnline runs
- **THEN** it SHALL buffer `step*2` frames before emitting tracks

### Requirement: Track visualization
`CoTrackerVisualizer` SHALL render the tracks stored under the required `generic_key_field` onto images. Mode SHALL be one of `rainbow`, `cool` or `optical_flow`. (src: sinapsis-cotracker co_tracker_visualizer.py:14)

#### Scenario: Render tracks
- **WHEN** the visualizer runs with `mode: rainbow` and `overwrite: false`
- **THEN** the rendered frames SHALL be appended as new images

### Requirement: License plate recognition
`FastALPR` SHALL process each bbox annotation that has no text and whose bottom edge satisfies y/H ≥ `alpr_y_threshold`. For each, it SHALL crop and read the plate, accumulate the readings per `extra_labels["ID"]`, and set `annotation.text` to the best plate. (src: sinapsis-fast-alpr fast_alpr.py:53-81)

#### Scenario: Plate voting
- **GIVEN** a track read as "ABC123" twice and "A8C123" once
- **WHEN** FastALPR processes the frames
- **THEN** `annotation.text` SHALL be "ABC123" (majority vote, then confidence sum)

#### Scenario: Defaults
- **WHEN** the attributes are omitted
- **THEN** the detector SHALL be `yolo-v9-s-608-license-plate-end2end`
- **AND** the OCR model SHALL be `cct-xs-v1-global-model`
- **AND** `alpr_y_threshold` SHALL be 0.7

### Requirement: Perspective transform
`DetectionPerspectiveTransform` SHALL map each bbox through the perspective defined by `source_points` into `oriented_bbox`. When `filter_detections_roi` is true, which is the default, it SHALL drop detections outside the ROI plus a 10% margin. (src: sinapsis-fast-alpr perspective_transform.py:18-131)

#### Scenario: Outside ROI
- **WHEN** a detection lies well outside the source polygon
- **THEN** it SHALL be removed

### Requirement: Speed estimation
`ObjectSpeedCalculation` SHALL require `fps`, `meters_per_pixel` and `speed_limit`. It SHALL write `extra_labels["Speed(km/h)"]`, and SHALL set an `"Over limit"` flag that stays set for the rest of that track. (src: sinapsis-fast-alpr speed_calculation.py:23-114)

#### Scenario: Speeding vehicle
- **GIVEN** a tracked car whose speed exceeds `speed_limit`
- **WHEN** ObjectSpeedCalculation runs
- **THEN** the annotation SHALL be flagged "Over limit"
- **AND** the flag SHALL persist for that track id

### Requirement: Class filter and calibration tools
`ClassFilter` SHALL keep only annotations whose `label_str` is in `classes_to_keep`. The package SHALL install the calibration CLIs `pick-coordinates` and `meters-per-pixel`. (src: sinapsis-fast-alpr class_filter.py:16)

#### Scenario: Default classes
- **WHEN** `classes_to_keep` is omitted
- **THEN** only car, truck, motorcycle and bus annotations SHALL be kept
