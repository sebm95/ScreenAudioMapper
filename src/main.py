# src/main.py
import logging
import tkinter as tk

from gui.app import App


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    root = tk.Tk()
    app = App(root)
    root.mainloop()


if __name__ == "__main__":
    main()