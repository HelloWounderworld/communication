from transformers import ViTForImageClassification, AutoFeatureExtractor
from PIL import Image
import torch
import os
import json

model_name = "harshai-a/HarsAI"
model_extractor = "google/vit-base-patch16-224-in21k"
model = ViTForImageClassification.from_pretrained(model_name)
feature_extractor = AutoFeatureExtractor.from_pretrained(model_extractor)

diretorio = "./../../data_preparation/frames"

def fake_or_real(path):
    image = Image.open(path).convert("RGB")
    inputs = feature_extractor(images=image, return_tensors="pt")
    with torch.no_grad():
        outputs = model(**inputs)
        prediction = outputs.logits.argmax(-1).item()
    return "Real" if prediction == 0 else "Fake"

count = 0
real_model = 0
fake_model = 0
real_true = 0
fake_true = 0

for arquivo in os.listdir(diretorio):
    if arquivo.lower().endswith(".png"):
        count += 1
        caminho_png = os.path.join(diretorio, arquivo)
        resultado_modelo = fake_or_real(caminho_png)

        # Carregar o JSON correspondente
        nome_base = os.path.splitext(arquivo)[0]
        caminho_json = os.path.join(diretorio, f"{nome_base}.json")
        with open(caminho_json, "r", encoding="utf-8") as f:
            dados = json.load(f)
        
        # Supomos que o campo com o booleano se chama "is_fake"
        resultado_real = "Fake" if dados.get("is_fake", False) else "Real"

        print(f"{arquivo} | Modelo: {resultado_modelo} | Real: {resultado_real}")

        # Contagem
        if resultado_modelo == "Real":
            real_model += 1
        else:
            fake_model += 1

        if resultado_real == "Real":
            real_true += 1
        else:
            fake_true += 1

print("Total de imagens:", count)
print("Modelo - Real:", real_model, "Fake:", fake_model)
print("Ground Truth - Real:", real_true, "Fake:", fake_true)
