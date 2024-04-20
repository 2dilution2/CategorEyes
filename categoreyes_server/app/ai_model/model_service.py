from transformers import CLIPModel, CLIPProcessor
from PIL import Image
import io

# 모델 초기화
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

def classify_image(image_bytes, labels):
    # 이미지를 로드하고 분류
    image = Image.open(io.BytesIO(image_bytes))
    inputs = processor(text=labels, images=image, return_tensors="pt", padding=True)
    outputs = model(**inputs)
    probs = outputs.logits_per_image.softmax(dim=1)
    best_label_idx = probs.argmax().item()
    return labels[best_label_idx]
