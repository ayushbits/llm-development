source ./common_env.sh

NIM_ENDPOINT=${NIM_ENDPOINT:-"$NIM_CONTAINER_NAME:8000"}

# Use this to get the first model, if needed:
MODEL=$(curl -Ns -X "GET" $NIM_ENDPOINT'/v1/models' -H "Authorization: Bearer $NIM_ENDPOINT_TOKEN"  | jq -r '.data[0].id')
# MODEL="meta/llama-3.1-8b-base"

if [[ -z "$MODEL" ]]; then
    echo "Error: MODEL is not set or is an empty string." >&2
    exit 1
else
    echo "Model: $MODEL"
fi

REPO_LOCAL_PATH="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"

DATESTR=$(date +'%Y-%m-%d_%H.%M.%S')
TMP_GENAI_PERF_ARTIFACTS=/tmp/genai-perf-artifacts/model-${MODEL//\//-}/profile-$NIM_MODEL_PROFILE/$DATESTR
FINAL_GENAI_PERF_ARTIFACTS=$REPO_LOCAL_PATH/genai-perf-artifacts/model-${MODEL//\//-}/profile-$NIM_MODEL_PROFILE/
export HF_HOME=/tmp


declare -A useCases

# Populate the array with use case descriptions and their specified input/output lengths
useCases["Translation"]="200/200"
useCases["PageSummary"]="512/128"
# useCases["Some RAG"]="4000/700"
# useCases["Text classification"]="200/5"
# useCases["Text summary"]="2000/200"

runBenchmark() {
    local description="$1"
    local lengths="${useCases[$description]}"
    IFS='/' read -r inputLength outputLength <<< "$lengths"

    echo "Info: Running GenAI-Perf for $MODEL: $description use case, with input length $inputLength and output length $outputLength"
    
    # Define the concurrency levels and corresponding measurement intervals
    CONCURRENCIES=(1 2 5 25 50) 

    # Loop over the indices of the concurrency array
    for i in "${!CONCURRENCIES[@]}"; do
        local CONCURRENCY=${CONCURRENCIES[$i]}
        local MEASUREMENT_INTERVAL=${MEASUREMENT_INTERVALS[$i]}
        
        local INPUT_SEQUENCE_LENGTH=$inputLength
        local INPUT_SEQUENCE_STD=0
        local OUTPUT_SEQUENCE_LENGTH=$outputLength

        genai-perf profile \
            -m $MODEL \
            --endpoint-type chat \
            --streaming \
            -u $NIM_ENDPOINT \
            --synthetic-input-tokens-mean $INPUT_SEQUENCE_LENGTH \
            --synthetic-input-tokens-stddev $INPUT_SEQUENCE_STD \
            --warmup-request-count $CONCURRENCY \
            --concurrency $CONCURRENCY \
            --output-tokens-mean $OUTPUT_SEQUENCE_LENGTH \
            --extra-inputs max_tokens:$OUTPUT_SEQUENCE_LENGTH \
            --extra-inputs min_tokens:$OUTPUT_SEQUENCE_LENGTH \
            --extra-inputs ignore_eos:true \
            `#  structured generation example ` \
            `# --extra-inputs '{"nvext": {"guided_json": {"type": "object", "properties": { "text": { "type": "string" } }, "required" : [ "text" ] } } }' ` \
            --tokenizer $TOKENIZER_DIR \
            --artifact-dir $TMP_GENAI_PERF_ARTIFACTS/concurrency-$CONCURRENCY \
            --profile-export-file ${INPUT_SEQUENCE_LENGTH}_${OUTPUT_SEQUENCE_LENGTH}.json \
            --generate-plots \
            --request-count $((10 * CONCURRENCY)) \
            -- \
            -v \
            -H "Authorization: Bearer $NIM_ENDPOINT_TOKEN" \
            --max-threads=256 \
            `# adding --max-trials=1 doesn't speed up the things any further`

        mkdir -p $FINAL_GENAI_PERF_ARTIFACTS
        cp -r $TMP_GENAI_PERF_ARTIFACTS $FINAL_GENAI_PERF_ARTIFACTS

    done
}

# Iterate over all defined use cases and run the benchmark script for each
for description in "${!useCases[@]}"; do
    runBenchmark "$description"
done