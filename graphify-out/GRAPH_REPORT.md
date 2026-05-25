# Graph Report - /Users/kc/visualessential-scaffold  (2026-05-24)

## Corpus Check
- 196 files · ~348,447 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1231 nodes · 1862 edges · 96 communities (66 shown, 30 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 190 edges (avg confidence: 0.64)
- Token cost: 93,268 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_LatentSync Diffusion UNet|LatentSync Diffusion UNet]]
- [[_COMMUNITY_Image Degradation Pipeline|Image Degradation Pipeline]]
- [[_COMMUNITY_Video Segmentation Pipeline|Video Segmentation Pipeline]]
- [[_COMMUNITY_OpenAI Codex Image Generation|OpenAI Codex Image Generation]]
- [[_COMMUNITY_Scaffold App & Configuration|Scaffold App & Configuration]]
- [[_COMMUNITY_Easy-Wav2Lip Utilities|Easy-Wav2Lip Utilities]]
- [[_COMMUNITY_Image Processing Utilities|Image Processing Utilities]]
- [[_COMMUNITY_Whisper Model Loader|Whisper Model Loader]]
- [[_COMMUNITY_Visual Quality Filtering|Visual Quality Filtering]]
- [[_COMMUNITY_Training Data Pipeline|Training Data Pipeline]]
- [[_COMMUNITY_Whisper Transformer Model|Whisper Transformer Model]]
- [[_COMMUNITY_Text Normalization|Text Normalization]]
- [[_COMMUNITY_Video IO Utilities|Video I/O Utilities]]
- [[_COMMUNITY_Audio Processing|Audio Processing]]
- [[_COMMUNITY_Whisper Tokenizer|Whisper Tokenizer]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]
- [[_COMMUNITY_Community 53|Community 53]]
- [[_COMMUNITY_Community 54|Community 54]]
- [[_COMMUNITY_Community 55|Community 55]]
- [[_COMMUNITY_Community 56|Community 56]]
- [[_COMMUNITY_Community 57|Community 57]]
- [[_COMMUNITY_Community 58|Community 58]]
- [[_COMMUNITY_Community 59|Community 59]]
- [[_COMMUNITY_Community 60|Community 60]]
- [[_COMMUNITY_Community 61|Community 61]]
- [[_COMMUNITY_Community 62|Community 62]]
- [[_COMMUNITY_Community 63|Community 63]]
- [[_COMMUNITY_Community 64|Community 64]]
- [[_COMMUNITY_Community 65|Community 65]]
- [[_COMMUNITY_Community 66|Community 66]]
- [[_COMMUNITY_Community 67|Community 67]]
- [[_COMMUNITY_Community 68|Community 68]]
- [[_COMMUNITY_Community 69|Community 69]]
- [[_COMMUNITY_Community 70|Community 70]]
- [[_COMMUNITY_Community 71|Community 71]]
- [[_COMMUNITY_Community 72|Community 72]]
- [[_COMMUNITY_Community 74|Community 74]]
- [[_COMMUNITY_Community 75|Community 75]]
- [[_COMMUNITY_Community 77|Community 77]]
- [[_COMMUNITY_Community 80|Community 80]]
- [[_COMMUNITY_Community 81|Community 81]]
- [[_COMMUNITY_Community 85|Community 85]]
- [[_COMMUNITY_Community 88|Community 88]]
- [[_COMMUNITY_Community 89|Community 89]]
- [[_COMMUNITY_Community 93|Community 93]]
- [[_COMMUNITY_Community 94|Community 94]]
- [[_COMMUNITY_Community 95|Community 95]]

## God Nodes (most connected - your core abstractions)
1. `Whisper` - 21 edges
2. `Tokenizer` - 21 edges
3. `LipsyncPipeline` - 20 edges
4. `Attention` - 16 edges
5. `OpenAICodexOAuthClient` - 16 edges
6. `__call__()` - 15 edges
7. `ImageProcessor` - 15 edges
8. `UNet3DConditionModel` - 15 edges
9. `LatentSync — audio-conditioned latent diffusion lip-sync model` - 15 edges
10. `Block` - 14 edges

