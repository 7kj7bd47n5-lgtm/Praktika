
import pandas as pd
from io import StringIO
df = pd.read_csv("dataset.csv")
numeric_columns = [
    "Year",
    "NA_Sales",
    "EU_Sales",
    "JP_Sales",
    "Other_Sales",
    "Global_Sales"
]
category_columns = [
    "Name",
    "Platform",
    "Genre",
    "Publisher"
]
def create_report():
    report = StringIO()
    def output(*args):
        print(*args)
        print(*args, file=report)
    output("1. Размер набора данных")
    output(df.shape)
    output()
    output("2. Типы данных")
    output(df.info(buf=report) if False else "")
    info_buffer = StringIO()
    df.info(buf=info_buffer)
    output(info_buffer.getvalue().rstrip())
    output()
    output("3. Количество пропущенных значений")
    output(df.isnull().sum().to_string())
    output()
    output("4. Статистика числовых данных")
    output("Колонка\tСреднее\tМедиана\tОтклонение")
    for column in numeric_columns:
        mean = df[column].mean()
        median = df[column].median()
        std = df[column].std()
        output(
            f"{column}>\t"
            f"{mean:.2f};\t"
            f"{median:.2f};\t"
            f"{std:.2f}"
        )
    output()
    output("5. Категориальные данные")
    for column in category_columns:
        output()
        output(column)
        frequencies = df[column].value_counts(
            dropna=False
        )
        output(frequencies.to_string())
        output()
    report_path = "report.txt"
    with open(report_path, "w", encoding="utf-8") as file:
        file.write(report.getvalue())
    report.close()
    print(f"\nОтчет сохранен: {report_path}")
if __name__ == "__main__":
    create_report()