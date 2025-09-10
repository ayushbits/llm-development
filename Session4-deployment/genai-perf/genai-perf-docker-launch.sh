source ./common_env.sh

if [ -z "$NIM_MODEL_PROFILE" ]; then
    echo "ERROR: NIM_MODEL_PROFILE was not set. The default profile for this GPU configuration was probably used." 
    echo "Please set NIM_MODEL_PROFILE in ./common_env.sh to the value which is printed in the NIM container. Look for the following:"
    echo "Selected profile: ac34857fyyyd174ad524974248fqqqf271bd2a0355643b2cfbbb0d0fe778aaa (tensorrt_llm-a100-bf16-tp4-pp1-throughput)"
    echo "And then set NIM_MODEL_PROFILE='tensorrt_llm-a100-bf16-tp4-pp1-throughput'"
    exit 1
fi
export IMG_NAME=nvcr.io/nvidia/tritonserver:25.06-py3-sdk # note the SDK postfix

docker run -it --rm \
--name=genai-perf \
--shm-size=16GB \
--link $NIM_CONTAINER_NAME \
--user $DUID:$DGID \
-e NIM_CONTAINER_NAME \
-e NIM_MODEL_PROFILE \
-v $REPO_PHYS_PATH:/ext/repo/ \
-w /ext/repo/ \
$IMG_NAME \
./sweep-genai-perf.sh