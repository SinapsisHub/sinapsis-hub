# Data Processing Templates

## Purpose
These packages form the I/O and utility layer used by most Agents:

| Package | Provides |
|---|---|
| `sinapsis-data-readers` | File, dataset, video and audio readers |
| `sinapsis-data-writers` | Image, video, audio, COCO and JSON writers |
| `sinapsis-data-visualization` | Annotation drawers and plots |
| `sinapsis-generic-data-tools` | Buffers, masks, chunking and color conversion |
| `sinapsis-langchain-readers` | Every LangChain document loader, wrapped dynamically |
| `sinapsis-langchain-splitters` | Every LangChain text splitter, wrapped dynamically |

Citations are relative to `packages/python/data/processing/`.

## Requirements

### Requirement: File-based reader iteration
File readers SHALL iterate across executions and add the next batch to the container on each execute. (src: sinapsis_data_readers/src/sinapsis_data_readers/templates/base_file_data_loader.py:62)

#### Scenario: Defaults
- **WHEN** the reader attributes are omitted
- **THEN** `root_dir` SHALL default to `SINAPSIS_CACHE_DIR` and `pattern` SHALL default to `**/*`
- **AND** `batch_size` SHALL be 1 (`-1` loads all), `shuffle_data` SHALL be false, `samples_to_load` SHALL be -1 and `load_on_init` SHALL be false

#### Scenario: Batched folder reading
- **GIVEN** `FolderImageDatasetCV2` with `batch_size: 2` over a folder of 5 images
- **WHEN** the Agent executes three times
- **THEN** the executions SHALL yield 2, 2 and 1 RGB images, each labelled with its parent directory

### Requirement: Text and audio readers
The readers package SHALL provide `TextInput`, `AudioReaderPydub`, `AudioReaderSoundfile` and `AudioReaderToBytes`. Pydub and Soundfile SHALL also come in Lazy and ExecuteNTimes variants. (src: sinapsis_data_readers/src/sinapsis_data_readers/templates/text_readers/; audio_readers/)

#### Scenario: Text input
- **WHEN** `TextInput` runs with `text: "hi"`
- **THEN** one TextPacket "hi" SHALL be appended

#### Scenario: Pydub defaults
- **WHEN** AudioReaderPydub runs with defaults
- **THEN** the audio SHALL be read at 16 kHz as mono float32

### Requirement: Image and COCO readers
The readers package SHALL provide `FolderImageDatasetCV2`, `CSVImageDataset`, `CocoDetectionDatasetCV2`, `CocoSegmentationDatasetCV2` and `CocoKeypointsDatasetCV2`. (src: sinapsis_data_readers/src/sinapsis_data_readers/templates/image_readers/)

#### Scenario: Supported image extensions
- **WHEN** FolderImageDatasetCV2 scans a folder
- **THEN** only .jpg, .jpeg, .png, .gif and .tiff files SHALL be loaded

#### Scenario: CSV pixel dataset
- **WHEN** CSVImageDataset reads an MNIST-style CSV with default height and width 28
- **THEN** column 0 SHALL be used as the label and the remaining columns as pixels

### Requirement: Tabular readers
`CSVDatasetReader` SHALL load a CSV into a DataFramePacket, or into a TimeSeriesPacket when `store_as_time_series` is set. `CSVDatasetSplitter` SHALL append x/y train/test DataFramePackets. (src: sinapsis_data_readers/src/sinapsis_data_readers/templates/datasets_readers/csv_datasets.py:11; dataset_splitter.py:9)

#### Scenario: Splitter defaults
- **WHEN** CSVDatasetSplitter runs with defaults
- **THEN** `target_key` SHALL be `target`, `random_state` SHALL be 42 and `train_size` SHALL be 0.2

### Requirement: Video readers
The readers package SHALL provide `VideoReaderCV2`, `MultiVideoReaderCV2`, `LiveVideoReaderCV2`, plus DALI (GPU only), FFMPEG and TorchCodec variants. These SHALL emit frames as ImagePackets with source `<video_source>_<idx>`. (src: sinapsis_data_readers/src/sinapsis_data_readers/templates/video_readers/)

#### Scenario: CV2 frames
- **WHEN** VideoReaderCV2 reads a video with `batch_size: 1`
- **THEN** each execute SHALL append one RGB frame

### Requirement: Dynamic dataset readers
The readers package SHALL generate wrapper templates for every `sklearn.datasets` `load*`/`fetch*` function (for example `load_irisWrapper`) and for every `sktime.datasets` loader, minus each exclusion list. (src: sinapsis_data_readers/src/sinapsis_data_readers/templates/datasets_readers/sklearn_datasets.py:26-189; sktime_datasets.py:25-211)

#### Scenario: sklearn split
- **WHEN** `load_irisWrapper` runs with `split_dataset: true` and the default `train_size` of 0.9
- **THEN** x_train, y_train, x_test and y_test DataFramePackets SHALL be appended

#### Scenario: sktime defaults
- **WHEN** an sktime dataset wrapper runs with defaults
- **THEN** `train_size` SHALL be 0.7 and the output SHALL be TimeSeriesPackets

