import sys
import gxipy as gx
import cv2
import numpy as np
import time
from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QHBoxLayout, QSlider, QSizePolicy
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import QTimer, Qt

class CameraStream(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Caméra Daheng - PyQt6")

        # Label vidéo
        self.label = QLabel("Flux vidéo")
        self.label.setScaledContents(True)
        self.label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Sliders + labels à droite
        self.fps_label = QLabel("FPS: --")
        self.fps_slider = QSlider(Qt.Orientation.Horizontal)
        self.fps_slider.setMinimum(1)    # sera ajusté après init caméra
        self.fps_slider.setMaximum(1000)
        self.fps_slider.setValue(60)
        self.fps_slider.valueChanged.connect(self.change_fps)
        self.fps_slider.setTickPosition(QSlider.TickPosition.TicksRight)
        self.fps_slider.setTickInterval(10)

        self.exp_label = QLabel("Exposition (µs): --")
        self.exp_slider = QSlider(Qt.Orientation.Horizontal)
        self.exp_slider.setMinimum(100)  # Valeur minimale exposée à 100 µs (ajuster selon caméra)
        self.exp_slider.setMaximum(50000) # Valeur max provisoire
        self.exp_slider.setValue(5000)
        self.exp_slider.valueChanged.connect(self.change_exposure)
        self.exp_slider.setTickPosition(QSlider.TickPosition.TicksRight)
        self.exp_slider.setTickInterval(5000)

        # Layout sliders verticaux
        sliders_layout = QVBoxLayout()
        sliders_layout.addWidget(self.fps_label, alignment=Qt.AlignmentFlag.AlignCenter)
        sliders_layout.addWidget(self.fps_slider)
        sliders_layout.addSpacing(30)
        sliders_layout.addWidget(self.exp_label, alignment=Qt.AlignmentFlag.AlignCenter)
        sliders_layout.addWidget(self.exp_slider)
        sliders_layout.addStretch()

        # Layout principal horizontal
        main_layout = QHBoxLayout()
        main_layout.addWidget(self.label, stretch=4)
        main_layout.addLayout(sliders_layout, stretch=1)

        self.setLayout(main_layout)

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
        maxfps=1000
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
        cv2.putText(bgr_image, f"FPS caméra: {self.current_fps} - FPS loop: {fps_loop:.2f}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        height, width, channel = bgr_image.shape
        bytes_per_line = 3 * width
        qt_image = QImage(bgr_image.data, width, height, bytes_per_line, QImage.Format.Format_BGR888)

        self.label.setPixmap(QPixmap.fromImage(qt_image))

    def closeEvent(self, event):
        self.timer.stop()
        self.cam.stream_off()
        self.cam.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CameraStream()
    window.resize(1200, 700)
    window.show()
    sys.exit(app.exec())
