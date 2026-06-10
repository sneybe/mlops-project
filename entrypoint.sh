#!/bin/bash
MODEL_PATH=$(python3 -c "
import glob
models = glob.glob('/app/mlruns/1/models/*/artifacts')
if models:
    print(sorted(models)[-1])
")
echo "Using model: $MODEL_PATH"
mlflow models serve -m "$MODEL_PATH" --host 0.0.0.0 --port 5001 --no-conda
