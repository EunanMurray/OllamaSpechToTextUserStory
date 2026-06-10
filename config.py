STT_MODEL = "base"
STT_DEVICE = "cpu"
STT_COMPUTE_TYPE = "int8"

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2"
OLLAMA_TIMEOUT = 120  # seconds per request
OLLAMA_KEEP_ALIVE = "30m"  # keep the model in RAM between requests (default is only 5m)

AUDIO_SAMPLE_RATE = 16000
AUDIO_CHANNELS = 1
AUDIO_DTYPE = "float32"

ENABLE_CLARIFICATION = True
MAX_CLARIFYING_QUESTIONS = 3
