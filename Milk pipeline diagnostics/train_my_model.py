# train_my_model.py
from ultralytics import YOLO
import os
import shutil
import yaml
import random

print("=" * 60)
print("ОБУЧЕНИЕ МОДЕЛИ НА ВАШИХ ДАННЫХ")
print("=" * 60)

# 1. Проверяем наличие размеченных данных
if not os.path.exists("dataset/images"):
    print("❌ Ошибка: Нет размеченных данных в dataset/images/")
    print("   Сначала запустите скрипт разметки!")
    exit()

images = [f for f in os.listdir("dataset/images") if f.endswith('.jpg')]
print(f"✅ Найдено {len(images)} размеченных изображений")

# 2. Создаем YAML конфигурацию
yaml_content = f"""
path: {os.path.abspath('dataset')}
train: images
val: images

nc: 5
names: ['Milk stone', 'Fat', 'Protein', 'Biofilm', 'Custom']
"""

with open("dataset.yaml", "w") as f:
    f.write(yaml_content)

print("✅ Создан dataset.yaml")

# 3. Обучаем модель
print("\n🚀 Начинаем обучение...")
print("⚠️  Это займет некоторое время (10-30 минут на CPU)")

# Используем предобученную модель как основу
model = YOLO('yolov8n.pt')

# Быстрое обучение с минимальными параметрами
results = model.train(
    data='dataset.yaml',
    epochs=30,  # Меньше эпох для быстрого обучения
    imgsz=320,  # Меньший размер для быстрейшего обучения
    batch=4,  # Маленький batch для CPU
    device='cpu',  # Используем CPU
    name='my_farm_animals',
    verbose=True,
    save=True,
    plots=True,
    # Минимальные аугментации
    hsv_h=0.0,
    hsv_s=0.0,
    hsv_v=0.0,
)

print("\n✅ Обучение завершено!")
print("📁 Модель сохранена в: runs/detect/my_farm_animals/weights/best.pt")

# 4. Тестируем на случайном изображении
test_images = images[:5]  # Берем первые 5 изображений для теста
if test_images:
    test_image = f"dataset/images/{random.choice(test_images)}"
    print(f"\n🧪 Тестируем на изображении: {os.path.basename(test_image)}")

    results = model(test_image, save=True, project="test_results", name="test")
    print(f"✅ Тест сохранен в: test_results/test/")