## Surprising Connections (you probably didn't know these)
- `CLAUDE.md — Graphify project instructions` --documents_graphify_for--> `Next.js 14 App Router application`  [INFERRED]
  CLAUDE.md → README.md
- `GET()` --calls--> `getJob()`  [INFERRED]
  app/api/uploads/[id]/route.ts → lib/jobStore.ts
- `Particles()` --calls--> `cn()`  [EXTRACTED]
  components/Particles.tsx → lib/utils.ts
- `LatentSync — audio-conditioned latent diffusion lip-sync model` --potential_tool_for--> `Next.js 14 App Router application`  [INFERRED]
  tools/LatentSync/README.md → README.md
- `Easy-Wav2Lip — improved Wav2Lip lip-sync wrapper` --potential_tool_for--> `Next.js 14 App Router application`  [INFERRED]
  tools/Easy-Wav2Lip/README.md → README.md

## Communities (96 total, 30 thin omitted)

### Community 0 - "LatentSync Diffusion UNet"
Cohesion: 0.05
Nodes (37): Attention, BaseOutput, ConfigMixin, ModelMixin, Attention, BasicTransformerBlock, __init__(), Transformer3DModel (+29 more)

### Community 1 - "Image Degradation Pipeline"
Cohesion: 0.06
Nodes (53): add_gaussian_noise(), add_gaussian_noise_pt(), add_jpg_compression(), add_poisson_noise(), add_poisson_noise_pt(), bivariate_Gaussian(), bivariate_generalized_Gaussian(), bivariate_plateau() (+45 more)

### Community 2 - "Video Segmentation Pipeline"
Cohesion: 0.06
Nodes (29): eval_fvd(), FVD, compute_fvd(), compute_our_fvd(), compute_stats(), main(), data_processing_pipeline(), detect_shot() (+21 more)

### Community 3 - "OpenAI Codex Image Generation"
Cohesion: 0.06
Nodes (26): main(), main(), Example: Generate images using Codex OAuth (no API key)., main(), OpenAICodexOAuthClient, Run the full device code flow for openai-codex., Standalone OpenAI Codex (ChatGPT) OAuth client.      Handles device-code login,, Perform device code login flow. (+18 more)

### Community 4 - "Scaffold App & Configuration"
Cohesion: 0.05
Nodes (44): CLAUDE.md — Graphify project instructions, Music Video Generator — Personal Scaffold (README), 6-step create flow (Photos→Audio→Scene→Outfit→Lyrics→Generate), Google Gemini (scene image generation backend option), Generation API backend (VisualEssential proxy or DIY), Kling AI (video generation backend option), Lyrics overlay (15 fonts, position, case, blend mode), Next.js 14 App Router application (+36 more)

### Community 5 - "Easy-Wav2Lip Utilities"
Cohesion: 0.08
Nodes (13): get_video_details(), _load(), load_file_from_url(), load_model(), Load file form http url, will download models if necessary.      Ref:https://g, Function to display video in Colab, show_video(), Conv2d (+5 more)

