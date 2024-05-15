from ai_model.model_service import classify_image
import os
from aiohttp import ClientError
from fastapi import FastAPI, File, HTTPException, UploadFile, Request
from typing import List
import io
import zipfile
from dotenv import load_dotenv
import requests
import boto3
from boto3.dynamodb.conditions import Key, Attr
from datetime import datetime, timedelta
from starlette.middleware.sessions import SessionMiddleware
import uuid

load_dotenv()  # .env 파일에서 환경 변수들을 로드합니다.

app = FastAPI()

def format_category_name(category: str) -> str:
    return category.replace('_', ' ')  # 밑줄을 공백으로 변환

# CORS 활성화
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 도메인에서의 요청 허용
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메소드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('categoreyes')
SESSION_KEY = os.getenv("SessionMiddlewareKey")
S3_BUCKET = os.getenv("S3_BUCKET")
app.add_middleware(SessionMiddleware, secret_key=SESSION_KEY)
labels = ["a photo of a human", "a landscape photo", "a photo of an animal", "a photo of food", "a photo of a document", "a photo of something else"]

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

@app.get("/")
def get_main_page():
    return {"message": "메인페이지"}

@app.post("/upload")
async def upload_files(request: Request, files: List[UploadFile] = File(...)):
    urls = []
    # 세션 ID 생성 또는 기존 세션 ID 가져오기
    session_id = request.session.get("session_id", generate_session_id())
    request.session["session_id"] = session_id
    
    for file in files:
        image_data = await file.read()
        category = classify_image(image_data, labels)
        object_name = f"{category}/{file.filename}"
        s3_client.upload_fileobj(io.BytesIO(image_data), S3_BUCKET, object_name)
        file_url = f"https://{S3_BUCKET}.s3.amazonaws.com/{object_name}"
        urls.append(file_url)
        
        # 파일 정보를 DynamoDB에 저장하는 부분
        save_url_to_dynamodb(request, file_url, file.filename, category)

    # 세션 ID를 포함하여 응답 반환    
    return {"session_id": session_id, "urls": urls}

@app.get("/uploaded_images/{session_id}")
async def uploaded_images(session_id: str):
    uploaded_images_urls = get_images_by_session_id(session_id)
    return {"uploaded_images_urls": uploaded_images_urls, "session_id": session_id}

@app.get("/categories/{session_id}")
async def get_categories(session_id: str):
    categories_info = {}
    for category in labels:
        response = table.scan(FilterExpression=Attr('Category').eq(category) & Attr('sessionID').eq(session_id))
        items = response.get('Items', [])
        if items:
            representative_image = items[0]['URL']
            categories_info[category] = representative_image
    return {"categories_info": categories_info, "session_id": session_id}

@app.get("/categories/{category_name}/{session_id}")
async def get_category_images(category_name: str, session_id: str):
    formatted_category = format_category_name(category_name)
    response = table.scan(
        FilterExpression=Attr('Category').eq(formatted_category) & Attr('sessionID').eq(session_id)
    )
    items = response.get('Items', [])
    images = [item['URL'] for item in items]
    return {"category_name": formatted_category, "images": images, "session_id": session_id}

@app.get("/download/{category_name}")
async def download_category(category_name: str):
    items = table.scan(FilterExpression=Attr('Category').eq(category_name)).get('Items', [])
    
    # 임시 메모리에 zip 파일 생성
    in_memory_zip = io.BytesIO()
    
    with zipfile.ZipFile(in_memory_zip, mode='w', compression=zipfile.ZIP_DEFLATED) as zipf:
        for item in items:
            url = item['URL']
            response = requests.get(url)
            if response.status_code == 200:
                image_filename = url.split("/")[-1]
                zipf.writestr(image_filename, response.content)
    
    # 포인터를 파일의 시작 부분으로 이동
    in_memory_zip.seek(0)
    
    # 인 메모리 zip 파일의 내용을 S3 버킷에 업로드
    zip_filename = f"{category_name}.zip"
    s3_client.upload_fileobj(in_memory_zip, S3_BUCKET, zip_filename)
    file_url = f"https://{S3_BUCKET}.s3.amazonaws.com/{zip_filename}"
    
    # 클라이언트가 다운로드할 수 있는 링크를 제공
    return {"url": file_url}
