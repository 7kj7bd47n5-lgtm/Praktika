import io
import tkinter as tk
from tkinter import ttk, colorchooser, messagebox
from datetime import datetime
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
from matplotlib.figure import Figure
from matplotlib import colormaps
from PIL import Image, ImageTk, ImageDraw
import dataset

DATA = dataset.df
ROOT = Path(__file__).resolve().parent
NAMES = {
    'Rank': 'Рейтинг игры', 'Year': 'Год выпуска',
    'NA_Sales': 'Продажи в Северной Америке',
    'EU_Sales': 'Продажи в Европе', 'JP_Sales': 'Продажи в Японии',
    'Other_Sales': 'Продажи в других регионах',
    'Global_Sales': 'Мировые продажи', 'Name': 'Название игры',
    'Platform': 'Игровая платформа', 'Genre': 'Жанр игры',
    'Publisher': 'Издатель'
}
NUMERIC = {'Rank', 'Year', 'NA_Sales', 'EU_Sales', 'JP_Sales', 'Other_Sales', 'Global_Sales'}
CMAPS = [
    'viridis', 'plasma', 'inferno', 'magma', 'cividis', 'Greys',
    'Purples', 'Blues', 'Greens', 'Oranges', 'Reds', 'YlOrBr',
    'YlOrRd', 'OrRd', 'PuRd', 'RdPu', 'BuPu', 'GnBu', 'PuBu',
    'YlGnBu', 'PuBuGn', 'BuGn', 'YlGn', 'binary', 'gist_yarg',
    'spring', 'summer', 'autumn', 'winter'
]
WIDTH, HEIGHT = 900, 560
DEFAULT_BRUSH = '#161820'  # RGB 22, 24, 32

