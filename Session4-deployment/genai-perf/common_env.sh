# General Docker Variables:
#
# Name of the container to be created

export NIM_CONTAINER_NAME=nim-llama-3.1-70b-instruct
# The Docker/Nim Container to run:
export NIM_IMG_NAME=nvcr.io/nim/meta/llama-3.1-70b-instruct:1.10.1

# NIM Variables. For more information on NIM, see:
# https://docs.nvidia.com/nim/large-language-models/latest/configuration.html#environment-variables
# 
# Specifies the model configuration profile to use -
# Fpr ex: tensorrt_llm-a100-bf16-tp4-pp1-throughput profile is optimized for A100 GPUs with BF16 Precision, 
# tensor parallelism of 4, pipeline parallelism of 1, and optimized for throughput
# Please, use the profile name, instead of the profile id
export NIM_MODEL_PROFILE=tensorrt_llm-trtllm_buildable-bf16-tp4-pp1
# tensorrt_llm-trtllm_buildable-fp8-tp4-pp1
# Gets current user ID for Docker container permissions
export DUID=$(id -u)
# Gets current group ID for Docker container permissions
export DGID=$(id -g)

# Gets the physical path to the repository root directory
export REPO_PHYS_PATH="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"

# Storage Configuration
export NIM_CACHE_PATH="/home/user/customer-tco-computation-main/.cache"

# export LOCAL_NIM_CACHE="$(realpath ~/.cache/nim)"
export LOCAL_NIM_CACHE="/home/user/customer-tco-computation-main/.cache/nim"
echo "Info: NIM Model Profiles will be stored in: $LOCAL_NIM_CACHE"

# Create necessary directories
mkdir -p "$NIM_CACHE_PATH" 

# # If testing with a custom NIM_ENDPOINT, set the following:
# export NIM_ENDPOINT=https://multi-llm-tower-plus.xenon.lepton.run
# export NIM_ENDPOINT_TOKEN=tyITVPHBBdESnLz62IG9B86HrOKQk3gC
# # Remove trailing slash from NIM_ENDPOINT if present
# export NIM_ENDPOINT="${NIM_ENDPOINT%/}"

# if testing Profiles with Lora support, choose a directory to store the loras and uncomment the following:
# export LOCAL_PEFT_DIRECTORY="$(realpath ~/.cache/loras)"
# export NIM_PEFT_SOURCE="$(realpath ~/.cache/loras)"
# mkdir -p "$LOCAL_PEFT_DIRECTORY"

# To enable selection of a model profile not included in the original model_manifest.yaml:
# export NIM_MANIFEST_ALLOW_UNSAFE=1   
# export NIM_MODEL_NAME=<fill>  # path to the model directory or an NGC path.

# We use the default GenAI-Perf llama tokenizer to be able to compare models between each other for the same text
# https://docs.nvidia.com/deeplearning/triton-inference-server/user-guide/docs/perf_analyzer/genai-perf/README.html#tokenizer-str
export TOKENIZER_DIR=hf-internal-testing/llama-tokenizer