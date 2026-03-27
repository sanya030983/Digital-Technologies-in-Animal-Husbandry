import cv2
from ultralytics import YOLO
import matplotlib.pyplot as plt

# 1. Загрузка предобученной модели YOLOv8 (скачается автоматически, ~6 Мб)
# 'yolo11n.pt' — самая маленькая и быстрая модель, достаточная для демонстрации
model = YOLO('yolo11n.pt')

# 2. Загрузка изображения
# Замените 'herd.jpg' на путь к вашему файлу
image_path = 'herd.jpg'
image = cv2.imread(image_path)

if image is None:
    print("Ошибка загрузки изображения. Проверьте путь.")
    exit()

# 3. Выполнение детекции
# Модель YOLO обучена на COCO, где есть классы 'cow', 'sheep', 'horse' и др.
results = model(image)

# 4. Визуализация результатов и подсчет
result_image = image.copy()
animal_count = 0

# Классы, которые нас интересуют (номера из COCO: 19=cow, 20=sheep, 17=cat, 18=dog для примера)
target_classes = {'cow': 19, 'sheep': 20}

for result in results:
    boxes = result.boxes
    for box in boxes:
        # Получаем координаты, уверенность и класс
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        confidence = float(box.conf[0])
        class_id = int(box.cls[0])

        # Если обнаруженное животное - корова или овца
        if class_id in target_classes.values():
            animal_count += 1
            # Рисуем прямоугольник и подпись
            cv2.rectangle(result_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            label = f"{list(target_classes.keys())[list(target_classes.values()).index(class_id)]} {confidence:.2f}"
            cv2.putText(result_image, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

# 5. Вывод результатов
print(f"На изображении обнаружено животных: {animal_count}")

# 6. Показать оригинальное и обработанное изображение
fig, axes = plt.subplots(1, 2, figsize=(15, 7))
axes[0].imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
axes[0].set_title('Оригинальное изображение')
axes[0].axis('off')

axes[1].imshow(cv2.cvtColor(result_image, cv2.COLOR_BGR2RGB))
axes[1].set_title(f'Обнаружено животных: {animal_count}')
axes[1].axis('off')

plt.tight_layout()
plt.show()

# 7. (Дополнительно) Сохранение результата
cv2.imwrite('result_detection.jpg', result_image)
print("Результат сохранен как 'result_detection.jpg'")
