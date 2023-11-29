import os
from aiohttp import ClientError
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, Request
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from typing import List
from PIL import Image
import io
import zipfile
from transformers import CLIPProcessor, CLIPModel
from boto3.dynamodb.conditions import Attr
from dotenv import load_dotenv
import requests
import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime, timedelta
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
import uuid
from base64 import b64encode

load_dotenv()  # .env 파일에서 환경 변수들을 로드합니다.

templates = Jinja2Templates(directory="templates")
templates.env.filters['b64encode'] = lambda x: b64encode(x).decode()

app = FastAPI()

# 정적 파일 경로 추가
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# AWS S3 클라이언트 초기화
s3_client = boto3.client('s3')

# DynamoDB 리소스 초기화
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('categoreyes')

# CLIP 모델과 프로세서 로드
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

# 카테고리 라벨
labels = ["a photo of a person", "a landscape photo", "a photo of an animal", "a photo of food", "a photo of a document", "a photo of something else"]

# SessionMiddlewareKey 환경 변수 불러오기
SESSION_KEY = os.getenv("SessionMiddlewareKey")
S3_BUCKET = os.getenv("S3_BUCKET")

# 세션 미들웨어 추가
app.add_middleware(SessionMiddleware, secret_key=SESSION_KEY)


# 파일을 S3에 업로드하는 함수
def upload_file_to_s3(file_stream, bucket, object_name):
    try:
        s3_client.upload_fileobj(file_stream, bucket, object_name)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Failed to upload to S3")

def generate_session_id():
    # uuid4 함수는 랜덤한 UUID를 생성합니다.
    session_id = uuid.uuid4()
    # 생성된 UUID를 문자열로 변환하여 반환합니다.
    return str(session_id)

# DynamoDB에 데이터 저장
def save_url_to_dynamodb(request: Request, url, filename, category):
    try:
        session_id = request.session.get("session_id")
        if not session_id:
            session_id = generate_session_id()  # 세션 ID 생성
            request.session["session_id"] = session_id

        current_time = datetime.now().isoformat()
        expiration_time = int((datetime.now() + timedelta(days=3)).timestamp())

        table.put_item(
            Item={
                'sessionID': session_id,
                'UploadDate': current_time,
                'Filename': filename,
                'URL': url,
                'Category': category,
                'ExpirationTime': expiration_time
            }
        )
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Failed to save to DynamoDB")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    # 메인 페이지를 렌더링합니다.
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload")
async def upload_files(request: Request, files: List[UploadFile] = File(...)):
    urls = []
    # 세션 ID 생성 또는 기존 세션 ID 가져오기
    session_id = request.session.get("session_id", generate_session_id())
    request.session["session_id"] = session_id

    for file in files:
        image_data = await file.read()
        image = Image.open(io.BytesIO(image_data))
        inputs = processor(text=labels, images=image, return_tensors="pt", padding=True)

        outputs = model(**inputs)
        logits_per_image = outputs.logits_per_image
        probs = logits_per_image.softmax(dim=1)
        best_label_idx = probs.argmax().item()
        category = labels[best_label_idx]

        object_name = f"{category}/{file.filename}"
        upload_file_to_s3(io.BytesIO(image_data), S3_BUCKET, object_name)

        file_url = f"https://{S3_BUCKET}.s3.amazonaws.com/{object_name}"
        urls.append(file_url)

        # 파일 정보를 DynamoDB에 저장하는 부분
        save_url_to_dynamodb(request, file_url, file.filename, category)

    # 세션 ID를 포함하여 응답 반환
    return {"message": "Files uploaded successfully.", "session_id": session_id, "urls": urls}


def get_images_by_session_id(session_id: str):
    # DynamoDB에서 세션 ID에 맞는 이미지들을 조회
    try:
        response = table.query(
            IndexName="sessionID-index",  # 세션 ID를 기반으로 한 GSI(Global Secondary Index)가 필요합니다.
            KeyConditionExpression=Key('sessionID').eq(session_id)
        )
        return [item['URL'] for item in response['Items']]
    except ClientError as e:
        print(e.response['Error']['Message'])
        return []

@app.get("/uploaded_images/{session_id}", response_class=HTMLResponse)
async def uploaded_images(request: Request, session_id: str):
    # 세션 ID를 기반으로 업로드된 이미지들을 가져옵니다.
    # uploaded_images_urls = get_images_by_session_id(session_id)
    uploaded_images_urls = 'https://{S3_BUCKET}.s3.amazonaws.com/thinktank.png'

    # 업로드된 이미지가 없는 경우 기본 이미지를 표시
    if not uploaded_images_urls:
        uploaded_images_urls = ["static/img/default.jpg"]

    # 템플릿에 이미지 URL 리스트를 전달
    return templates.TemplateResponse("uploaded_images.html", {
        "request": request,
        "uploaded_images_urls": uploaded_images_urls,
        "session_id": session_id
    })

@app.get("/categories/{session_id}", response_class=HTMLResponse)
async def get_categories(request: Request, session_id: str):
    categories_info = {}
    for category in labels:
        response = table.scan(
            FilterExpression=Attr('Category').eq(category) & Attr('sessionID').eq(session_id)
        )
        items = response.get('Items', [])
        if items:
            representative_image = items[0]['URL']
            categories_info[category] = representative_image

    return templates.TemplateResponse("categories.html", {
        "request": request,
        "categories_info": categories_info,
        "session_id": session_id
    })

@app.get("/download/{category_name}")
async def download_category(category_name: str):
    response = table.scan(FilterExpression=Attr('Category').eq(category_name))
    items = response.get('Items', [])
    zip_filename = f"{category_name}.zip"

    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        for item in items:
            url = item['URL']
            response = requests.get(url)
            if response.status_code == 200:
                image_filename = url.split("/")[-1]
                zipf.writestr(image_filename, response.content)

    return StreamingResponse(open(zip_filename, 'rb'), media_type="application/zip")

@app.get("/category_images/{category_name}/{session_id}", response_class=HTMLResponse)
async def get_category_images(request: Request, category_name: str, session_id: str):
    response = table.scan(
        FilterExpression=Attr('Category').eq(category_name) & Attr('sessionID').eq(session_id)
    )
    items = response.get('Items', [])
    images = [item['URL'] for item in items]

    return templates.TemplateResponse("category_images.html", {
        "request": request,
        "category_name": category_name,
        "images": images,
        "session_id": session_id
    })
