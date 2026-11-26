# AI and ML Templates

## Purpose
These Template packages add LLM, generative and classic-ML capabilities to Agents:

| Package | What it adds |
|---|---|
| `sinapsis-chatbots-base` | Chat with any OpenAI-compatible endpoint, with streaming, multimodal, structured outputs and MCP tool loops |
| `sinapsis-unsloth` | LoRA fine-tuning, inference and export |
| `sinapsis-huggingface-*` | diffusers, transformers, Grounding DINO, embeddings, Hub download |
| `sinapsis-openai` | OpenAI endpoints |
| `sinapsis-bertopic` | Topic modelling |
| `sinapsis-vowpal-wabbit` | Contextual bandits |

Each package is installed on its own and exposes its Templates through a lazy `templates/__init__.py` lookup. Citations are relative to `packages/python/`.

## Requirements

### Requirement: LLM conversation input
`LLMConversationInput` SHALL append one `LLMConversationPacket` to `container.llm_conversations`. The packet SHALL contain the required `prompt`, an optional `system_prompt` and an optional `identity` (`user_id`, `session_id`, `run_id`, `agent_id`). (src: ai/chatbots/sinapsis_chatbots_base/src/sinapsis_chatbots_base/templates/llm_conversation_input.py:17-111)

#### Scenario: Prompt from file
- **GIVEN** `prompt: prompts/q.txt` and the file exists
- **WHEN** the template executes
- **THEN** the packet content SHALL be the file's text

#### Scenario: Missing .txt path
- **GIVEN** `prompt: missing.txt` and the file does not exist
- **WHEN** the template executes
- **THEN** the literal string `missing.txt` SHALL be used as the prompt

### Requirement: Text to conversation
`TextToLLMConversation` SHALL convert `container.texts` into conversation packets, with each prompt built as `prompt_prefix + text + prompt_suffix`. (src: ai/chatbots/sinapsis_chatbots_base/src/sinapsis_chatbots_base/templates/text_to_llm_conversation.py:25-110)

#### Scenario: Single mode default
- **WHEN** it runs with the default `mode: single`
- **THEN** all texts SHALL be joined with `"\n\n--- PAGE ---\n\n"` into one packet

#### Scenario: Per-packet mode
- **WHEN** it runs with `mode: per_text_packet` over 3 texts
- **THEN** 3 conversation packets SHALL be created

### Requirement: OpenAI-compatible completion
`EndpointLLMCompletion` SHALL call `chat.completions` at `init_args.base_url`. It SHALL send messages in this order: the system prompt with contexts formatted as `[category] source\ncontent`, then the history, then tool results, then the user prompt. (src: ai/chatbots/sinapsis_chatbots_base/src/sinapsis_chatbots_base/templates/endpoint_llm_completion.py:31-226)

#### Scenario: Defaults
- **WHEN** only `base_url` is configured
- **THEN** `timeout` SHALL be 120 s and `max_tokens` SHALL be 4096
- **AND** `temperature`, `top_p` and `top_k` SHALL be unset (None)
- **AND** the API key SHALL fall back to `LLM_API_KEY` when `init_args.api_key` is unset

#### Scenario: Response written to packet
- **WHEN** the completion succeeds
- **THEN** `response`, `reasoning`, `usage`, `termination`, `provider_info` and the measured latency SHALL be set on the packet

### Requirement: Reasoning extraction and cache skip
LLM templates SHALL split text between `reasoning_start_tag` and `reasoning_end_tag` (defaults `<think>` and `</think>`) into `reasoning`. They SHALL skip packets whose `finish_reason` is `cache_hit`. (src: ai/chatbots/sinapsis_chatbots_base/src/sinapsis_chatbots_base/templates/llm_template_base.py:17-32,375-418)

#### Scenario: Reasoning separated
- **WHEN** the model returns `<think>plan</think>Answer`
- **THEN** `reasoning` SHALL be `plan` and `response` SHALL be `Answer`

