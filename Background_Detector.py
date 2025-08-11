import cv2
import numpy as np
import os

def ask_background_position():
    while True:
        pos = input("Le fond est-il à gauche ou à droite ? (g/d) : ").strip().lower()
        if pos in ['g', 'd']:
            return pos
        print("Réponse invalide. Tapez 'g' pour gauche ou 'd' pour droite.")

def get_image_files(folder):
    extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']
    return [os.path.join(folder, f) for f in os.listdir(folder)
            if os.path.splitext(f)[1].lower() in extensions]

def detect_background_hsv(image_hsv, hsv_lower, hsv_upper):
    mask = cv2.inRange(image_hsv, hsv_lower, hsv_upper)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5,5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    return mask

def find_background_zone(mask, bg_position, image_shape):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    largest_contour = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(largest_contour)
    height, width = image_shape[:2]
    if bg_position == 'g':
        # On considère toute la zone de fond à gauche jusqu'à la largeur du rectangle détecté
        return (0, 0, x + w, height)
    else:
        # Zone fond à droite : du x détecté jusqu'à la fin à droite
        return (x, 0, width - x, height)

def draw_background_zone(image, bg_rect):
    if bg_rect is None:
        return image
    x, y, w, h = bg_rect
    annotated = image.copy()
    cv2.rectangle(annotated, (x,y), (x+w, y+h), (0,255,0), 2)
    return annotated

def main():
    input_folder = "C:/Users/DGame/Downloads/IMG"  # dossier à adapter
    output_folder = "C:/Users/DGame/Downloads/IMG_BACK"
    os.makedirs(output_folder, exist_ok=True)

    # Exemple plage HSV pour un fond marron clair, à calibrer selon tes images
    hsv_lower = np.array([10, 50, 50])
    hsv_upper = np.array([30, 255, 255])

    bg_position = ask_background_position()
    image_files = get_image_files(input_folder)

    print(f"Traitement de {len(image_files)} images du dossier {input_folder}")

    for i, img_path in enumerate(sorted(image_files), 1):
        img = cv2.imread(img_path)
        if img is None:
            print(f"Impossible de charger {img_path}, fichier ignoré.")
            continue

        hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        mask = detect_background_hsv(hsv_img, hsv_lower, hsv_upper)

        bg_rect = find_background_zone(mask, bg_position, img.shape)

        img_annotated = draw_background_zone(img, bg_rect)

        output_path = os.path.join(output_folder, f"{i:03d}_{os.path.basename(img_path)}")
        cv2.imwrite(output_path, img_annotated)
        print(f"Image traitée et sauvegardée: {output_path}")

if __name__ == "__main__":
    main()
