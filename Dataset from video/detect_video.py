from ultralytics import YOLO

# Загружаем модель
model = YOLO('runs/detect/my_farm_animals4/weights/best.pt')

# Запускаем детекцию с отображением
results = model(
    'dataset from video.mkv',
    save=True,           # сохранять видео
    show=True,           # показывать окно с видео
    conf=0.5,           # порог уверенности
    imgsz=640,          # размер изображения
    device='cpu',       # или 'cuda' если есть GPU
    verbose=False       # уменьшить вывод в консоль
)