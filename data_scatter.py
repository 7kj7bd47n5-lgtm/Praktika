
import io
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox
import matplotlib
matplotlib.use("Agg")
from matplotlib.figure import Figure
from PIL import Image, ImageTk
import dataset
df = dataset.df

columns = {
    "Year": "Год выпуска",
    "NA_Sales": "Продажи в C.Америке",
    "EU_Sales": "Продажи в Европе",
    "JP_Sales": "Продажи в Японии",
    "Other_Sales": "Продажи в регионах",
    "Global_Sales": "Мировые продажи"
}
x_column = "Year"
y_column = "NA_Sales"
BASE_DIR = Path(__file__).resolve().parent
current_figure = None
current_image = None
canvas = None
def create_graph():
    global current_figure
    data = df[[x_column, y_column]].dropna()
    fig = Figure(figsize=(8, 5), dpi=100)
    ax = fig.add_subplot(111)
    ax.scatter(
        data[x_column],
        data[y_column],
        color="blue",
        marker="s",
        s=12
    )
    ax.set_xlabel(columns[x_column])
    ax.set_ylabel(columns[y_column])
    fig.tight_layout()
    current_figure = fig
    return fig
def update_graph():
    global current_image
    fig = create_graph()
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=100)
    buffer.seek(0)
    with Image.open(buffer) as image:
        current_image = ImageTk.PhotoImage(image.copy())
    buffer.close()
    canvas.delete("all")
    canvas.create_image(
        0, 0,
        anchor=tk.NW,
        image=current_image
    )
def select_x(column):
    global x_column
    x_column = column
    update_graph()

def select_y(column):
    global y_column
    y_column = column
    update_graph()

def save_graph():
    if current_figure is None:
        return
    filename = datetime.now().strftime(
        "graph%H_%M_%S.png"
    )
    filepath = BASE_DIR / filename
    current_figure.savefig(
        filepath,
        format="png",
        dpi=100
    )
    messagebox.showinfo(
        "Сохранение графика",
        f"График успешно сохранён:\n{filepath}"
    )
def main():
    global canvas
    window = tk.Tk()
    window.title("Система визуализации данных")
    window.geometry("1250x650")
    main_frame = tk.Frame(window)
    main_frame.pack(
        fill=tk.BOTH,
        expand=True,
        padx=5,
        pady=5
    )
    left_frame = tk.Frame(main_frame)
    left_frame.pack(
        side=tk.LEFT,
        fill=tk.Y
    )
    center_frame = tk.Frame(main_frame)
    center_frame.pack(
        side=tk.LEFT,
        fill=tk.BOTH,
        expand=True
    )
    for column, russian_name in columns.items():
        button = tk.Button(
            left_frame,
            text=russian_name,
            width=29,
            command=lambda c=column: select_y(c)
        )
        button.pack(fill=tk.X, pady=2)
    save_button = tk.Button(
        left_frame,
        text="Сохранить график",
        command=save_graph
    )
    save_button.pack(
        side=tk.BOTTOM,
        anchor=tk.W,
        pady=5
    )
    canvas = tk.Canvas(
        center_frame,
        width=800,
        height=520,
        bg="white"
    )
    canvas.pack(
        side=tk.TOP,
        fill=tk.BOTH,
        expand=True
    )
    bottom_frame = tk.Frame(center_frame)
    bottom_frame.pack(
        side=tk.BOTTOM,
        fill=tk.X
    )
    for column, russian_name in columns.items():
        button = tk.Button(
            bottom_frame,
            text=russian_name,
            command=lambda c=column: select_x(c),
            wraplength=125
        )
        button.pack(
            side=tk.LEFT,
            fill=tk.X,
            expand=True,
            padx=1
        )
    update_graph()
    window.mainloop()
if __name__ == "__main__":
    main()
