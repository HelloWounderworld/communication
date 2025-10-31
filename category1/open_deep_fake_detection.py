import gradio as gr
from transformers import AutoImageProcessor, SiglipForImageClassification
from PIL import Image
import torch

# Load model and processor
# model_name = "prithivMLmods/open-deepfake-detection"  # Updated model name
model_name = "./../../models/pretrained/models--prithivMLmods--open-deepfake-detection/snapshots/e85fa6022fbc0223396f5b19f5ad4612ba31e142"
# model_name = "./../../models/pretrained/models--shivani1511--deepfake-image-detector-new-v2/snapshots/5ca54670d6d61860ce93fa846ec922c8d2817ecf"  # Updated model name
  # Updated model name
model = SiglipForImageClassification.from_pretrained(model_name)
processor = AutoImageProcessor.from_pretrained(model_name)

# # Carregue uma imagem manualmente
# image_path = "./../../data/data_movies_processed/test/fake/easy_1_1110.jpg"
# image = Image.open(image_path).convert("RGB")

# inputs = processor(images=image, return_tensors="pt")

# with torch.no_grad():
#     outputs = model(**inputs)
#     logits = outputs.logits
#     probs = torch.nn.functional.softmax(logits, dim=1)

# print("Logits:", logits)
# print("Probabilidades:", probs)

# Updated label mapping
id2label = {
    "0": "Fake",
    "1": "Real"
}

def classify_image(image):
    print("Received image:", type(image), image.shape)
    image = Image.fromarray(image).convert("RGB")
    inputs = processor(images=image, return_tensors="pt")

    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        probs = torch.nn.functional.softmax(logits, dim=1).squeeze().tolist()
        # probs = torch.nn.functional.softmax(logits, dim=1).squeeze()

    prediction = {
        id2label[str(i)]: round(probs[i], 3) for i in range(len(probs))
    }

    return prediction

    # return [(id2label[str(i)], round(probs[i], 3)) for i in range(len(probs))]

    # print(f"probs type: {type(probs)}, value: {probs}")

    # # Garantir que probs é iterável (lista ou tensor com mais de 1 elemento)
    # if isinstance(probs, float) or isinstance(probs, int):
    #     # Só uma classe, retorna lista com um item só
    #     probs = [probs]
    # elif torch.is_tensor(probs):
    #     probs = probs.tolist()

    # result = [(id2label[str(i)], round(probs[i], 3)) for i in range(len(probs))]
    # print("Result:", result)
    # return result

    # if torch.is_tensor(probs):
    #     probs = probs.tolist()

    # result = [(id2label[str(i)], round(probs[i], 3)) for i in range(len(probs))]
    # print("Returning result:", result)
    # return str(result)

# Gradio Interface
iface = gr.Interface(
    fn=classify_image,
    inputs=gr.Image(type="numpy"),
    outputs=gr.Label(num_top_classes=2, label="Deepfake Detection"),
    # outputs=gr.Label(label="Deepfake Detection"),
    # outputs=gr.JSON(),
    # outputs=gr.Textbox(label="Resultado"),
    title="open-deepfake-detection",
    description="Upload an image to detect whether it is AI-generated (Fake) or a real photograph (Real), using the OpenDeepfake-Preview dataset."
)

# iface = gr.Interface(
#     fn=classify_image,
#     inputs=gr.Image(type="numpy"),
#     outputs="text",  # ou gr.Textbox()
#     title="Teste Gradio",
#     description="Apenas testando se o Gradio renderiza."
# )

if __name__ == "__main__":
    iface.launch(server_name="0.0.0.0", server_port=7860, share=False)
    # iface.launch(server_port=7860, debug=True)
