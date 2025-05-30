import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import cv2
import numpy as np


class ImageEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Editor")

        # Image variables
        self.original_image = None
        self.cropped_image = None
        self.resized_image = None
        self.display_image = None
        self.rect_id = None  # For drawing the crop rectangle on canvas

        # Mouse drag coordinates for cropping
        self.start_x = self.start_y = 0
        self.end_x = self.end_y = 0

        # Stacks for undo/redo functionality
        self.undo_stack = []
        self.redo_stack = []

        # Initialize GUI
        self.setup_ui()
        self.setup_shortcuts()

    def setup_ui(self):
        # Button frame at the top
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=5)

        # Basic controls
        tk.Button(button_frame, text="Load Image", command=self.load_image).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Save Image", command=self.save_image).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Grayscale", command=self.apply_grayscale).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Blur", command=self.apply_blur).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Edge Detect", command=self.apply_edge).pack(side=tk.LEFT, padx=5)

        # Image display frame (side-by-side original and cropped)
        image_frame = tk.Frame(self.root)
        image_frame.pack(pady=10)

        # Canvas for original image (left)
        self.canvas = tk.Canvas(image_frame, cursor="cross")
        self.canvas.pack(side=tk.LEFT)

        # Label for displaying cropped image (right)
        self.cropped_label = tk.Label(image_frame, text="Cropped Image will appear here", bd=2, relief="sunken")
        self.cropped_label.pack(side=tk.LEFT, padx=10)

        # Bind mouse actions for crop rectangle
        self.canvas.bind("<ButtonPress-1>", self.start_crop)
        self.canvas.bind("<B1-Motion>", self.update_crop)
        self.canvas.bind("<ButtonRelease-1>", self.finish_crop)

        # Resize slider
        self.slider = tk.Scale(self.root, from_=10, to=200, orient="horizontal", label="Resize (%)", command=self.resize_image)
        self.slider.set(100)
        self.slider.pack(pady=10)

    def setup_shortcuts(self):
        # Keyboard shortcuts
        self.root.bind("<Control-s>", lambda e: self.save_image())
        self.root.bind("<Control-z>", lambda e: self.undo())
        self.root.bind("<Control-y>", lambda e: self.redo())

    def load_image(self):
        # Load image from file
        path = filedialog.askopenfilename()
        if not path:
            return
        self.original_image = cv2.imread(path)

        # Save current state for undo
        self.push_undo(self.original_image.copy())
        self.show_image(self.original_image)

    def show_image(self, img):
        # Convert image from OpenCV to Tkinter format
        self.display_image = img
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)
        self.tk_image = ImageTk.PhotoImage(img_pil)

        # Update canvas with the loaded image
        self.canvas.config(width=self.tk_image.width(), height=self.tk_image.height())
        self.canvas.create_image(0, 0, image=self.tk_image, anchor=tk.NW)

    def start_crop(self, event):
        # Start drawing crop rectangle
        self.start_x, self.start_y = event.x, event.y
        self.rect_id = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline="red")

    def update_crop(self, event):
        # Update crop rectangle in real time
        if self.rect_id:
            self.canvas.coords(self.rect_id, self.start_x, self.start_y, event.x, event.y)

    def finish_crop(self, event):
        # Complete cropping and extract the cropped region
        self.end_x, self.end_y = event.x, event.y
        x1, y1 = min(self.start_x, self.end_x), min(self.start_y, self.end_y)
        x2, y2 = max(self.start_x, self.end_x), max(self.start_y, self.end_y)

        # Scale canvas coords to image size
        scale_x = self.display_image.shape[1] / self.canvas.winfo_width()
        scale_y = self.display_image.shape[0] / self.canvas.winfo_height()
        img_x1, img_y1 = int(x1 * scale_x), int(y1 * scale_y)
        img_x2, img_y2 = int(x2 * scale_x), int(y2 * scale_y)

        # Perform cropping
        self.cropped_image = self.display_image[img_y1:img_y2, img_x1:img_x2]
        self.resized_image = self.cropped_image.copy()

        # Save state for undo
        self.push_undo(self.resized_image.copy())
        self.display_cropped_image(self.cropped_image)

    def display_cropped_image(self, img):
        # Display the cropped/resized image in the label
        if img is None or img.size == 0:
            return
        display_img = cv2.resize(img, (300, 300), interpolation=cv2.INTER_AREA)
        img_rgb = cv2.cvtColor(display_img, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)
        self.tk_crop = ImageTk.PhotoImage(img_pil)
        self.cropped_label.config(image=self.tk_crop, text="")

    def resize_image(self, value):
        # Resize cropped image based on slider
        if self.cropped_image is None:
            return
        percent = int(value)
        width = int(self.cropped_image.shape[1] * percent / 100)
        height = int(self.cropped_image.shape[0] * percent / 100)
        resized = cv2.resize(self.cropped_image, (width, height))
        self.resized_image = resized
        self.display_cropped_image(resized)

    def save_image(self):
        # Save the current resized image to file
        if self.resized_image is None:
            messagebox.showerror("Error", "No image to save.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg")])
        if path:
            cv2.imwrite(path, self.resized_image)
            messagebox.showinfo("Saved", "Image saved successfully.")
            
    def resize_image(self, value):
        # Resize cropped image based on slider
        if self.cropped_image is None:
            return
        percent = int(value)
        width = int(self.cropped_image.shape[1] * percent / 100)
        height = int(self.cropped_image.shape[0] * percent / 100)
        resized = cv2.resize(self.cropped_image, (width, height))
        self.resized_image = resized
        self.display_cropped_image(resized)

    def save_image(self):
        # Save the current resized image to file
        if self.resized_image is None:
            messagebox.showerror("Error", "No image to save.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg")])
        if path:
            cv2.imwrite(path, self.resized_image)
            messagebox.showinfo("Saved", "Image saved successfully.")

def apply_edge(self):
        # Apply Canny edge detection
        if self.resized_image is not None:
            gray = cv2.cvtColor(self.resized_image, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 100, 200)
            edge_bgr = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
            self.push_undo(self.resized_image.copy())
            self.resized_image = edge_bgr
            self.display_cropped_image(self.resized_image)

    def push_undo(self, image):
        # Save state for undo and clear redo stack
        self.undo_stack.append(image)
        self.redo_stack.clear()

    def undo(self):
        # Revert to previous state if possible
        if len(self.undo_stack) > 1:
            self.redo_stack.append(self.undo_stack.pop())
            self.resized_image = self.undo_stack[-1].copy()
            self.display_cropped_image(self.resized_image)

    def redo(self):
        # Redo the last undone action
        if self.redo_stack:
            self.resized_image = self.redo_stack.pop()
            self.undo_stack.append(self.resized_image.copy())
            self.display_cropped_image(self.resized_image)

# Main execution
if __name__ == "__main__":
    root = tk.Tk()
    app = ImageEditorApp(root)
    root.mainloop()
