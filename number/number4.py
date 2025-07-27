from ultralytics import YOLO
import cv2
import os
from paddleocr import PaddleOCR

model = YOLO('best.pt')
ocr = PaddleOCR(use_textline_orientation=True, lang='korean')

input_folder = "./input"
output_folder = "./plates"
os.makedirs(output_folder, exist_ok=True)

image_files = [f for f in os.listdir(input_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
total_images = len(image_files)
print(f"입력 폴더 내 이미지 개수: {total_images}")

def enhance_image(img):
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0)
    cl = clahe.apply(l)
    limg = cv2.merge((cl, a, b))
    return cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

detected_images_count = 0  # 번호판 1개 이상 탐지된 이미지 수 카운트

for filename in image_files:
    print(f"처리 중: {filename}")
    full_path = os.path.join(input_folder, filename)
    image = cv2.imread(full_path)
    if image is None:
        print(f"❌ 이미지 불러오기 실패: {filename}")
        continue

    enhanced_image = enhance_image(image)

    results = model(enhanced_image, imgsz=960)[0]
    boxes = results.boxes.xyxy.cpu().numpy()
    num_boxes = len(boxes)
    print(f"탐지된 박스 개수: {num_boxes}")

    if num_boxes == 0:
        print(f"❌ 번호판 탐지 실패: {filename}")
        continue

    # 번호판 하나라도 탐지되면 이미지 1장 성공 카운트 증가
    detected_images_count += 1

    for i, box in enumerate(boxes):
        x1, y1, x2, y2 = map(int, box)
        plate_img = image[y1:y2, x1:x2]
        plate_filename = f"{os.path.splitext(filename)[0]}_plate_{i}.jpg"
        plate_path = os.path.join(output_folder, plate_filename)
        cv2.imwrite(plate_path, plate_img)
        print(f"✅ 번호판 이미지 저장: {plate_filename}")

        # OCR 수행 (필요 시 아래 부분 수정 가능)
        ocr_result = ocr.ocr(plate_img)

        texts = []
        for line in ocr_result:
            if len(line) == 2:
                text_info = line[1]
                if isinstance(text_info, (list, tuple)) and len(text_info) == 2:
                    text, conf = text_info
                    if conf > 0.5:
                        texts.append(text)

        print(f"📄 인식된 텍스트: {texts}")

        text_filename = f"{os.path.splitext(filename)[0]}_plate_{i}.txt"
        text_path = os.path.join(output_folder, text_filename)
        with open(text_path, 'w', encoding='utf-8') as f:
            for text_line in texts:
                f.write(text_line + '\n')
        print(f"📄 텍스트 저장 완료: {text_filename}")

# 이미지 단위 성공률 계산 및 출력
if total_images > 0:
    detection_rate = (detected_images_count / total_images) * 100
else:
    detection_rate = 0.0

print(f"\n총 이미지 수: {total_images}")
print(f"번호판 1개 이상 탐지된 이미지 수: {detected_images_count}")
print(f"탐지 성공률(이미지 단위): {detection_rate:.2f}%")

print("모든 작업 완료")
