import cv2
import os
import json
from datetime import datetime
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox

# ========== КОНФИГУРАЦИЯ ==========
CLASSES = ['Sheep', 'Cow', 'Chicken', 'Goose', 'Pig', 'Custom']
CLASS_COLORS = {
    'Sheep': (0, 255, 0),  # Green
    'Cow': (255, 0, 0),  # Blue
    'Chicken': (0, 255, 255),  # Yellow
    'Goose': (255, 255, 0),  # Cyan
    'Pig': (0, 0, 255),  # Red
    'Custom': (255, 0, 255)  # Magenta
}

# Создаем папки для датасета
os.makedirs("dataset/images", exist_ok=True)
os.makedirs("dataset/labels", exist_ok=True)

# JSON для метаданных аннотаций
annotations_file = "dataset/annotations.json"
if not os.path.exists(annotations_file):
    with open(annotations_file, 'w', encoding='utf-8') as f:
        json.dump({
            "info": {
                "description": "Farm Animals Dataset",
                "date_created": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            "images": [],
            "annotations": [],
            "categories": [{"id": i, "name": cls} for i, cls in enumerate(CLASSES)]
        }, f, indent=2)

# ========== ПОИСК ВИДЕО ==========
video_files = []
for file in os.listdir('.'):
    if file.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.flv')):
        video_files.append(file)

if not video_files:
    print("Video file not found! Place video file in this folder.")
    print(f"Current folder: {os.getcwd()}")
    exit()

video_path = video_files[0]
print(f"Using video: {video_path}")

# ========== ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ==========
cap = cv2.VideoCapture(video_path)
if not cap.isOpened():
    print("Cannot open video!")
    exit()

# Variables for annotation
roi = None
ix, iy = -1, -1
drawing = False
frame_count = 0
saved_count = 0
current_frame = None
current_annotations = []
selected_class = 0
temp_roi = None
custom_class_name = ""

# Tkinter window for class selection
class_selection_window = None


# ========== FUNCTIONS ==========
def load_annotations():
    """Load existing annotations"""
    if os.path.exists(annotations_file):
        with open(annotations_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"images": [], "annotations": []}


def save_annotation(image_id, bbox, class_id, class_name):
    """Save annotation to JSON"""
    data = load_annotations()

    annotation = {
        "id": len(data.get("annotations", [])) + 1,
        "image_id": image_id,
        "bbox": bbox,
        "category_id": class_id,
        "category_name": class_name,
        "area": bbox[2] * bbox[3]
    }

    if "annotations" not in data:
        data["annotations"] = []
    data["annotations"].append(annotation)

    with open(annotations_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

    # Also save in YOLO format
    save_yolo_annotation(image_id, bbox, class_id)


def save_yolo_annotation(image_id, bbox, class_id):
    """Save annotation in YOLO format"""
    h, w = current_frame.shape[:2]
    x_center = (bbox[0] + bbox[2] / 2) / w
    y_center = (bbox[1] + bbox[3] / 2) / h
    width = bbox[2] / w
    height = bbox[3] / h

    label_file = f"dataset/labels/{image_id}.txt"
    with open(label_file, 'a') as f:
        f.write(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")


def show_class_selection():
    """Show class selection window"""
    global class_selection_window, selected_class, custom_class_name

    if class_selection_window is not None:
        class_selection_window.destroy()

    class_selection_window = tk.Toplevel()
    class_selection_window.title("Select Class")
    class_selection_window.geometry("300x400")
    class_selection_window.resizable(False, False)

    class_selection_window.transient(root)
    class_selection_window.grab_set()

    # Center the window
    class_selection_window.update_idletasks()
    x = root.winfo_x() + (root.winfo_width() - class_selection_window.winfo_width()) // 2
    y = root.winfo_y() + (root.winfo_height() - class_selection_window.winfo_height()) // 2
    class_selection_window.geometry(f"+{x}+{y}")

    tk.Label(class_selection_window, text="Select animal class:",
             font=('Arial', 12, 'bold')).pack(pady=10)

    # Buttons for each class
    for idx, cls in enumerate(CLASSES):
        color = CLASS_COLORS.get(cls, (255, 255, 255))
        color_hex = '#%02x%02x%02x' % color

        btn = tk.Button(
            class_selection_window,
            text=cls,
            bg=color_hex,
            fg='white' if sum(color) < 400 else 'black',
            font=('Arial', 10, 'bold'),
            width=20,
            height=2,
            command=lambda idx=idx: select_class(idx)
        )
        btn.pack(pady=5)

    # Custom class button
    if 'Custom' in CLASSES:
        custom_btn = tk.Button(
            class_selection_window,
            text="✏️ Enter custom...",
            bg='#8B00FF',
            fg='white',
            font=('Arial', 10, 'bold'),
            width=20,
            height=2,
            command=enter_custom_class
        )
        custom_btn.pack(pady=10)

    tk.Label(class_selection_window,
             text="Or press number 0-5 on keyboard",
             font=('Arial', 9)).pack(pady=5)


def select_class(class_idx):
    """Select class"""
    global selected_class, class_selection_window, custom_class_name
    selected_class = class_idx

    # If selecting Custom class and no name set, ask for it
    if CLASSES[selected_class] == "Custom" and not custom_class_name:
        enter_custom_class()

    if class_selection_window:
        class_selection_window.destroy()
        class_selection_window = None

    print(f"Selected class: {CLASSES[selected_class]}")
    if CLASSES[selected_class] == "Custom" and custom_class_name:
        print(f"Custom name: {custom_class_name}")


def enter_custom_class():
    """Enter custom class name"""
    global custom_class_name, selected_class, class_selection_window

    custom_name = simpledialog.askstring(
        "Custom Class",
        "Enter object name:",
        parent=class_selection_window if class_selection_window else root
    )

    if custom_name and custom_name.strip():
        custom_class_name = custom_name.strip()
        selected_class = CLASSES.index('Custom')
        print(f"Custom class: {custom_class_name}")
    elif custom_name == "":
        # User cancelled, revert to previous class
        selected_class = 0  # Default to Sheep
        print("Custom input cancelled. Reverted to Sheep.")


def mouse_callback(event, x, y, flags, param):
    """Mouse event handler"""
    global roi, ix, iy, drawing, temp_roi

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        ix, iy = x, y
        roi = None
        temp_roi = None

    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            temp_roi = (ix, iy, x - ix, y - iy)

    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        x1 = min(ix, x)
        y1 = min(iy, y)
        x2 = max(ix, x)
        y2 = max(iy, y)
        w = x2 - x1
        h = y2 - y1

        if w > 10 and h > 10:
            roi = (x1, y1, w, h)
            temp_roi = None
            print(f"Selected area: {w}x{h}")


# ========== MAIN CODE ==========
# Load first frame
ret, current_frame = cap.read()
if not ret:
    print("Cannot read video!")
    exit()

frame_count = 1
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

# Initialize Tkinter
root = tk.Tk()
root.withdraw()

# Create OpenCV window
cv2.namedWindow("Video Annotation Tool", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Video Annotation Tool", 1280, 720)
cv2.setMouseCallback("Video Annotation Tool", mouse_callback)

# Instructions
print("\n" + "=" * 60)
print("ANNOTATION INSTRUCTIONS:")
print("=" * 60)
print("1. Select animal with LMB (click and drag)")
print("2. Press number to select class:")
print("   0: Sheep    1: Cow    2: Chicken")
print("   3: Goose    4: Pig    5: Custom")
print("3. Press 's' - save annotation (with selected class)")
print("4. Press 'a' - save all annotations and go to next frame")
print("5. Press 'n' - next frame without saving")
print("6. Press 'd' - delete last annotation")
print("7. Press 'c' - clear all annotations")
print("8. Press 'space' - open class selection window")
print("9. Press 'e' - edit custom class name (if Custom selected)")
print("10. Press 'q' - quit")
print("=" * 60)

while True:
    # Copy frame for display
    display_frame = current_frame.copy()

    # Draw existing annotations
    for i, ann in enumerate(current_annotations):
        x, y, w, h = ann["bbox"]
        cls_name = ann["class_name"]
        color = CLASS_COLORS.get(cls_name, (255, 255, 255))

        # Rectangle
        cv2.rectangle(display_frame, (x, y), (x + w, y + h), color, 3)

        # Label with class
        label = f"{i + 1}: {cls_name}"
        if cls_name == "Custom" and custom_class_name:
            label = f"{i + 1}: {custom_class_name}"

        # Text background
        (text_width, text_height), baseline = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2
        )
        cv2.rectangle(
            display_frame,
            (x, y - text_height - 10),
            (x + text_width, y),
            color,
            -1
        )
        cv2.putText(
            display_frame,
            label,
            (x, y - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

    # Draw current selection
    if drawing and temp_roi:
        x, y, w, h = temp_roi
        cv2.rectangle(display_frame, (x, y), (x + w, y + h), (255, 255, 0), 2)
    elif roi:
        x, y, w, h = roi
        current_color = CLASS_COLORS.get(CLASSES[selected_class], (255, 255, 255))
        cv2.rectangle(display_frame, (x, y), (x + w, y + h), current_color, 2)

    # Display information
    class_display = CLASSES[selected_class]
    if CLASSES[selected_class] == "Custom" and custom_class_name:
        class_display = f"Custom: {custom_class_name}"

    cv2.putText(display_frame, f"Frame: {frame_count}/{total_frames}",
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    cv2.putText(display_frame, f"Annotations: {len(current_annotations)}",
                (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
    cv2.putText(display_frame, f"Class: {class_display}",
                (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)

    # Instructions
    cv2.putText(display_frame, "s-save, a-save&next, n-next, d-del, c-clear, space-class, q-quit",
                (10, display_frame.shape[0] - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    cv2.imshow("Video Annotation Tool", display_frame)

    # Key handling
    key = cv2.waitKey(1) & 0xFF

    # Numbers for class selection (0-5) - always available
    if ord('0') <= key <= ord('5'):
        class_idx = key - ord('0')
        if class_idx < len(CLASSES):
            select_class(class_idx)

    elif key == ord('s') and roi:  # Save single annotation
        if roi:
            class_name = CLASSES[selected_class]
            if class_name == "Custom":
                if not custom_class_name:
                    enter_custom_class()
                    if not custom_class_name:  # User cancelled
                        continue
                if custom_class_name:
                    class_name = custom_class_name

            current_annotations.append({
                "bbox": roi,
                "class_id": selected_class,
                "class_name": class_name
            })
            print(f"✓ Added: {class_name}")
            roi = None

    elif key == ord('a') and len(current_annotations) > 0:  # Save all and next frame
        # Save image
        image_id = f"frame_{frame_count:06d}"
        image_filename = f"{image_id}.jpg"
        image_path = f"dataset/images/{image_filename}"
        cv2.imwrite(image_path, current_frame)

        # Save annotations
        for ann in current_annotations:
            save_annotation(image_id, ann["bbox"], ann["class_id"], ann["class_name"])

        # Add image info to JSON
        data = load_annotations()
        data["images"].append({
            "id": image_id,
            "file_name": image_filename,
            "width": current_frame.shape[1],
            "height": current_frame.shape[0],
            "frame_number": frame_count
        })
        with open(annotations_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        saved_count += 1
        print(f"✓ Saved frame {frame_count} with {len(current_annotations)} annotations")

        # Next frame
        ret, current_frame = cap.read()
        if ret:
            frame_count += 1
            current_annotations = []
            roi = None
        else:
            print("End of video")
            break

    elif key == ord('n'):  # Next frame without saving
        ret, current_frame = cap.read()
        if ret:
            frame_count += 1
            current_annotations = []
            roi = None
            print(f"→ Next frame {frame_count}")
        else:
            print("End of video")
            break

    elif key == ord('d'):  # Delete last annotation
        if current_annotations:
            removed = current_annotations.pop()
            print(f"✗ Removed: {removed['class_name']}")

    elif key == ord('c'):  # Clear all annotations
        current_annotations = []
        roi = None
        print("Cleared all annotations")

    elif key == 32:  # Space bar - open class selection
        show_class_selection()

    elif key == ord('e'):  # Edit custom class name
        if CLASSES[selected_class] == "Custom":
            enter_custom_class()
        else:
            print("Custom class not selected. Press 5 first to select Custom.")

    elif key == ord('q'):  # Quit
        break

# ========== CLEANUP ==========
cap.release()
cv2.destroyAllWindows()
if root:
    root.destroy()

# Statistics
print(f"\n{'=' * 50}")
print("ANNOTATION COMPLETE!")
print(f"{'=' * 50}")
print(f"Processed frames: {frame_count}")
print(f"Saved annotated frames: {saved_count}")

if os.path.exists(annotations_file):
    with open(annotations_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    annotations = data.get("annotations", [])
    if annotations:
        print(f"Total annotations: {len(annotations)}")

        from collections import Counter

        class_counts = Counter([ann.get("category_name", "Unknown") for ann in annotations])

        print("\nClass distribution:")
        for cls, count in class_counts.items():
            print(f"  {cls}: {count}")

        # Save statistics
        stats_file = "dataset/statistics.txt"
        with open(stats_file, 'w', encoding='utf-8') as f:
            f.write(f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Video: {video_path}\n")
            f.write(f"Total frames: {frame_count}\n")
            f.write(f"Annotated frames: {saved_count}\n")
            f.write(f"Total annotations: {len(annotations)}\n\n")
            f.write("Class distribution:\n")
            for cls, count in class_counts.items():
                f.write(f"  {cls}: {count}\n")

        print(f"\nStatistics saved to: {stats_file}")
        print(f"Annotations: {annotations_file}")
        print(f"Images: dataset/images/")
        print(f"YOLO labels: dataset/labels/")

print(f"\nFor YOLO training create dataset.yaml:")
print("""
path: /path/to/dataset
train: images
val: images

nc: 6
names: ['Sheep', 'Cow', 'Chicken', 'Goose', 'Pig', 'Custom']
""")