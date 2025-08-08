import gxipy as gx
import cv2
import numpy as np
import time

def main():
    # Initialisation
    device_manager = gx.DeviceManager()
    device_manager.update_device_list()
    dev_num = device_manager.get_device_number()

    if dev_num == 0:
        print("❌ Aucune caméra Daheng détectée.")
        return

    # Ouverture de la première caméra
    cam = device_manager.open_device_by_index(1)
    cam.TriggerMode.set(gx.GxSwitchEntry.OFF)
    cam.stream_on()

    print("📷 Streaming en cours... Appuyez sur 'q' pour quitter.")
    
    # Fenêtre nommée
    cv2.namedWindow("Caméra Daheng", cv2.WINDOW_NORMAL)
    
    # Activer la configuration manuelle du framerate
    cam.AcquisitionFrameRateMode.set(gx.GxSwitchEntry.ON)
    
    # Régler le framerate souhaité (dans les limites de la caméra)
    cam.AcquisitionFrameRate.set(1000.0)
    
    cam.ExposureTime.set(5000.0)
    



    # Boucle de capture
    while True:
        start_time = time.time()

        # Récupérer image
        raw_image = cam.data_stream[0].get_image(timeout=100)
        if raw_image is None:
            print("⚠️ Image non capturée.")
            continue

        # Conversion RGB → Numpy
        rgb_image = raw_image.convert("RGB")
        np_image = rgb_image.get_numpy_array()

        if np_image is None:
            print("⚠️ Conversion en numpy échouée.")
            continue

        # Conversion RGB → BGR pour OpenCV
        bgr_image = cv2.cvtColor(np_image, cv2.COLOR_RGB2BGR)

        # (Optionnel) Ajouter du texte (FPS ou autre)
        elapsed_time = time.time() - start_time
        fps = 1 / elapsed_time if elapsed_time > 0 else 0
        cv2.putText(bgr_image, f"FPS : {fps:.2f}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # Afficher dans la fenêtre
        cv2.imshow("Caméra Daheng", bgr_image)

        # Sortir si 'q' est pressé
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Nettoyage
    cam.stream_off()
    cam.close()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