#### Scenario: Cached packet
- **GIVEN** a packet with `termination.finish_reason == "cache_hit"`
- **WHEN** the template executes
- **THEN** no request SHALL be sent for that packet

### Requirement: Structured output
When `response_format.type` is `json_object`, the request SHALL ask for JSON. A schema, if given, SHALL be sent as `json_schema` named `structured_output`. The response SHALL be parsed into `structured_output`. (src: ai/chatbots/sinapsis_chatbots_base/src/sinapsis_chatbots_base/templates/endpoint_llm_completion.py:148-164; llm_template_base.py:385-403)

#### Scenario: Without schema
- **WHEN** no schema is configured
- **THEN** the request SHALL send `{"type": "json_object"}`

#### Scenario: Invalid JSON
- **WHEN** the response is not valid JSON
- **THEN** `structured_output` SHALL stay unset
- **AND** only a warning SHALL be logged

### Requirement: Streaming completion
`EndpointLLMStreamingCompletion` SHALL run only asynchronously. It SHALL yield one partial container per delta and SHALL mark the final container with an end-of-stream sentinel. (src: ai/chatbots/sinapsis_chatbots_base/src/sinapsis_chatbots_base/templates/endpoint_llm_streaming_completion.py:61-308)

#### Scenario: Sync call
- **WHEN** the sync `invoke_backend` is called
- **THEN** `NotImplementedError` SHALL be raised

#### Scenario: Stream deltas
- **WHEN** a stream yields deltas
- **THEN** each partial packet's `response` SHALL contain only the current delta
- **AND** the final container SHALL have `generic_data["SINAPSIS_SENTINEL"] = "SINAPSIS_END_OF_STREAM"`
- **AND** `stream_options.include_usage` SHALL be forced to true

### Requirement: Multimodal completion
`EndpointLLMMultiModal` SHALL send `container.images` as `image_url` data URIs placed before the text part of the user turn. (src: ai/chatbots/sinapsis_chatbots_base/src/sinapsis_chatbots_base/templates/endpoint_llm_multimodal.py:44-57)

#### Scenario: Image question
- **GIVEN** one image and the prompt "What is this?"
- **WHEN** the template executes
- **THEN** the user message SHALL contain an image part followed by a text part

### Requirement: MCP tool loop
`EndpointLLMCompletionWithMCP` SHALL parse tool calls, first from native `tool_calls` and otherwise from the response text. It SHALL report `num_elements() == 1` while calls are pending, so that an `AsyncWhileLoop` keeps iterating. (src: ai/chatbots/sinapsis_chatbots_base/src/sinapsis_chatbots_base/templates/endpoint_llm_completion_mcp.py:55-593)

#### Scenario: Defaults
- **WHEN** the tool attributes are omitted
- **THEN** `max_tool_retries` SHALL be 3, `tool_choice` SHALL be `auto`, and `add_tool_to_prompt` and `send_tools_in_payload` SHALL be true

#### Scenario: Retries exhausted
- **WHEN** three consecutive tool rounds fail
- **THEN** the packet SHALL stop with `stop_reason="max_tool_retries"` and a fallback response

### Requirement: Unsloth model loading
Unsloth templates SHALL load models with `FastLanguageModel.from_pretrained`, using `HF_TOKEN` and `model_args`. (src: ai/llm/sinapsis-unsloth/src/sinapsis_unsloth/templates/unsloth_base.py:10-50; helpers/schemas/base.py:120-153)

#### Scenario: Defaults
- **WHEN** only `model_name` is given
- **THEN** `max_seq_length` SHALL be 2048, `load_in_4bit` SHALL be true and `device_map` SHALL be `sequential`
- **AND** `cache_dir` SHALL be `SINAPSIS_CACHE_DIR` and `random_state` SHALL be 3407

