from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from typing import List
from PIL import Image
import io
from pathlib import Path
import zipfile
import torch
from transformers import CLIPProcessor, CLIPModel

app = FastAPI()

# 정적 파일 경로 추가
app.mount("/", StaticFiles(directory="static", html=True), name="static")

# CLIP 모델과 프로세서 로드
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

# 카테고리 라벨
labels = ["a photo of a person", "a landscape photo", "a photo of an animal", "a photo of food", "a photo of a document", "a photo of something else"]

# 폴더 생성
upload_dirs = ['사람', '풍경', '동물', '음식', '문서', '기타']
for upload_dir in upload_dirs:
    Path(f'./uploads/{upload_dir}').mkdir(parents=True, exist_ok=True)

@app.post("/upload-files/")
async def upload_files(files: List[UploadFile] = File(...)):
    for file in files:
        # 파일을 메모리에 로드
        image_data = await file.read()  # 이미지 데이터를 읽음

        # PIL 이미지로 변환
        image = Image.open(io.BytesIO(image_data))
        inputs = processor(text=labels, images=image, return_tensors="pt", padding=True)

        # 모델 실행
        outputs = model(**inputs)
        logits_per_image = outputs.logits_per_image
        probs = logits_per_image.softmax(dim=1)
        best_label_idx = probs.argmax().item()

        # 분류된 카테고리에 따라 폴더 경로 지정
        category = upload_dirs[best_label_idx]
        category_folder = Path(f'./uploads/{category}')
        category_folder.mkdir(parents=True, exist_ok=True)

        # 파일 저장 경로
        file_path = category_folder / file.filename

        # 파일 시스템에 저장
        with open(file_path, "wb") as buffer:
            buffer.write(image_data)  # 이미지 데이터를 파일에 저장

        # 파일 포인터를 초기화 (다른 처리를 위해)
        await file.seek(0)

    return {"message": "Files uploaded and classified successfully."}

@app.get("/download/{category_name}")
async def download_category(category_name: str):
    if category_name not in upload_dirs:
        raise HTTPException(status_code=404, detail="Category not found")

    # 분류된 카테고리 폴더 경로
    category_path = Path(f'./uploads/{category_name}')
    zip_path = Path(f'./downloads/{category_name}.zip')
    zip_path.parent.mkdir(parents=True, exist_ok=True)

    # 폴더를 ZIP 파일로 압축
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for file in category_path.iterdir():
            zipf.write(file, arcname=file.name)

    # ZIP 파일로 클라이언트에게 제공
    return FileResponse(zip_path, media_type='application/octet-stream', filename=f'{category_name}.zip')
