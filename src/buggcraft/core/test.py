import os
import sys
import platform
import subprocess
import signal
import time
import psutil
import threading
import queue
import json
import minecraft_launcher_lib
import locale
from concurrent.futures import ThreadPoolExecutor


from PySide6.QtCore import QThread

