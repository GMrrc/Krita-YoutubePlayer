from krita import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtCore import QThread, pyqtSignal
import cv2
import yt_dlp
import numpy as np
import time


DOCKER_TITLE = 'YouTube Player Docker'


class YouTubePlayerDocker(QDockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(DOCKER_TITLE)

        main_widget = QWidget(self)
        self.setWidget(main_widget)

        layout = QVBoxLayout()
        main_widget.setLayout(layout)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Entrez l'URL YouTube")
        layout.addWidget(self.url_input)

        self.play_button = QPushButton("Télécharger et lire la vidéo")
        self.play_button.clicked.connect(self.play_video)
        layout.addWidget(self.play_button)

        self.status_label = QLabel("Statut: En attente...")
        layout.addWidget(self.status_label)

    def play_video(self):
        url = self.url_input.text()
        if "youtube.com" in url or "youtu.be" in url:
            self.status_label.setText("Téléchargement en cours...")
            video_path = self.download_video(url)
            if video_path:
                self.status_label.setText("Vidéo téléchargée, lecture en cours...")
                self.display_video_on_canvas(video_path)
            else:
                self.status_label.setText("Erreur lors du téléchargement.")
        else:
            QMessageBox.warning(self, "Erreur", "Veuillez entrer une URL YouTube valide")



    def download_video(self, url):
        ydl_opts = {
            'format': 'bestvideo[height<=720][ext=mp4]',
            'outtmpl': '/tmp/%(title)s.%(ext)s',  # Chemin temporaire
            'noplaylist': True
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)
                video_path = ydl.prepare_filename(info_dict)
                return video_path
        except Exception as e:
            print(f"Erreur lors du téléchargement : {e}")
            return None
        


    def display_video_on_canvas(self, video_path):
        cap = cv2.VideoCapture(video_path)
        video_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        video_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        doc = Krita.instance().createDocument(video_width, video_height, "Lecture Vidéo", "RGBA", "U8", "", 120.0)
        Krita.instance().activeWindow().addView(doc)
        layer = doc.createNode("Video Layer", "paintlayer")
        doc.rootNode().addChildNode(layer, None)

        # Lancer le thread de lecture vidéo
        self.video_thread = VideoPlayerThread(video_path)
        self.video_thread.frameReady.connect(lambda frame, width, height, fps: self.update_frame(layer, frame, width, height, doc))
        self.video_thread.start()

    def update_frame(self, layer, frame, video_width, video_height, doc):
        # Convertir la frame en RGBA
        frame_rgba = cv2.cvtColor(frame, cv2.COLOR_RGB2RGBA)
        pixel_data = np.ascontiguousarray(frame_rgba).tobytes()

        # Mettre à jour les pixels sur le calque
        layer.setPixelData(pixel_data, 0, 0, video_width, video_height)

        # Rafraîchir le document
        doc.refreshProjection()
        QApplication.processEvents()



class VideoPlayerThread(QThread):
    frameReady = pyqtSignal(np.ndarray, int, int, float)

    def __init__(self, video_path):
        super().__init__()
        self.video_path = video_path

    def run(self):
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            return
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        video_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        video_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Émettre la frame à traiter dans le thread principal
            self.frameReady.emit(frame, video_width, video_height, fps)
            QThread.msleep(int(1000 / fps))

        # Libérer la capture vidéo après la fin de la lecture
        cap.release()



# Enregistrer le docker dans Krita
app = Krita.instance()
dock_widget_factory = DockWidgetFactory(
    DOCKER_TITLE,
    DockWidgetFactoryBase.DockRight,
    YouTubePlayerDocker
)
app.addDockWidgetFactory(dock_widget_factory)
