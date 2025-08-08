import sys 
import gxipy as gx
import cv2
import numpy as np
import time
from PyQt6.QtWidgets import (
    QApplication, QLabel, QWidget, QVBoxLayout, QHBoxLayout, QSlider,
    QSizePolicy, QPushButton, QSpacerItem
)
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import QTimer, Qt

class CameraStream(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Caméra Daheng - PyQt6")

        # Bouton Quitter en haut à droite
        self.quit_button = QPushButton("Quitter")
        self.quit_button.setStyleSheet("background-color: red; color: white; font-weight: bold;")
        self.quit_button.clicked.connect(self.close)

        # Layout horizontal supérieur pour bouton quitter à droite
        top_layout = QHBoxLayout()
        top_layout.addStretch()
        top_layout.addWidget(self.quit_button)

        # Label vidéo
        self.label = QLabel("Flux vidéo")
        self.label.setScaledContents(True)
        self.label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Zone pour afficher la photo de référence
        self.ref_label = QLabel("Photo de référence")
        self.ref_label.setFixedSize(520, 320)
        self.ref_label.setStyleSheet("border: 2px solid gray; background-color: #f0f0f0;")
        self.ref_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Bouton bleu pour prendre photo de référence
        self.ref_button = QPushButton("Prendre photo de référence")
        self.ref_button.setStyleSheet("background-color: green; color: white; font-size: 18px; padding: 12px;")
        self.ref_button.clicked.connect(self.take_reference_photo)

        # Bouton pour supprimer la photo de référence
        self.clear_ref_button = QPushButton("Supprimer la photo de référence")
        self.clear_ref_button.setStyleSheet("background-color: grey; color: white; font-size: 12px; padding: 10px;")
        self.clear_ref_button.clicked.connect(self.clear_reference_photo)

        # Sliders + labels à droite
        self.fps_title = QLabel("Réglage FPS")
        self.fps_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.fps_label = QLabel("FPS: --")
        self.fps_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.fps_slider = QSlider(Qt.Orientation.Horizontal)
        self.fps_slider.setMinimum(1)    # sera ajusté après init caméra
        self.fps_slider.setMaximum(1000)
        self.fps_slider.setValue(60)
        self.fps_slider.valueChanged.connect(self.change_fps)
        self.fps_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.fps_slider.setTickInterval(100)

        self.exp_title = QLabel("Réglage Exposition (µs)")
        self.exp_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.exp_label = QLabel("Exposition (µs): --")
        self.exp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.exp_slider = QSlider(Qt.Orientation.Horizontal)
        self.exp_slider.setMinimum(100)  # Valeur minimale exposée à 100 µs (ajuster selon caméra)
        self.exp_slider.setMaximum(10000) # Valeur max provisoire
        self.exp_slider.setValue(1500)
        self.exp_slider.valueChanged.connect(self.change_exposure)
        self.exp_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.exp_slider.setTickInterval(2500)

        # Layout sliders verticaux avec titres
        sliders_layout = QVBoxLayout()
        sliders_layout.addWidget(self.fps_title)
        sliders_layout.addWidget(self.fps_label)
        sliders_layout.addWidget(self.fps_slider)
        sliders_layout.addSpacing(30)
        sliders_layout.addWidget(self.exp_title)
        sliders_layout.addWidget(self.exp_label)
        sliders_layout.addWidget(self.exp_slider)
        sliders_layout.addStretch()

        # Layout vertical pour la photo de référence et ses boutons
        # Layout vertical pour la photo de référence, sliders et ses boutons
        ref_buttons_layout = QVBoxLayout()
        
        # Ajout des sliders + labels au-dessus
        ref_buttons_layout.addWidget(self.fps_title)
        ref_buttons_layout.addWidget(self.fps_label)
        ref_buttons_layout.addWidget(self.fps_slider)
        ref_buttons_layout.addSpacing(20)
        ref_buttons_layout.addWidget(self.exp_title)
        ref_buttons_layout.addWidget(self.exp_label)
        ref_buttons_layout.addWidget(self.exp_slider)
        ref_buttons_layout.addSpacing(30)
        
        # Puis la zone de photo et les boutons
        ref_buttons_layout.addWidget(self.ref_label)
        ref_buttons_layout.addWidget(self.ref_button)
        ref_buttons_layout.addWidget(self.clear_ref_button)
        ref_buttons_layout.addStretch()
        
        
        # Layout vidéo + boutons pause/reprendre (à gauche)
        video_layout = QVBoxLayout()
        video_layout.addWidget(self.label)
        
        # Boutons pause/reprendre sous le flux vidéo
        self.pause_button = QPushButton("Pause")
        self.pause_button.setStyleSheet("background-color: orange; color: black; font-size: 16px; padding: 10px;")
        self.pause_button.clicked.connect(self.pause_stream)
        
        self.resume_button = QPushButton("Reprendre")
        self.resume_button.setStyleSheet("background-color: blue; color: white; font-size: 16px; padding: 10px;")
        self.resume_button.clicked.connect(self.resume_stream)
        
        video_layout.addWidget(self.pause_button)
        video_layout.addWidget(self.resume_button)
        video_layout.addStretch()
        
        # Layout principal horizontal
        main_layout = QHBoxLayout()
        main_layout.addLayout(video_layout, stretch=4)
        main_layout.addLayout(ref_buttons_layout, stretch=2)

    

        # Layout global vertical (bouton + contenu)
        global_layout = QVBoxLayout()
        global_layout.addLayout(top_layout)
        global_layout.addLayout(main_layout)

        self.setLayout(global_layout)

        # Initialisation caméra
        self.device_manager = gx.DeviceManager()
        self.device_manager.update_device_list()
        dev_num = self.device_manager.get_device_number()
        if dev_num == 0:
            raise RuntimeError("Aucune caméra Daheng détectée")

        self.cam = self.device_manager.open_device_by_index(1)
        self.cam.TriggerMode.set(gx.GxSwitchEntry.OFF)

        # Activer contrôle manuel FPS
        self.cam.AcquisitionFrameRateMode.set(gx.GxSwitchEntry.ON)

        # Récupérer plages FPS et exposition réelles
        fps_range = self.cam.AcquisitionFrameRate.get_range()
        minfps=10
        maxfps=500
        self.min_fps = int(fps_range['min'])
        self.max_fps = int(fps_range['max'])
        self.fps_slider.setMinimum(minfps)
        self.fps_slider.setMaximum(maxfps)

        exposure_range = self.cam.ExposureTime.get_range()
        self.min_exp = int(exposure_range['min'])
        self.max_exp = int(exposure_range['max'])
        minexp = 500
        maxexp = 20000
        self.exp_slider.setMinimum(minexp)
        self.exp_slider.setMaximum(maxexp)

        # Valeurs initiales
        self.current_fps = self.fps_slider.value()
        self.current_exp = self.exp_slider.value()
        self.cam.AcquisitionFrameRate.set(self.current_fps)
        self.cam.ExposureTime.set(self.current_exp)

        self.fps_label.setText(f"FPS: {self.current_fps}")
        self.exp_label.setText(f"Exposition (µs): {self.current_exp}")

        self.cam.stream_on()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(int(1000 / self.current_fps))
        
        try:
            if hasattr(self.cam, "FocusMode") and self.cam.FocusMode.is_writable():
                self.cam.FocusMode.set(gx.GxFocusMode.AUTO)
                print("🎯 Autofocus activé.")
            else:
                print("⚠️ Autofocus non supporté sur cette caméra.")
        except Exception as e:
            print(f"Erreur lors de l'activation de l'autofocus : {e}")

        # Variable pour stocker la photo de référence en format QImage
        self.reference_image = None
        
        # Bouton Pause
        self.pause_button = QPushButton("Pause")
        self.pause_button.setStyleSheet("background-color: orange; color: black; font-size: 16px; padding: 10px;")
        self.pause_button.clicked.connect(self.pause_stream)
        
        # Bouton Reprendre
        self.resume_button = QPushButton("Reprendre")
        self.resume_button.setStyleSheet("background-color: blue; color: white; font-size: 16px; padding: 10px;")
        self.resume_button.clicked.connect(self.resume_stream)
        

        
        ###############################
        ###############################
        ###############################
        ######## FIN INIT #############
        ###############################
        ###############################
        ###############################

    def take_reference_photo(self):
        raw_image = self.cam.data_stream[0].get_image(timeout=100)
        if raw_image is None:
            return
        rgb_image = raw_image.convert("RGB")
        np_image = rgb_image.get_numpy_array()
        if np_image is None:
            return

        bgr_image = cv2.cvtColor(np_image, cv2.COLOR_RGB2BGR)
        height, width, channel = bgr_image.shape
        bytes_per_line = 3 * width
        qt_image = QImage(bgr_image.data, width, height, bytes_per_line, QImage.Format.Format_BGR888)

        self.reference_image = qt_image
        self.ref_label.setPixmap(QPixmap.fromImage(self.reference_image))

    def clear_reference_photo(self):
        self.reference_image = None
        self.ref_label.clear()
        self.ref_label.setText("Photo de référence")

    def change_fps(self, value):
        self.current_fps = value
        self.cam.AcquisitionFrameRate.set(self.current_fps)
        self.fps_label.setText(f"FPS: {self.current_fps}")
        self.timer.setInterval(int(1000 / self.current_fps))

    def change_exposure(self, value):
        self.current_exp = value
        self.cam.ExposureTime.set(self.current_exp)
        self.exp_label.setText(f"Exposition (µs): {self.current_exp}")

    def update_frame(self):
        start_time = time.time()

        raw_image = self.cam.data_stream[0].get_image(timeout=50)
        if raw_image is None:
            return

        rgb_image = raw_image.convert("RGB")
        np_image = rgb_image.get_numpy_array()
        if np_image is None:
            return

        bgr_image = cv2.cvtColor(np_image, cv2.COLOR_RGB2BGR)

        elapsed_time = time.time() - start_time
        fps_loop = 1 / elapsed_time if elapsed_time > 0 else 0
        cv2.putText(bgr_image, f"FPS cam: {self.current_fps} - FPS loop: {fps_loop:.2f}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        height, width, channel = bgr_image.shape
        bytes_per_line = 3 * width
        qt_image = QImage(bgr_image.data, width, height, bytes_per_line, QImage.Format.Format_BGR888)

        self.label.setPixmap(QPixmap.fromImage(qt_image))

    def closeEvent(self, event):
        self.timer.stop()
        self.cam.stream_off()
        # Ne pas appeler self.cam.close() car non existant
        event.accept()
        
    def pause_stream(self):
        if self.timer.isActive():
            self.timer.stop()
    
    def resume_stream(self):
        if not self.timer.isActive():
            self.timer.start(int(1000 / self.current_fps))



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CameraStream()
    window.resize(1200, 700)
    window.show()
    sys.exit(app.exec())
