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
    print(f'Model file successfully copied to {target_path}')" > /app/download_model.py


# Copying the system monitoring script
COPY system_monitor.py /app/system_monitor.py

# Executing the script to download the model
RUN python3 /app/download_model.py

# Creating a startup script
RUN echo '#!/bin/bash\n\
python3 /app/system_monitor.py &\n\
/llama-server -m /models/Phi-3.5-mini-instruct-IQ3_M.gguf --port 8080 --host 0.0.0.0 -n 512 "$@"' > /start.sh && \
    chmod +x /start.sh

# Setting the working directory
WORKDIR /app

# Exposing ports for llama.cpp server and monitoring UI
EXPOSE 8080 5000

# Setting the entrypoint to our startup script
ENTRYPOINT ["/start.sh"]