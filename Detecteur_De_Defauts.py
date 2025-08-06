# -*- coding: utf-8 -*-

import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
import os
import datetime
import threading
import queue
import json
import logging
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTK

# CONFIGURATION DU LOGGING

logging.basicConfig(level=logging.INFO, format = '%(asctime)s - %(levelname)s - %(message)s')

#CLASSE PRINCIPALE DE L'APPLICATION

class 