### Requirement: Unsloth fine-tuning
`UnslothPretrainer`, `UnslothInstructTrainer` (Alpaca format) and `UnslothConversationTrainer` (alpaca or sharegpt input) SHALL train LoRA adapters on a Hugging Face dataset. They SHALL save the adapters to `save_path` and write that path to `generic_data`. (src: ai/llm/sinapsis-unsloth/src/sinapsis_unsloth/templates/training/; helpers/schemas/fine_tuning.py:11-288)

#### Scenario: Training defaults
- **WHEN** the training attributes are omitted
- **THEN** LoRA `r` and `lora_alpha` SHALL be 16
- **AND** `epochs` SHALL be 3, `lr` SHALL be 5e-5 and `batch_size` SHALL be 8
- **AND** `packing` SHALL be false

### Requirement: Unsloth inference
`UnslothInferenceCompletion`, `UnslothInferenceInstruct`, `UnslothInferenceConversational` and `UnslothInferenceReasoning` SHALL append generated TextPackets to `container.texts`. Inputs SHALL always be moved to `cuda`, so there is no CPU path. (src: ai/llm/sinapsis-unsloth/src/sinapsis_unsloth/templates/inference/unsloth_inference_base.py:122-204)

#### Scenario: Reasoning output
- **WHEN** UnslothInferenceReasoning generates `<think>cot</think>ans`
- **THEN** a TextPacket containing `ans` SHALL be appended
- **AND** `generic_data[instance_name]` SHALL be `cot`

### Requirement: Unsloth export
`UnslothExportGGUF` and `UnslothExportMerged` SHALL save the model locally, or push it to the Hub when `push_to_hub` is true. (src: ai/llm/sinapsis-unsloth/src/sinapsis_unsloth/templates/)

#### Scenario: Export defaults
- **WHEN** the export attributes are omitted
- **THEN** GGUF SHALL use `quantization_method: fast_quantized`
- **AND** merged export SHALL use `save_method: merged_16bit`

### Requirement: Diffusers generation
`TextToImageDiffusers`, `ImageToImageDiffusers`, `InpaintingDiffusers` (bbox or mask mode) and `ImageToVideoGenXLDiffusers` SHALL generate uint8 RGB ImagePackets. `device` is required, and `model_path` is restricted to a Literal of model ids. (src: ai/sinapsis-huggingface/sinapsis_huggingface_diffusers/src/sinapsis_huggingface_diffusers/templates/base_diffusers.py:69-76)

#### Scenario: Text-to-image
- **WHEN** TextToImageDiffusers runs with `device: cuda` and the prompt "a cat"
- **THEN** `num_images_per_prompt` images SHALL be appended

#### Scenario: Allowed models
- **WHEN** `model_path` is omitted
- **THEN** it SHALL default to `stable-diffusion-v1-5/stable-diffusion-v1-5`
- **AND** the only other accepted values SHALL be SD 2.1, SD 1.4 and `Qwen/Qwen-Image-Edit`

### Requirement: Transformers pipelines
The transformers package SHALL provide `ImageToTextTransformers`, `SpeechToTextTransformers`, `SummarizationTransformers`, `TranslationTransformers`, `SentimentAnalysisTransformers`, `TextToSpeechTransformers`, `PaliGemmaInference` and `PaliGemmaDetection`. These SHALL wrap Hugging Face pipelines or PaliGemma. (src: ai/sinapsis-huggingface/sinapsis_huggingface_transformers/src/sinapsis_huggingface_transformers/templates/)

#### Scenario: In-place text tasks
- **WHEN** summarization or translation runs
- **THEN** the text content SHALL be overwritten in place

#### Scenario: TTS output
- **WHEN** TextToSpeechTransformers runs
- **THEN** `container.audios` SHALL be replaced

#### Scenario: Missing module
- **WHEN** `PaliGemmaSegmentation` is accessed
- **THEN** `ModuleNotFoundError` SHALL currently be raised, because its module does not exist

