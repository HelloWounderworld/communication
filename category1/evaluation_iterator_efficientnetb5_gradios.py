from transformers import AutoImageProcessor, AutoModelForImageClassification
from PIL import Image
import torch
import os
import pandas as pd

# Load model and processor
model_name = "google/efficientnet-b7"
# model_name = "google/efficientnet-b6"
# model_name = "google/efficientnet-b5"
# model_name = "google/efficientnet-b4"
# model_name = "google/efficientnet-b3"
# model_name = "google/efficientnet-b2"
# model_name = "google/efficientnet-b1"
# model_name = "google/efficientnet-b0"
model = AutoModelForImageClassification.from_pretrained(model_name)
processor = AutoImageProcessor.from_pretrained(model_name)

diretorio = "./../../data_preparation/frames/"
saida_excel = "resultados_classificacao.xlsx"

id2label = {
    "0": "Fake",
    "1": "Real"
}

def classify_image(path):
    image = Image.open(path).convert("RGB")
    inputs = processor(images=image, return_tensors="pt")

    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        probs = torch.nn.functional.softmax(logits, dim=1).squeeze().tolist()

    prediction = {
        id2label[str(i)]: round(probs[i], 3) for i in range(len(probs))
    }

    return prediction

# === Loop sobre as imagens e coleta resultados ===
resultados = []
total_fake = 0
total_real = 0
num_frames = 0

for arquivo in os.listdir(diretorio):
    if arquivo.lower().endswith(".jpg"):
        classificacao = classify_image(os.path.join(diretorio, arquivo))
        print(f"{arquivo}: {classificacao}")
        
        prob_fake = classificacao["Fake"]
        prob_real = classificacao["Real"]
        
        resultados.append({
            "arquivo": arquivo,
            "prob_fake": prob_fake,
            "prob_real": prob_real,
            "real_or_fake": "Fake" if prob_fake >= prob_real else "Real"
        })

        total_fake += prob_fake
        total_real += prob_real
        num_frames += 1

# === Cálculo da média final ===
media_fake = total_fake / num_frames if num_frames > 0 else 0
media_real = total_real / num_frames if num_frames > 0 else 0

print("\n=== Resultado final do vídeo ===")
print(f"Média probabilidade Fake: {media_fake:.3f}")
print(f"Média probabilidade Real: {media_real:.3f}")
conclusao = "Fake" if media_fake >= media_real else "Real"
print(f"🎬 Conclusão: O vídeo é considerado **{conclusao}** com base na média dos frames.")

# === Salva em Excel ===
df = pd.DataFrame(resultados)
df.to_excel(saida_excel, index=False)
print(f"\nResultados salvos em: {saida_excel}")