class GraphApp:
    def __init__(self, root):
        self.root = root
        root.title('Визуализация и рисование')
        root.geometry('1450x790')
        self.x = 'Year'
        self.y = 'NA_Sales'
        self.cmap = tk.StringVar(value='Reds')
        self.brush_color = DEFAULT_BRUSH
        self.brush_size = 7
        self.mode = False
        self.drawing = False
        self.strokes = []
        self.current = None
        self.undo_target = None
        self.base = None
        self.photo = None
        self.plot_bounds = (0, 0, WIDTH, HEIGHT)

        toolbar = tk.Frame(root)
        toolbar.pack(fill='x', padx=6, pady=6)
        tk.Label(toolbar, text='Цветовая схема:').pack(side='left')
        chooser = ttk.Combobox(toolbar, textvariable=self.cmap,
                               values=CMAPS, state='readonly', width=16)
        chooser.pack(side='left', padx=6)
        chooser.bind('<<ComboboxSelected>>', lambda e: self.update_plot())
        self.mode_button = tk.Button(toolbar, text='Рисование', width=14,
                                     command=self.toggle_mode)
        self.mode_button.pack(side='left', padx=12)
        tk.Label(toolbar, text='Толщина:').pack(side='left')
        self.thickness = tk.StringVar(value='7')
        spin = tk.Spinbox(toolbar, from_=1, to=50, width=5,
                          textvariable=self.thickness, command=self.update_thickness)
        spin.pack(side='left', padx=5)
        spin.bind('<Return>', self.update_thickness)
        spin.bind('<FocusOut>', self.update_thickness)
        tk.Label(toolbar, text='Цвет:').pack(side='left', padx=(12, 4))
        self.color_button = tk.Button(toolbar, bg=self.brush_color, width=4,
                                      command=self.choose_color)
        self.color_button.pack(side='left')

        body = tk.Frame(root)
        body.pack(fill='both', expand=True, padx=6)
        left = tk.Frame(body)
        left.pack(side='left', fill='y')
        center = tk.Frame(body)
        center.pack(side='left', fill='both', expand=True)
        tk.Label(left, text='Ось Y', font=('Arial', 10, 'bold')).pack(pady=3)
        for col, title in NAMES.items():
            tk.Button(left, text=title, width=29,
                      command=lambda c=col: self.choose_axis('y', c)).pack(fill='x', pady=2)
        tk.Button(left, text='Сохранить график', command=self.save).pack(
            side='bottom', fill='x', pady=8)

        self.canvas = tk.Canvas(center, width=WIDTH, height=HEIGHT,
                                bg='white', highlightthickness=1)
        self.canvas.pack(side='top', padx=4, pady=4)
        self.canvas.bind('<ButtonPress-1>', self.begin_stroke)
        self.canvas.bind('<B1-Motion>', self.move_stroke)
        self.canvas.bind('<ButtonRelease-1>', self.end_stroke)
        root.bind_all('<Button-3>', self.right_click)
        root.bind_all('<Control-z>', self.undo)
        root.bind_all('<Control-Z>', self.undo)

        tk.Label(center, text='Ось X', font=('Arial', 10, 'bold')).pack()
        bar = tk.Frame(center)
        bar.pack(fill='x')
        bottom = tk.Canvas(bar, height=52, highlightthickness=0)
        scroll = tk.Scrollbar(bar, orient='horizontal', command=bottom.xview)
        bottom.configure(xscrollcommand=scroll.set)
        bottom.pack(fill='x')
        scroll.pack(fill='x')
        buttons = tk.Frame(bottom)
        bottom.create_window((0, 0), window=buttons, anchor='nw')
        for col, title in NAMES.items():
            tk.Button(buttons, text=title, width=19, wraplength=130,
                      command=lambda c=col: self.choose_axis('x', c)).pack(side='left', padx=1)
        buttons.update_idletasks()
        bottom.configure(scrollregion=bottom.bbox('all'))
        self.update_plot()

    def colors(self, n):
        cm = colormaps[self.cmap.get()]
        return [cm(float(v)) for v in np.linspace(.12, .88, max(n, 1))]

    def make_figure(self):
        fig = Figure(figsize=(WIDTH / 100, HEIGHT / 100), dpi=100)
        ax = fig.add_subplot(111)
        xn, yn = self.x in NUMERIC, self.y in NUMERIC
        cx, cy = self.x, self.y
        cm = colormaps[self.cmap.get()]

        if cx == cy and xn:
            values = pd.to_numeric(DATA[cx], errors='coerce').dropna()
            ax.hist(values, bins=10, color=cm(.7), edgecolor='black')
            ax.set(xlabel=NAMES[cx], ylabel='Количество записей', title='Гистограмма')
        elif cx == cy and not xn:
            counts = DATA[cx].fillna('Нет данных').astype(str).value_counts()
            wedges, _ = ax.pie(counts.to_numpy(), colors=self.colors(len(counts)),
                               startangle=90)
            if len(counts) <= 20:
                ax.legend(wedges, counts.index, loc='center left',
                          bbox_to_anchor=(1, .5), fontsize=7)
            else:
                ax.text(.5, -.07, f'Всего категорий: {len(counts)}',
                        transform=ax.transAxes, ha='center', fontsize=9)
            ax.set_title('Круговая диаграмма: ' + NAMES[cx])
        elif xn and not yn:
            temp = DATA[[cx, cy]].copy()
            temp[cx] = pd.to_numeric(temp[cx], errors='coerce')
            temp = temp.dropna()
            groups = temp.groupby(cy, sort=False)[cx]
            labels, values = [], []
            for label, series in groups:
                if not series.empty:
                    labels.append(str(label))
                    values.append(series.to_numpy())
            if values:
                bp = ax.boxplot(values, vert=False, patch_artist=True,
                                showfliers=False, manage_ticks=False)
                for patch, color in zip(bp['boxes'], self.colors(len(values))):
                    patch.set_facecolor(color)
                # Не исключаем категории из расчета, ограничиваем только подписи.
                step = max(1, int(np.ceil(len(labels) / 16)))
                positions = list(range(1, len(labels) + 1, step))
                ax.set_yticks(positions)
                ax.set_yticklabels([labels[p-1][:24] for p in positions], fontsize=7)
                ax.set_ylim(.5, len(labels) + .5)
            ax.set(xlabel=NAMES[cx], ylabel=NAMES[cy], title='Коробочная диаграмма')
        elif not xn and yn:
            counts = DATA[cx].fillna('Нет данных').astype(str).value_counts()
            ax.bar(np.arange(len(counts)), counts.to_numpy(),
                   color=self.colors(len(counts)))
            step = max(1, int(np.ceil(len(counts) / 16)))
            positions = np.arange(0, len(counts), step)
            ax.set_xticks(positions)
            ax.set_xticklabels([str(counts.index[p])[:20] for p in positions],
                               rotation=45, ha='right', fontsize=7)
            ax.set(xlabel=NAMES[cx], ylabel='Количество записей',
                   title='Столбчатая диаграмма')
        else:
            temp = DATA[[cx, cy]].dropna()
            def coords(col):
                if col in NUMERIC:
                    return pd.to_numeric(temp[col], errors='coerce').to_numpy()
                return pd.Categorical(temp[col].astype(str)).codes
            ax.scatter(coords(cx), coords(cy), color=cm(.7), marker='s',
                       s=12, alpha=.7)
            ax.set(xlabel=NAMES[cx], ylabel=NAMES[cy], title='Точечная диаграмма')

        fig.tight_layout(pad=1.6)
        return fig, ax

    def update_plot(self):
        fig, ax = self.make_figure()
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', dpi=100)
        buffer.seek(0)
        with Image.open(buffer) as img:
            self.base = img.convert('RGB').copy()
        buffer.close()
        bounds = ax.get_window_extent()
        self.plot_bounds = (bounds.x0, HEIGHT - bounds.y1,
                            bounds.x1, HEIGHT - bounds.y0)
        self.strokes.clear()
        self.current = None
        self.drawing = False
        self.undo_target = None
        self.refresh()

    def refresh(self):
        self.photo = ImageTk.PhotoImage(self.base)
        self.canvas.delete('all')
        self.canvas.create_image(0, 0, image=self.photo, anchor='nw')
        for stroke in self.strokes:
            self.paint_canvas(stroke)
        if self.current:
            self.paint_canvas(self.current)

    def paint_canvas(self, stroke):
        points, color, size = stroke['points'], stroke['color'], stroke['size']
        if not points:
            return
        half = size / 2
        x, y = points[0]
        self.canvas.create_rectangle(x-half, y-half, x+half, y+half,
                                     fill=color, outline=color)
        if len(points) > 1:
            flat = [coordinate for point in points for coordinate in point]
            self.canvas.create_line(*flat, fill=color, width=size,
                                    capstyle=tk.PROJECTING, joinstyle=tk.ROUND)

    def choose_axis(self, axis, column):
        self.disable_mode()
        if axis == 'x':
            self.x = column
        else:
            self.y = column
        self.update_plot()

    def toggle_mode(self):
        self.mode = not self.mode
        self.mode_button.config(relief=tk.SUNKEN if self.mode else tk.RAISED)
        self.canvas.config(cursor='pencil' if self.mode else '')

    def disable_mode(self):
        if self.mode:
            self.toggle_mode()

    def update_thickness(self, event=None):
        try:
            size = int(self.thickness.get())
            if not 1 <= size <= 50:
                raise ValueError
            self.brush_size = size
        except ValueError:
            self.thickness.set(str(self.brush_size))
            messagebox.showwarning('Толщина', 'Введите целое число от 1 до 50')

    def choose_color(self):
        _, value = colorchooser.askcolor(color=self.brush_color,
                                         title='Выбор цвета кисти')
        if value:
            self.brush_color = value
            self.color_button.config(bg=value, activebackground=value)

    def inside(self, x, y):
        x0, y0, x1, y1 = self.plot_bounds
        margin = self.brush_size / 2
        return x0+margin <= x <= x1-margin and y0+margin <= y <= y1-margin

    def begin_stroke(self, event):
        if not self.mode or not self.inside(event.x, event.y):
            return
        self.drawing = True
        self.undo_target = None
        self.current = {'points': [(event.x, event.y)],
                        'color': self.brush_color, 'size': self.brush_size}
        self.refresh()

    def move_stroke(self, event):
        if not self.drawing:
            return
        if self.inside(event.x, event.y):
            self.current['points'].append((event.x, event.y))
            self.refresh()

    def end_stroke(self, event):
        if not self.drawing:
            return
        self.strokes.append(self.current)
        self.undo_target = self.current
        self.current = None
        self.drawing = False
        self.refresh()

    def right_click(self, event):
        if self.drawing:
            self.end_stroke(event)
        self.disable_mode()

    def undo(self, event=None):
        if self.drawing or self.undo_target is None:
            return
        if self.strokes and self.strokes[-1] is self.undo_target:
            self.strokes.pop()
            self.undo_target = None
            self.refresh()

    def save(self):
        if self.base is None:
            return
        result = self.base.copy()
        painter = ImageDraw.Draw(result)
        for stroke in self.strokes:
            points, color, size = stroke['points'], stroke['color'], stroke['size']
            if not points:
                continue
            x, y = points[0]
            h = size / 2
            painter.rectangle((round(x-h), round(y-h), round(x+h), round(y+h)),
                              fill=color)
            if len(points) > 1:
                painter.line(points, fill=color, width=size, joint='curve')
        path = ROOT / datetime.now().strftime('graph%H_%M_%S.png')
        result.save(path)
        messagebox.showinfo('Сохранение', f'График сохранён:\n{path}')


if __name__ == '__main__':
    app_root = tk.Tk()
    GraphApp(app_root)
    app_root.mainloop()