### Requirement: Grounding DINO
`GroundingDINO` SHALL perform open-vocabulary detection from `text_input`, which must contain `.`. It SHALL replace each image's annotations. `GroundingDINOClassification` SHALL extend annotations with the top-k class labels. (src: ai/sinapsis-huggingface/sinapsis_huggingface_grounding_dino/src/sinapsis_huggingface_grounding_dino/templates/grounding_dino.py:38-43)

#### Scenario: Detection defaults
- **WHEN** `threshold`, `text_threshold` and `top_k` are omitted
- **THEN** `threshold` and `text_threshold` SHALL be 0.25
- **AND** classification `top_k` SHALL be 5

### Requirement: Embeddings and Hub download
`HuggingFaceEmbeddingExtractor` and `SpeakerEmbeddingFromAudio` SHALL write `packet.embedding`. `HuggingFaceDownloader` SHALL run `snapshot_download` at init and write the local path to `generic_data`. (src: ai/sinapsis-huggingface/sinapsis_huggingface_embeddings/src/; ai/sinapsis-huggingface/sinapsis_huggingface_hub/src/)

#### Scenario: Download repo
- **WHEN** HuggingFaceDownloader runs with `repo_id` and the default `max_workers` of 8
- **THEN** the snapshot path SHALL be written to `generic_data`

### Requirement: OpenAI dynamic wrappers
`sinapsis-openai` SHALL generate the Chat, AudioTranscription, AudioTranslation, AudioCreation, ImageCreation, ImageToImageGeneration and ImageInpainting templates by wrapping the `OpenAI` client. Client kwargs go under `openai_init`, and endpoint kwargs go under `create`, `generate` or `edit`. (src: ai/sinapsis-openai/src/sinapsis_openai/templates/openai_base.py:51-208)

#### Scenario: API key precedence
- **GIVEN** both `OPENAI_API_KEY` and `openai_init.api_key` are set
- **WHEN** the client is created
- **THEN** the env var SHALL take precedence

#### Scenario: API error
- **WHEN** the endpoint raises `APIConnectionError` or `BadRequestError`
- **THEN** the error SHALL be logged
- **AND** no result SHALL be produced

### Requirement: Topic modelling
`BERTopicFitModel` and `BERTopicFitModelFromDataFrame` SHALL fit BERTopic and save it to `root_dir/save_model_path`. `BERTopicPredict` SHALL attach a topic `TextAnnotations` to each text. (src: ml/sinapsis-bertopic/src/sinapsis_bertopic/templates/)

#### Scenario: Fit defaults
- **WHEN** the fit attributes are omitted
- **THEN** the embedding model SHALL be `sentence-transformers/all-MiniLM-L6-v2`
- **AND** `min_topic_size` SHALL be 5 and `top_n_words` SHALL be 10

#### Scenario: Predict topics
- **WHEN** BERTopicPredict runs on 3 texts
- **THEN** each text SHALL receive one annotation with `label`, `label_str` and `confidence_score`

### Requirement: Contextual-bandit learning
`CBExploreADFLearn` and `CBExploreADFLearnEmbeddings` SHALL train a Vowpal Wabbit `--cb_explore_adf` model over the configured `actions` and save it to `save_path`. (src: ml/sinapsis-vowpal-wabbit/src/sinapsis_vowpal_wabbit/templates/cb_explore_adf_base.py:43-205)

#### Scenario: Learn defaults
- **WHEN** the learning attributes are omitted
- **THEN** `epochs` SHALL be 5, the exploration SHALL be `epsilon` with value 0.2, and `bit_precision` SHALL be 24

### Requirement: Contextual-bandit prediction
`CBExploreADFPredict` and `CBExploreADFPredictEmbeddings` SHALL replace each text's annotations with the `top_k` actions (default 3), ranked by probability. (src: ml/sinapsis-vowpal-wabbit/src/sinapsis_vowpal_wabbit/templates/cb_explore_adf_predict.py:94)

#### Scenario: Nothing above threshold
- **WHEN** no action probability passes `threshold`
- **THEN** the label SHALL currently be the misspelled `"Unkown"`
