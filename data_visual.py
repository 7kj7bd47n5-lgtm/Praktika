
import io
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")

from matplotlib.figure import Figure
from matplotlib import colormaps
from PIL import Image, ImageTk

import dataset
df = dataset.df
columns = {
    "Year": "Год выпуска",
    "NA_Sales": "Продажи в C.Америке",
    "EU_Sales": "Продажи в Европе",
    "JP_Sales": "Продажи в Японии",
    "Other_Sales": "Продажи в регионах",
    "Global_Sales": "Мировые продажи",
    "Rank": "Рейтинг игры",
    "Name": "Название игры",
    "Platform": "Платформа",
    "Genre": "Жанр игры",
    "Publisher": "Издатель"
}
numeric_columns = [
    "Year", "NA_Sales", "EU_Sales",
    "JP_Sales", "Other_Sales", "Global_Sales"
]
category_columns = [
    "Rank", "Name", "Platform",
    "Genre", "Publisher"
]
color_maps = [
    "viridis", "plasma", "inferno", "magma",
    "cividis", "Greys", "Purples", "Blues",
    "Greens", "Oranges", "Reds", "YlOrBr",
    "YlOrRd", "OrRd", "PuRd", "RdPu",
    "BuPu", "GnBu", "PuBu", "YlGnBu",
    "PuBuGn", "BuGn", "YlGn", "binary",
    "gist_yarg", "spring", "summer",
    "autumn", "winter"
]
x_column = "Year"
y_column = "NA_Sales"
selected_cmap = "Reds"
BASE_DIR = Path(__file__).resolve().parent
current_figure = None
current_image = None
canvas = None

MAX_CATEGORIES = 15
def get_colors(count):
    cmap = colormaps[selected_cmap]
    if count <= 1:
        return [cmap(0.65)]
    return [
        cmap(value)
        for value in np.linspace(0.15, 0.9, count)
    ]
def category_counts(column):
    counts = df[column].fillna(
        "Нет данных"
    ).astype(str).value_counts()
    if len(counts) > MAX_CATEGORIES:
        main = counts.iloc[:MAX_CATEGORIES].copy()
        other = counts.iloc[MAX_CATEGORIES:].sum()

        main.loc["Остальные"] = other
        return main

    return counts

def create_graph():
    global current_figure
    fig = Figure(figsize=(8.5, 5.6), dpi=100)
    ax = fig.add_subplot(111)
    x_numeric = x_column in numeric_columns
    y_numeric = y_column in numeric_columns
    x_name = columns[x_column]
    y_name = columns[y_column]
    cmap = colormaps[selected_cmap]

    if x_column == y_column and x_numeric:
        values = df[x_column].dropna()
        ax.hist(
            values,
            bins=10,
            color=cmap(0.7),
            edgecolor="black"
        )
        ax.set_xlabel(x_name)
        ax.set_ylabel("Количество записей")
        ax.set_title("Гистограмма распределения")

    elif x_column == y_column and not x_numeric:
        counts = category_counts(x_column)
        ax.pie(
            counts.values,
            labels=counts.index,
            colors=get_colors(len(counts)),
            autopct="%1.1f%%" if len(counts) <= 12
            else None,
            startangle=90,
            textprops={"fontsize": 8}
        )
        ax.set_title(
            f"Распределение по категориям: {x_name}"
        )

    elif not x_numeric and y_numeric:
        counts = category_counts(x_column)
        ax.bar(
            range(len(counts)),
            counts.values,
            color=get_colors(len(counts))
        )
        ax.set_xticks(range(len(counts)))
        ax.set_xticklabels(
            counts.index,
            rotation=40,
            ha="right",
            fontsize=8
        )
        ax.set_xlabel(x_name)
        ax.set_ylabel("Количество записей")
        ax.set_title("Столбчатая диаграмма")

    elif x_numeric and not y_numeric:
        data = df[[x_column, y_column]].dropna()
        categories = (
            data[y_column]
            .value_counts()
            .head(MAX_CATEGORIES)
            .index
        )
        groups = []
        labels = []

        for category in categories:
            values = data.loc[
                data[y_column] == category,
                x_column
            ].dropna().values

            if len(values) > 0:
                groups.append(values)
                labels.append(str(category))

        if groups:
            result = ax.boxplot(
                groups,
                orientation="horizontal",
                patch_artist=True,
                tick_labels=labels
            )

            colors = get_colors(len(groups))

            for patch, color in zip(
                result["boxes"], colors
            ):
                patch.set_facecolor(color)

            ax.tick_params(axis="y", labelsize=8)

        ax.set_xlabel(x_name)
        ax.set_ylabel(y_name)
        ax.set_title("Коробочная диаграмма")

    else:
        data = df[[x_column, y_column]].dropna()

        # Преобразуем категории в числовые коды
        if x_numeric:
            x_values = data[x_column]
        else:
            x_values = data[x_column].astype(
                "category"
            ).cat.codes

        if y_numeric:
            y_values = data[y_column]
        else:
            y_values = data[y_column].astype(
                "category"
            ).cat.codes

        ax.scatter(
            x_values,
            y_values,
            color=cmap(0.7),
            marker="s",
            s=12,
            alpha=0.65
        )

        ax.set_xlabel(x_name)
        ax.set_ylabel(y_name)
        ax.set_title("Точечная диаграмма")

        if not x_numeric:
            cats = data[x_column].astype(
                "category"
            ).cat.categories

            if len(cats) <= 15:
                ax.set_xticks(range(len(cats)))
                ax.set_xticklabels(
                    cats, rotation=40,
                    ha="right", fontsize=8
                )

        if not y_numeric:
            cats = data[y_column].astype(
                "category"
            ).cat.categories

            if len(cats) <= 15:
                ax.set_yticks(range(len(cats)))
                ax.set_yticklabels(
                    cats, fontsize=8
                )

    fig.tight_layout(pad=2)
    current_figure = fig

    return fig


def update_graph():
    global current_image
    fig = create_graph()
    buffer = io.BytesIO()
    fig.savefig(
        buffer,
        format="png",
        dpi=100
    )
    buffer.seek(0)

    with Image.open(buffer) as image:
        current_image = ImageTk.PhotoImage(
            image.copy()
        )
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

def change_cmap(event=None):
    global selected_cmap
    selected_cmap = cmap_box.get()
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
        "Сохранение",
        f"График сохранён:\n{filepath}"
    )

def main():
    global canvas, cmap_box
    window = tk.Tk()
    window.title("Система визуализации данных")
    window.geometry("1350x780")
    top_frame = tk.Frame(window)
    top_frame.pack(
        side=tk.TOP,
        fill=tk.X,
        padx=5,
        pady=5
    )
    tk.Label(
        top_frame,
        text="Цветовая схема:"
    ).pack(side=tk.LEFT, padx=5)
    cmap_box = ttk.Combobox(
        top_frame,
        values=color_maps,
        state="readonly",
        width=20
    )

    cmap_box.set(selected_cmap)
    cmap_box.pack(side=tk.LEFT)

    cmap_box.bind(
        "<<ComboboxSelected>>",
        change_cmap
    )

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

        button.pack(
            fill=tk.X,
            pady=2
        )

    save_button = tk.Button(
        left_frame,
        text="Сохранить график",
        command=save_graph
    )

    save_button.pack(
        side=tk.BOTTOM,
        fill=tk.X,
        pady=5
    )

    canvas = tk.Canvas(
        center_frame,
        width=850,
        height=560,
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
            wraplength=110,
            command=lambda c=column: select_x(c)
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