### Requirement: Image and video writers
`ImageSaver` SHALL write images with cv2 and update `packet.source` to the saved path. `VideoWriterCV2` and `VideoWriterFFMPEG` SHALL encode frames into a video file. (src: sinapsis_data_writers/src/sinapsis_data_writers/templates/image_writers/image_saver.py:22; video_writers/)

#### Scenario: Save images
- **WHEN** ImageSaver runs with `save_dir: out` and `extension: png`
- **THEN** each image SHALL be written as a PNG under `out`

#### Scenario: Allowed formats
- **WHEN** an image extension or codec is chosen
- **THEN** ImageSaver SHALL accept jpg (the default), png, tif, bmp, ppm, webp, jp2, hdr and ras
- **AND** VideoWriterCV2 SHALL accept `mp4v` (the default) or `avc1`

#### Scenario: In-place color change
- **WHEN** ImageSaver or VideoWriterCV2 processes RGB packets
- **THEN** the input packets SHALL be converted to BGR in place

### Requirement: Audio, JSON, COCO and PDF writers
The writers package SHALL provide `AudioWriterSoundfile` (wav, flac, aif, raw), `GenericDataJSONWriter`, `COCOAnnotationWriter` and `PDFToImage`. (src: sinapsis_data_writers/src/sinapsis_data_writers/templates/)

#### Scenario: COCO unknown label
- **WHEN** an annotation's label is not in `category_mapping`
- **THEN** it SHALL be written with category -1 "generic"

#### Scenario: PDF dpi
- **WHEN** PDFToImage runs with defaults
- **THEN** pages SHALL be rendered at 200 dpi
- **AND** the dpi SHALL be capped at 800

### Requirement: Annotation drawers
`LabelDrawer`, `BBoxDrawer`, `KeyPointsDrawer`, `OrientedBBoxDrawer` and `SegmentationMaskDrawer` SHALL draw annotations onto images. (src: sinapsis_data_visualization/src/sinapsis_data_visualization/templates/)

#### Scenario: Non-overwriting draw
- **GIVEN** images with bbox annotations and `overwrite` left at its default of false
- **WHEN** BBoxDrawer runs
- **THEN** annotated copies with source `a_<name>` SHALL be appended
- **AND** the originals SHALL be unchanged

#### Scenario: Mask alpha
- **WHEN** SegmentationMaskDrawer runs with defaults
- **THEN** masks SHALL be blended with alpha 0.5

### Requirement: Data plots
`DataDistributionVisualization` and `TabularDataVisualization` SHALL save PNG plots under `save_image_dir` (default `SINAPSIS_CACHE_DIR`) and append them as ImagePackets. (src: sinapsis_data_visualization/src/sinapsis_data_visualization/templates/base_visualization_template.py:39-76)

#### Scenario: Histogram
- **WHEN** TabularDataVisualization runs with `histogram: true`
- **THEN** a histogram PNG SHALL be saved and appended as an image

### Requirement: Generic data tools
The generic tools package SHALL provide `ImageColorConversionNumpy`, `MaskNonROIs`, `PacketBufferQueue`, `SourceHistoryAggregator`, `TextContentFilter` and `ContextChunker`. (src: sinapsis-generic-data-tools/src/sinapsis_generic_data_tools/templates/)

#### Scenario: Unmapped color conversion
- **WHEN** ImageColorConversionNumpy is asked for an unsupported color-space pair
- **THEN** `ValueError` SHALL be raised

#### Scenario: Repetitive text filtered
- **WHEN** TextContentFilter sees a text in which one word repeats more than 10 times
- **THEN** the content SHALL be replaced with "invalid string, please try again"

#### Scenario: Chunker defaults
- **WHEN** ContextChunker runs with defaults
- **THEN** it SHALL create sentence windows of 5 with an overlap of 2

### Requirement: Dynamic LangChain loaders
`sinapsis-langchain-readers` SHALL generate a `<Loader>Wrapper` for each `langchain_community.document_loaders` class that is not excluded. Constructor kwargs SHALL go under the attribute `<lowercasename>_init`. (src: sinapsis-langchain-readers/src/sinapsis_langchain_readers/templates/langchain_data_readers.py:30-122)

#### Scenario: Wikipedia loader
- **WHEN** `WikipediaLoaderWrapper` runs with `wikipedialoader_init: {query: "Python"}` and `add_document_as_text_packet: true`
- **THEN** one TextPacket SHALL be appended per page, with the page title as source

#### Scenario: Documents to generic data
- **WHEN** `add_document_as_text_packet` is false (the default)
- **THEN** the Documents SHALL be written to `generic_data`

### Requirement: LangChain text splitters
`sinapsis-langchain-splitters` SHALL wrap the `langchain_text_splitters` classes as `<Splitter>Wrapper` templates. It SHALL also provide `RegexTurnSplitter` and `PatternAggregatorSplitter`. (src: sinapsis-langchain-splitters/src/sinapsis_langchain_splitters/templates/)

#### Scenario: Split text packets
- **WHEN** `RecursiveCharacterTextSplitterWrapper` runs on texts with `add_document_as_text_packet: true`
- **THEN** `container.texts` SHALL be replaced by the chunks
