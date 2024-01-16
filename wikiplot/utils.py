import torch
from bash import bash

import time
from datetime import timedelta


class Timer(object):
    """Timer object used to time things

    Based on: https://realpython.com/python-timer/#creating-a-python-timer-context
               -manager
    """

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, *exception_info):
        self.end = time.perf_counter()
        self.duration = timedelta(seconds=self.end - self.start)
        self.duration_minutes = self.duration.seconds / 60
        self.duration_hours = self.duration.seconds / 3600

class GPUStatistics(object):
    """Based on: https://huggingface.co/datasets/unsloth/notebooks/blob/main/Alpaca_%2B_Mistral_7b_full_example.ipynb
    """

    def __enter__(self):
        gpu_stats = torch.cuda.get_device_properties(0)
        self.start_gpu_memory = round(torch.cuda.max_memory_reserved() / 1024 / 1024 / 1024, 3)
        self.max_memory = round(gpu_stats.total_memory / 1024 / 1024 / 1024, 3)
        print(f"GPU = {gpu_stats.name}. Max memory = {self.max_memory} GB.")
        print(f"{self.start_gpu_memory} GB of memory reserved.")
        return self

    def __exit__(self, *exception_info):
        used_memory = round(torch.cuda.max_memory_reserved() / 1024 / 1024 / 1024, 3)
        used_memory_for_lora = round(used_memory - self.start_gpu_memory, 3)
        used_percentage = round(used_memory / self.max_memory * 100, 3)
        lora_percentage = round(used_memory_for_lora / self.max_memory * 100, 3)
        print(f"Peak reserved memory = {used_memory} GB.")
        print(f"Peak reserved memory for training = {used_memory_for_lora} GB.")
        print(f"Peak reserved memory % of max memory = {used_percentage} %.")
        print(f"Peak reserved memory for training % of max memory = {lora_percentage} %.")


def print_trainer_stats(trainer_stats):
    # From: https://huggingface.co/datasets/unsloth/notebooks/blob/main/Alpaca_%2B_Mistral_7b_full_example.ipynb
    print(f"{trainer_stats.metrics['train_runtime']} seconds used for training.")
    print(f"{round(trainer_stats.metrics['train_runtime']/60, 2)} minutes used for training.")


def quantize_to_gguf(modal_storage_dir, save_directory="artifacts", quantization_method = "q4_k_m"):
    print("TODO maybe replace this with https://twitter.com/maximelabonne/status/1746812715606348138")
    # From: https://huggingface.co/datasets/unsloth/notebooks/blob/main/Alpaca_%2B_Mistral_7b_full_example.ipynb
    #    it appears this is based on: https://github.com/ggerganov/llama.cpp#prepare-data--run
    from transformers.models.llama.modeling_llama import logger
    import os

    logger.warning_once(
        "Unsloth: `colab_quantize_to_gguf` is still in development mode.\n"\
        "If anything errors or breaks, please file a ticket on Github.\n"\
        "Also, if you used this successfully, please tell us on Discord!"
    )

    # From https://mlabonne.github.io/blog/posts/Quantize_Llama_2_models_using_ggml.html
    ALLOWED_QUANTS = \
    {
        "q2_k"   : "Uses Q4_K for the attention.vw and feed_forward.w2 tensors, Q2_K for the other tensors.",
        "q3_k_l" : "Uses Q5_K for the attention.wv, attention.wo, and feed_forward.w2 tensors, else Q3_K",
        "q3_k_m" : "Uses Q4_K for the attention.wv, attention.wo, and feed_forward.w2 tensors, else Q3_K",
        "q3_k_s" : "Uses Q3_K for all tensors",
        "q4_0"   : "Original quant method, 4-bit.",
        "q4_1"   : "Higher accuracy than q4_0 but not as high as q5_0. However has quicker inference than q5 models.",
        "q4_k_m" : "Uses Q6_K for half of the attention.wv and feed_forward.w2 tensors, else Q4_K",
        "q4_k_s" : "Uses Q4_K for all tensors",
        "q5_0"   : "Higher accuracy, higher resource usage and slower inference.",
        "q5_1"   : "Even higher accuracy, resource usage and slower inference.",
        "q5_k_m" : "Uses Q6_K for half of the attention.wv and feed_forward.w2 tensors, else Q5_K",
        "q5_k_s" : "Uses Q5_K for all tensors",
        "q6_k"   : "Uses Q8_K for all tensors",
        "q8_0"   : "Almost indistinguishable from float16. High resource use and slow. Not recommended for most users.",
    }

    if quantization_method not in ALLOWED_QUANTS.keys():
        error = f"Unsloth: Quant method = [{quantization_method}] not supported. Choose from below:\n"
        for key, value in ALLOWED_QUANTS.items():
            error += f"[{key}] => {value}\n"
        raise RuntimeError(error)

    print_info = \
        f"==((====))==  Unsloth: Conversion from QLoRA to GGUF information\n"\
        f"   \\\   /|    [0] Installing llama.cpp will take 3 minutes.\n"\
        f"O^O/ \_/ \\    [1] Converting HF to GUUF 16bits will take 3 minutes.\n"\
        f"\        /    [2] Converting GGUF 16bits to q4_k_m will take 20 minutes.\n"\
        f' "-____-"     In total, you will have to wait around 26 minutes.\n'
    print(print_info)

    if not os.path.exists("llama.cpp"):
        print("Unsloth: [0] Installing llama.cpp. This will take 3 minutes...")
        bash("git clone https://github.com/ggerganov/llama.cpp")
        bash("cd llama.cpp && make clean && LLAMA_CUBLAS=1 make -j")

    print("Unsloth: [1] Converting HF into GGUF 16bit. This will take 3 minutes...")
    bash(f"python llama.cpp/convert.py {save_directory} \
        --outfile {save_directory}-unsloth.gguf \
        --outtype f16")

    print("Unsloth: [2] Converting GGUF 16bit into q4_k_m. This will take 20 minutes...")
    final_location = f"./{save_directory}-{quantization_method}-unsloth.gguf"
    bash(f"./llama.cpp/quantize ./{save_directory}-unsloth.gguf \
        {final_location} {quantization_method}")

    print(f"Unsloth: Output location: {final_location}")
    bash(f"cp -r ./{save_directory} {modal_storage_dir}")