### Community 6 - "Image Processing Utilities"
Cohesion: 0.09
Nodes (17): object, decode(), Detect, nms_(), PriorBox, Decode locations from predictions using priors to undo     the encoding we did f, Apply non-maximum suppression at test time to avoid detecting too many     overl, Courtesy of Ross Girshick     [https://github.com/rbgirshick/py-faster-rcnn/blob (+9 more)

### Community 7 - "Whisper Model Loader"
Cohesion: 0.09
Nodes (23): load_audio(), log_mel_spectrogram(), mel_filters(), pad_or_trim(), Open an audio file and read as mono waveform, resampling as necessary      Param, Pad or trim the audio array to N_SAMPLES, as expected by the encoder., load the mel filterbank matrix for projecting STFT into a Mel spectrogram.     A, Compute the log-Mel spectrogram of      Parameters     ----------     audio: Uni (+15 more)

### Community 8 - "Visual Quality Filtering"
Cohesion: 0.1
Nodes (15): Bottleneck, HyperNet, Target network for quality prediction., Fully connection operations for target net      Note:         Weights & biases a, Hyper network for learning perceptual rules.      Args:         lda_out_channels, Constructs a ResNet-50 model_hyper.      Args:         pretrained (bool): If Tru, resnet50_backbone(), ResNetBackbone (+7 more)

### Community 9 - "Training Data Pipeline"
Cohesion: 0.09
Nodes (15): FrameDataset, get_dataloader(), is_image_file(), preprocess(), preprocess_image(), Initializes and return the dataset., Initializes and returns the dataloader., Generic dataset for videos files stored in folders.     Videos of the same class (+7 more)

### Community 10 - "Whisper Transformer Model"
Cohesion: 0.12
Nodes (11): AudioEncoder, Conv1d, LayerNorm, Linear, MultiHeadAttention, x : torch.Tensor, shape = (batch_size, n_mels, n_ctx)             the mel spectr, x : torch.LongTensor, shape = (batch_size, <= n_ctx)             the text tokens, Returns sinusoids for positional embedding (+3 more)

### Community 11 - "Text Normalization"
Cohesion: 0.11
Nodes (10): BasicTextNormalizer, Replace any other markers, symbols, and punctuations with a space,     and drop, Replace any other markers, symbols, punctuations with a space, keeping diacritic, remove_symbols(), remove_symbols_and_diacritics(), EnglishNumberNormalizer, EnglishSpellingNormalizer, EnglishTextNormalizer (+2 more)

### Community 12 - "Video I/O Utilities"
Cohesion: 0.12
Nodes (13): main(), validation(), main(), cosine_loss(), dummy_context, gather_loss(), init_dist(), one_step_sampling() (+5 more)

### Community 13 - "Audio Processing"
Cohesion: 0.15
Nodes (15): _amp_to_db(), _build_mel_basis(), get_hop_size(), get_melspec_overlap(), _linear_to_mel(), linearspectrogram(), _lws_processor(), melspectrogram() (+7 more)

### Community 14 - "Whisper Tokenizer"
Cohesion: 0.13
Nodes (13): DecodingOptions, all_language_codes(), build_tokenizer(), get_tokenizer(), no_speech(), no_timestamps(), non_speech_tokens(), A thin wrapper around `GPT2TokenizerFast` providing quick access to special toke (+5 more)

### Community 15 - "Community 15"
Cohesion: 0.11
Nodes (19): CreatePageInner(), NAV_ITEMS, PhonePreview, PIPELINE_LABELS, Step, STEP_ICONS, STEP_LABELS, STEPS (+11 more)

### Community 16 - "Community 16"
Cohesion: 0.15
Nodes (14): _amp_to_db(), _build_mel_basis(), get_hop_size(), _linear_to_mel(), linearspectrogram(), _lws_processor(), melspectrogram(), _normalize() (+6 more)

### Community 17 - "Community 17"
Cohesion: 0.11
Nodes (11): FeatureStats, load(), Get all the stored features as NumPy Array.          Returns:             Concat, Get all the stored features as PyTorch Tensor.          Returns:             Con, Get the mean and covariance of the stored features.          Returns:, Save the features and statistics to a pickle file.          Args:             pk, Class to store statistics of features, including all features and mean/covarianc, Set the number of features diminsions.          Args:             num_features: (+3 more)

### Community 18 - "Community 18"
Cohesion: 0.14
Nodes (14): BasePredictor, load_sr(), upscale(), create_mask(), create_tracked_mask(), datagen(), face_detect(), face_rect() (+6 more)

### Community 19 - "Community 19"
Cohesion: 0.12
Nodes (10): FaceDetector, remove_incorrect_affined(), remove_incorrect_affined_multiprocessing(), count_total_videos_time(), main(), plot_histogram(), FileslistWriter, count_video_time() (+2 more)

### Community 20 - "Community 20"
Cohesion: 0.15
Nodes (5): DiffusionPipeline, __call__(), LipsyncPipeline, paste_surrounding_pixels_back(), check_ffmpeg_installed()

### Community 21 - "Community 21"
Cohesion: 0.15
Nodes (6): cuda_to_int(), FaceDetector, Convert the string with format "cuda:X" to integer X., ImageProcessor, load_fixed_mask(), VideoProcessor

### Community 22 - "Community 22"
Cohesion: 0.13
Nodes (10): BeamSearchDecoder, decode(), DecodingResult, GreedyDecoder, Initialize any stateful variables for decoding a new sequence, Specify how to select the next token, based on the current trace and logits, Finalize search and return the final candidate sequences          Parameters, Performs decoding of 30-second audio segment(s), provided as Mel spectrogram(s). (+2 more)

### Community 23 - "Community 23"
Cohesion: 0.14
Nodes (7): ApplyTimestampRules, LogitFilter, Apply any filtering or masking to logits in-place          Parameters         --, SuppressBlank, SuppressTokens, The `MultiHeadAttention` module optionally accepts `kv_cache` which stores the k, Whisper

### Community 24 - "Community 24"
Cohesion: 0.15
Nodes (9): Image editing / img2img using xAI.         Note: Support depends on xAI's curren, Start an async video generation job on xAI.          Returns immediately with a, Poll video generation status.          Returns status: "pending" | "processing", Upload a file to xAI Files API, returns file_id for use in generate_video., Placeholder for audio generation.         xAI may add TTS in the future. Current, Optionally lets Grok itself improve the prompt for better results.         This, Flexible and powerful media generation client for xAI.      Designed to be highl, Generate an image using xAI's Grok Imagine.          - `style`: artistic style, (+1 more)

### Community 25 - "Community 25"
Cohesion: 0.12
Nodes (13): ALL_ITEMS, BOTTOMS, buildOutfitDescription(), HATS, ITEM_MAP, OUTFIT_CATEGORIES, OUTFIT_PRESETS, OutfitCategory (+5 more)

### Community 26 - "Community 26"
Cohesion: 0.18
Nodes (14): main(), CLI entry point for xai-oauth-client., clear_tokens(), ensure_token_dir(), get_token_path(), load_full_state(), load_tokens(), Token storage for xAI OAuth (simple JSON file, modeled after Hermes). (+6 more)

### Community 27 - "Community 27"
Cohesion: 0.17
Nodes (11): COLOR_SCHEMES, FaqAccordion(), FaqAccordionProps, FAQItem, FloatingNav(), FloatingNavProps, NavItem, Particle (+3 more)

### Community 28 - "Community 28"
Cohesion: 0.16
Nodes (6): Attention, CosAttention, DropPath, PatchEmbed, Drop paths (Stochastic Depth) per sample  (when applied in main path of residual, Image to Patch Embedding

### Community 29 - "Community 29"
Cohesion: 0.18
Nodes (4): DecodingTask, detect_language(), PyTorchInference, Detect the spoken language in the audio, and return them as list of strings, alo

### Community 30 - "Community 30"
Cohesion: 0.19
Nodes (5): main(), AttentionBlock2D, DownEncoder2D, ResnetBlock2D, StableSyncNet

### Community 31 - "Community 31"
Cohesion: 0.16
Nodes (3): calc_pdist(), SyncNetEval, S

### Community 32 - "Community 32"
Cohesion: 0.21
Nodes (9): GET(), getJob(), Job, store, ClipStatus, ClipStatusResponse, GeneratePayload, OutfitSelection (+1 more)

### Community 33 - "Community 33"
Cohesion: 0.16
Nodes (14): Device Code OAuth Flow, gpt-image-2 Model, grok-imagine-image Model, Hermes Agent (referenced OAuth/media origin), openai-codex-client Package, OpenAI Codex Client README, OpenAI Codex Client Python Requirements, OpenAICodexMediaClient (+6 more)

### Community 34 - "Community 34"
Cohesion: 0.24
Nodes (9): _cfg(), pretrain_videomae_base_patch16_224(), pretrain_videomae_giant_patch14_224(), pretrain_videomae_huge_patch16_224(), pretrain_videomae_large_patch16_224(), pretrain_videomae_small_patch16_224(), PretrainVisionTransformer, Vision Transformer with support for patch or hybrid CNN input stage (+1 more)

### Community 35 - "Community 35"
Cohesion: 0.2
Nodes (6): Block, get_sinusoid_encoding_table(), Sinusoid position encoding table, PretrainVisionTransformerDecoder, Vision Transformer with support for patch or hybrid CNN input stage, trunc_normal_()

### Community 36 - "Community 36"
Cohesion: 0.16
Nodes (8): main(), main(), Advanced Media Generation Example using xAI OAuth  This demonstrates the flexibl, Example usage of the xAI OAuth client., Refresh the access token using the refresh token., Make sure we have a valid, non-expired access token., High-level client for xAI OAuth., XaiOAuthClient

### Community 37 - "Community 37"
Cohesion: 0.2
Nodes (4): main(), Audio2Feature, Get sliced features based on a given index         :param feature_array:, Get sliced features based on a given index         :param feature_array:

### Community 38 - "Community 38"
Cohesion: 0.24
Nodes (8): _pkce_challenge(), _pkce_verifier(), Main xAI OAuth client (PKCE flow + refresh)., Custom exception for xAI OAuth errors., Perform the full OAuth PKCE login flow., _start_callback_server(), _wait_for_callback(), XaiOAuthError

### Community 40 - "Community 40"
Cohesion: 0.29
Nodes (6): Exception, FaceDetector, filter_high_resolution_multiprocessing(), filter_video(), gather_video_paths(), multi_run_wrapper()

### Community 41 - "Community 41"
Cohesion: 0.22
Nodes (4): load_videomae_model(), Vision Transformer with support for patch or hybrid CNN input stage, VisionTransformer, vit_giant_patch14_224()

### Community 42 - "Community 42"
Cohesion: 0.22
Nodes (7): BEFORE_AFTER, FAQ, NAV_ITEMS, Particles, POPULAR, BeforeAfterCompare(), BeforeAfterCompareProps

### Community 43 - "Community 43"
Cohesion: 0.27
Nodes (10): LatentSync Framework Architecture Diagram, LatentSync Mouth-Region Mask (Variant 1 - Upper lip notch), LatentSync Mouth-Region Mask (Variant 2 - Wider semi-circle), LatentSync Mouth-Region Mask (Variant 3 - Narrow semi-circle), LatentSync Mouth-Region Mask (Variant 4 - Tall lower-jaw coverage), SyncNet Supervision (LatentSync), UNet Denoiser with Temporal Layers (LatentSync), VAE Decoder (LatentSync) (+2 more)

### Community 44 - "Community 44"
Cohesion: 0.29
Nodes (8): main(), syncnet_eval(), adjust_offset(), func(), gather_paths(), split(), sync_av_multi_gpus(), red_text()

### Community 45 - "Community 45"
Cohesion: 0.42
Nodes (8): buildScenePrompt(), downloadFile(), ffmpegAudioMerge(), POST(), runPipeline(), sleep(), createJob(), updateJob()

### Community 46 - "Community 46"
Cohesion: 0.33
Nodes (9): Before/After Video Comparison Pair Concept, Armory After Poster - Rapper in gun room, dark cinematic, high production, Armory Before Poster - Rapper in dark hallway, moody streetwear aesthetic, By The Fire After Poster - Guitarist at moonlit campfire, cinematic outdoor mood, By The Fire Before Poster - Guitarist in home studio, ungraded natural light, In The City After Poster - Artist in teal hoodie, low-angle night city shot, cinematic, In The City Before Poster - Artist in blue hoodie indoors, raw/ungraded look, On The Radar After Poster - Artist at mic with neon green sign, studio performance (+1 more)

### Community 47 - "Community 47"
Cohesion: 0.25
Nodes (5): _no_grad_trunc_normal_(), # NOTE: drop path for stochastic depth, we shall see if this is better than drop, # TODO: make it with torch instead of numpy, r"""Fills the input Tensor with values drawn from a truncated     normal distrib, trunc_normal_()

### Community 48 - "Community 48"
Cohesion: 0.29
Nodes (5): SHOTS, SceneTag, Shot, ALL_TAGS, NAV_ITEMS

### Community 54 - "Community 54"
Cohesion: 0.29
Nodes (3): drop_path(), Mlp, Adapted from timm codebase

### Community 55 - "Community 55"
Cohesion: 0.43
Nodes (6): affine_transform_multi_gpus(), combine_video_audio(), func(), gather_video_paths(), split(), write_video()

### Community 57 - "Community 57"
Cohesion: 0.29
Nodes (4): Inference, Perform a forward pass on the decoder and return per-token logits, Update the key-value cache according to the updated beams, Clean up any resources or hooks after decoding is finished

### Community 58 - "Community 58"
Cohesion: 0.29
Nodes (4): MaximumLikelihoodRanker, Given a list of groups of samples and their cumulative log probabilities,, Select the sample with the highest log probabilities, penalized using either, SequenceRanker

### Community 60 - "Community 60"
Cohesion: 0.33
Nodes (3): Constants for xAI OAuth (matching Hermes implementation)., xAI OAuth Client package with rich media generation support., Advanced Media Generation Client for xAI (Grok Imagine)  Supports: - Image gener

### Community 62 - "Community 62"
Cohesion: 0.6
Nodes (3): download_videos(), extract_vid(), main()

## Knowledge Gaps
- **247 isolated node(s):** `config`, `nextConfig`, `Load the model into memory to make running multiple predictions efficient`, `Run a single prediction on the model`, `Initializes distributed environment.` (+242 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **30 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Block` connect `Community 35` to `LatentSync Diffusion UNet`, `Community 34`, `Visual Quality Filtering`, `Whisper Transformer Model`, `Community 47`, `Community 50`, `Community 54`, `Community 28`?**
  _High betweenness centrality (0.143) - this node is a cross-community bridge._
- **Why does `main()` connect `Video I/O Utilities` to `Community 37`, `Community 69`, `Community 44`, `Community 49`, `Community 20`, `Community 56`, `Community 30`, `Community 31`?**
  _High betweenness centrality (0.090) - this node is a cross-community bridge._
- **Why does `syncnet_eval()` connect `Community 44` to `Community 40`, `Video I/O Utilities`?**
  _High betweenness centrality (0.080) - this node is a cross-community bridge._
- **Are the 14 inferred relationships involving `Whisper` (e.g. with `DecodingOptions` and `DecodingResult`) actually correct?**
  _`Whisper` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Are the 14 inferred relationships involving `Tokenizer` (e.g. with `DecodingOptions` and `DecodingResult`) actually correct?**
  _`Tokenizer` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `LipsyncPipeline` (e.g. with `UNet3DConditionModel` and `ImageProcessor`) actually correct?**
  _`LipsyncPipeline` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 10 inferred relationships involving `Attention` (e.g. with `TemporalTransformer3DModelOutput` and `VanillaTemporalModule`) actually correct?**
  _`Attention` has 10 INFERRED edges - model-reasoned connections that need verification._