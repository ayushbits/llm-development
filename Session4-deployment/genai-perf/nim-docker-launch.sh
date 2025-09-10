source ./common_env.sh

# Prerequisites Check
if ! command -v nvidia-smi &> /dev/null; then
    echo "ERROR: NVIDIA Driver not found. Please install NVIDIA Container Runtime"
    exit 1
fi

if [ -z "$NGC_API_KEY" ]; then
    echo "WARNING: NGC_API_KEY not set. If the container/model profile has not been downloaded yet, " 
    echo "the following command might fail. If so, please export NGC_API_KEY=<your_key>. "
    echo "Get your key from: https://ngc.nvidia.com/setup/api-key"
    echo ""
fi

if [ -z "$NIM_MODEL_PROFILE" ]; then
    echo "WARNING: NIM_MODEL_PROFILE not set. The default profile for this GPU configuration will be used. " 
    echo "When benchmarking, please set NIM_MODEL_PROFILE to the value which is printed in the NIM container. If not, it will default to the profile for the underlying GPU"
    echo ""
fi

# Set default values for optional variables
export NIM_PEFT_REFRESH_INTERVAL=${NIM_PEFT_REFRESH_INTERVAL:-3600}
export NIM_DISABLE_LOG_REQUESTS=${NIM_DISABLE_LOG_REQUESTS:-1}
export NIM_LOG_LEVEL=${NIM_LOG_LEVEL:-INFO}

docker run -it --rm \
--name="$NIM_CONTAINER_NAME" \
--runtime=nvidia \
--gpus all \
--shm-size=16GB \
--user "$DUID:$DGID" \
-e NGC_API_KEY \
-e NIM_CACHE_PATH \
-e NIM_DISABLE_LOG_REQUESTS \
-e NIM_LOG_LEVEL \
-e NIM_MODEL_PROFILE \
-e NIM_MANIFEST_ALLOW_UNSAFE \
-e NIM_MODEL_NAME \
-e NIM_MAX_MODEL_LEN \
-e NIM_PEFT_SOURCE \
-e LOCAL_PEFT_DIRECTORY \
-v "$LOCAL_NIM_CACHE:$NIM_CACHE_PATH" \
-p 8000:8000 \
"$NIM_IMG_NAME"
# list-model-profiles  # uncomment in order to get full list of model profiles for this NIM