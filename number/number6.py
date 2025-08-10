from ultralytics import YOLO
import cv2
import os
import numpy as np
import re
from paddleocr import PaddleOCR
import easyocr

# OCR 초기화
ocr_paddle = PaddleOCR(use_textline_orientation=True, lang='korean')
ocr_easy = easyocr.Reader(['ko'])

# YOLO 모델 불러오기
model = YOLO('best.pt')

# 폴더 설정
input_folder = "./input"
output_folder = "./plates"
os.makedirs(output_folder, exist_ok=True)

image_files = [f for f in os.listdir(input_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
total_images = len(image_files)
print(f"입력 이미지 수: {total_images}")

# 전처리 함수
def preprocess_plate_image(plate_img):
    desired_width = 300
    desired_height = 100
    resized = cv2.resize(plate_img, (desired_width, desired_height), interpolation=cv2.INTER_CUBIC)

    lab = cv2.cvtColor(resized, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_clahe = clahe.apply(l)
    merged = cv2.merge((l_clahe, a, b))
    bright_img = cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)

    denoised = cv2.bilateralFilter(bright_img, d=9, sigmaColor=75, sigmaSpace=75)

    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    sharpened = cv2.filter2D(denoised, -1, kernel)

    return sharpened

# ✅ 정규표현식 약화 (숫자+한글 조합만 통과)
def filter_license_text(texts):
    pattern = re.compile(r'[0-9가-힣A-Z]{4,}')  # 완화된 조건
    return [text for text in texts if pattern.fullmatch(text)]

# EasyOCR 실행
def run_easyocr(img):
    try:
        result = ocr_easy.readtext(img, detail=0)
        return ' '.join(result).strip()
    except Exception as e:
        print(f"[EasyOCR 오류] {e}")
        return ''

# PaddleOCR 실행
def run_paddleocr(img):
    try:
        result = ocr_paddle.predict(img, cls=True)
        texts = []
        for line in result:
            for box in line:
                if len(box) == 2:
                    text, conf = box[1]
                    if conf > 0.5:
                        texts.append(text)
        return ' '.join(texts).strip()
    except Exception as e:
        print(f"[PaddleOCR 오류] {e}")
        return ''

# OCR 통합
def run_multi_ocr(img):
    ocr1 = run_paddleocr(img)
    ocr2 = run_easyocr(img)

    print(f"🔎 PaddleOCR : {ocr1}")
    print(f"🔎 EasyOCR   : {ocr2}")

    candidates = filter_license_text([ocr1, ocr2])
    print(f"✅ 필터링된 후보 : {candidates}")

    return candidates[0] if candidates else (ocr1 or ocr2 or "NO_OCR_RESULT")

# 처리 루프
detected_images_count = 0

for filename in image_files:
    print(f"\n📷 처리 중: {filename}")
    path = os.path.join(input_folder, filename)
    image = cv2.imread(path)
    if image is None:
        print("❌ 이미지 로드 실패")
        continue

    results = model(image, imgsz=960)[0]
    boxes = results.boxes.xyxy.cpu().numpy()
    if len(boxes) == 0:
        print("❌ 번호판 탐지 실패")
        continue

    detected_images_count += 1
    for i, box in enumerate(boxes):
        x1, y1, x2, y2 = map(int, box)

        # padding 적용
        margin = 10
        x1 = max(0, x1 - margin)
        y1 = max(0, y1 - margin)
        x2 = min(image.shape[1], x2 + margin)
        y2 = min(image.shape[0], y2 + margin)

        plate_img = image[y1:y2, x1:x2]
        preprocessed = preprocess_plate_image(plate_img)

        base = os.path.splitext(filename)[0]
        plate_filename = f"{base}_plate_{i}"

        # 전처리된 이미지 저장
        pre_path = os.path.join(output_folder, f"{plate_filename}_preprocessed.jpg")
        cv2.imwrite(pre_path, preprocessed)
        print(f"🖼 전처리 이미지 저장됨: {pre_path}")

        # OCR 실행
        final_text = run_multi_ocr(preprocessed)
        print(f"💬 최종 추출 텍스트: '{final_text}'")

        # ✅ 텍스트 저장 시도 (무조건 저장)
        txt_path = os.path.join(output_folder, f"{plate_filename}.txt")
        try:
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(final_text + '\n')
            print(f"📝 텍스트 저장 성공: {txt_path}")
        except Exception as e:
            print(f"❌ 텍스트 저장 실패: {e}")

# 통계 출력
rate = (detected_images_count / total_images * 100) if total_images > 0 else 0
print(f"\n📊 최종: {total_images}개 중 {detected_images_count}개 탐지 ({rate:.2f}%)")
print("✅ 완료")
