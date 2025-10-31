import cv2
import os
import torch
from PIL import Image
from transformers import AutoImageProcessor, TimesformerForVideoClassification
from tqdm import tqdm

# ====== CONFIGURAÇÕES ======
video_path = "./sample.mp4"
output_dir = "./frames"
model_name = "HyperMoon/wav2vec2-base-960h-finetuned-deepfake"
frame_interval = 5  # captura 1 frame a cada 10

# ====== ETAPA 1: Extração de frames ======
os.makedirs(output_dir, exist_ok=True)
cap = cv2.VideoCapture(video_path)
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

print("Extraindo frames...")
frame_count = 0
saved_frames = []
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    if frame_count % frame_interval == 0:
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_pil = Image.fromarray(frame_rgb)
        frame_path = os.path.join(output_dir, f"frame_{frame_count:05d}.jpg")
        frame_pil.save(frame_path)
        saved_frames.append(frame_path)
    frame_count += 1
cap.release()

print(f"Total de frames salvos: {len(saved_frames)}")

# ====== ETAPA 2: Carregar modelo ======
device = "cuda" if torch.cuda.is_available() else "cpu"
extractor = AutoImageProcessor.from_pretrained(model_name)
model = TimesformerForVideoClassification.from_pretrained(model_name).to(device)

# ====== ETAPA 3: Classificar os frames ======
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

# ====== ETAPA 4: Resultado final ======
print("\n===== RESULTADO FINAL =====")
print(f"Frames classificados como REAL: {real_count}")
print(f"Frames classificados como FAKE: {fake_count}")

if fake_count > real_count:
    print("🎯 O vídeo provavelmente é FALSO.")
else:
    print("✅ O vídeo provavelmente é REAL.")
