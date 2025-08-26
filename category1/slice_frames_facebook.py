import torch
from PIL import Image
from transformers import AutoFeatureExtractor, AutoModelForImageClassification
from tqdm import tqdm
import os

# ====== CONFIGURAÇÕES ======
output_dir = "./../../data_preparation/frames/"
model_name = "facebook/timesformer-base-finetuned-k400"
saved_frames = [
    os.path.join(output_dir, fname)
    for fname in os.listdir(output_dir)
    if fname.lower().endswith((".jpg", ".jpeg", ".png"))
]

# ====== ETAPA 1: Carregar modelo ======
device = "cuda" if torch.cuda.is_available() else "cpu"
extractor = AutoFeatureExtractor.from_pretrained(model_name)
model = AutoModelForImageClassification.from_pretrained(model_name).to(device)

# ====== ETAPA 2: Classificar os frames ======
real_count, fake_count = 0, 0
print("Classificando frames...")
for frame_path in tqdm(saved_frames):
    image = Image.open(frame_path).convert("RGB")
    inputs = extractor(images=image, return_tensors="pt").to(device)

    with torch.no_grad():
        logits = model(**inputs).logits
        probs = torch.nn.functional.softmax(logits, dim=1)
        pred = torch.argmax(probs, dim=1).item()

    # Assumindo label 0 = Fake, 1 = Real (verifique id2label do modelo)
    if pred == 1:
        real_count += 1
    else:
        fake_count += 1

# ====== ETAPA 3: Resultado final ======
print("\n===== RESULTADO FINAL =====")
print(f"Frames classificados como REAL: {real_count}")
print(f"Frames classificados como FAKE: {fake_count}")

if fake_count > real_count:
    print("🎯 O vídeo provavelmente é FALSO.")
else:
    print("✅ O vídeo provavelmente é REAL.")
