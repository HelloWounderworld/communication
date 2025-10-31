# 📰 TituladorGPT — The Official Headline AI of the 21st Century

*“If the news is good, it makes it shine. If it’s bad, it makes up a better headline!”*

---

## 🤖 Introduction

**TituladorGPT** is an artificial intelligence system specialized in the **creative generation of journalistic headlines**. Whether for serious reports, sensational stories, or satirical pieces, it crafts attention-grabbing headlines — like a real newsroom editor running on pure coffee.

The goal of this project is to automate and accelerate the process of headline creation with editorial quality, linguistic fluency, and communicative impact, using state-of-the-art language models.

---

## 🧠 Model Used

* 🔷 **Current model:** [LLaMA 3](https://huggingface.co/meta-llama)
* 🔮 **Next step:** Integration with [**LLaMA 4**](https://ai.meta.com/llama/) (in development or pending release)

LLaMA (Large Language Model Meta AI) is one of the most advanced models for natural language understanding and generation, making it ideal for creative tasks such as headline writing.

---

## 🛠️ Development Environment

The project environment is fully containerized to ensure **reproducibility, portability, and scalability**.

### 🐳 Technologies used:

* **Docker**: portable and isolated infrastructure
* **Docker Compose**: service orchestration (model, API, etc.)
* **Python 3.13.4** with the following core libraries:

```txt
transformers
peft
bitsandbytes
datasets
scikit-learn
accelerate
trl
pandas
```

> The environment also supports GPU usage with CUDA/cuBLAS/cuDNN for accelerated training.

---

## 🧪 Fine-Tuning Method

To adapt LLaMA-3 specifically for the headline generation task, I used the method:

### 🔧 `qLoRA` (Quantized Low-Rank Adaptation)

* Enables fine-tuning of large models with **low memory cost**
* Uses 4-bit quantization to reduce computational footprint
* Ideal for training on GPUs with limited VRAM

### 📌 Future explorations:

I plan to experiment with additional fine-tuning strategies, including:

* 🔹 `LoRA` (Low-Rank Adaptation)
* 🔹 `Transformer Acceleration` (Fine-tuning Using Transformer Acceleration)
* 🔹 `Full Fine-Tuning` (updating all model weights)
* 🔹 `Adapter Tuning`
* 🔹 `Prompt Tuning` or `Prefix Tuning`

These methods will be evaluated based on computational cost, performance, and application flexibility.

---

## 🚧 Current Progress

* ✅ Dataset with real and creative headlines collected from journalistic sources
* ✅ Initial fine-tuning using qLoRA on LLaMA-3
* 🛠️ In development: automatic quality evaluation of generated headlines (BLEU, ROUGE, human metrics)
* 💡 Planned: web interface (Streamlit or FastAPI) to generate headlines via textarea

---

## 📦 How to Run the Project (preview)

```bash
# Build the image
docker build -t tituladorgpt .

# Run container
docker run --gpus all -p 7860:7860 tituladorgpt
```

---

## 📑 Input and Output Examples

**🔍 Input:**

> Text: "The government announced today a new economic stimulus package..."

**🧠 AI responds:**

> "Government Pulls a Rabbit Out of the Hat and Injects Billions into the Economy"

---

## 👨‍🔬 Author & Contact

Developed by **\[Your Name]**, an enthusiastic researcher at the intersection of **journalism, natural language, and AI**.

📫 Contact: \[[your-email@example.com](mailto:your-email@example.com)]

---

## ⚖️ License

MIT — feel free to use, remix, and create your own absurd AI-generated headlines.
