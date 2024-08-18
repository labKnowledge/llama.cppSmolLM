# Using the official llama.cpp server image as base
FROM ghcr.io/ggerganov/llama.cpp:server

# Installing Python and pip
RUN apt-get update && apt-get install -y python3 python3-pip && rm -rf /var/lib/apt/lists/*

# Installing huggingface_hub
RUN pip3 install --no-cache-dir huggingface_hub

# Setting a directory for the model
RUN mkdir -p /models && chmod 777 /models

# Creating a Python script to download the model
RUN echo "from huggingface_hub import hf_hub_download\n\
import shutil, os\n\
print('Starting model download...')\n\
model_path = hf_hub_download(repo_id='HuggingFaceTB/smollm-360M-instruct-add-basics-Q8_0-GGUF', \
filename='smollm-360m-instruct-add-basics-q8_0.gguf', cache_dir='/models')\n\
target_path = '/models/smollm-model.gguf'\n\
shutil.copy(model_path, target_path)\n\
if not os.path.exists(target_path):\n\
    raise FileNotFoundError(f'Model file not found at {target_path}')\n\
else:\n\
    print(f'Model file successfully copied to {target_path}')" > /download_model.py

# Executing the script to download the model
RUN python3 /download_model.py

# Setting the working directory
WORKDIR /models

# Creating a startup script
RUN echo '#!/bin/bash\n\
/llama-server -m /models/smollm-model.gguf --port 8080 --host 0.0.0.0 -n 512 "$@"' > /start.sh && \
    chmod +x /start.sh

# Setting the entrypoint to our startup script
ENTRYPOINT ["/start.sh"]