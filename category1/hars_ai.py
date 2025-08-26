from transformers import ViTForImageClassification, AutoFeatureExtractor
from PIL import Image
import torch
import os

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
real = 0 
fake = 0
for arquivo in os.listdir(diretorio):
    if arquivo.lower().endswith(".jpg"):
        count= count + 1
        # print(fake_or_real(diretorio + arquivo))
        if fake_or_real(diretorio + arquivo) == "Real":
            # print("Entrei")
            real= real + 1
        else:
            fake= fake + 1

print(count)
print(real)
print(fake)
