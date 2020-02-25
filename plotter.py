# -*- coding: utf-8 -*-

import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.ticker import MultipleLocator, FormatStrFormatter, AutoMinorLocator, NullFormatter

import argparse

MIN_VALUE = -0.002
PATH = os.path.dirname(os.path.abspath(__file__))

# TODO: Локализация и сохранение пиков
# TODO: Расчёт времени между пиками (указать примерное место можно даже)

to_float = lambda x: float(x.replace(',', '.'))

MIN_VOLTAGE = 3.4
MAX_VOLTAGE = 4.3
MIN_CURRENT = -1
MAX_CURRENT = 2.2

# Получение параметров
parser = argparse.ArgumentParser()
parser.add_argument("--drop",
                    action="store_true",
                    dest="drop_value",
                    default=False)
parser.add_argument("--date",
                    action="store_true",
                    dest="add_date",
                    default=False)

parser.add_argument("--current",
                    action="store_true",
                    dest="current",
                    default=False)

parser.add_argument("--table",
                    action="store_true",
                    dest="make_table",
                    default=False)

settings = vars(parser.parse_args())


def find(pattern, path):
    result, delete = os.listdir(path), []
    for name in result:
        if not name.endswith(pattern):
            delete.append(name)
    for delname in delete:
        result.remove(delname)
    if not len(result):
        raise FileNotFoundError
    return result


if __name__ == "__main__":

    # Настроить параметры работы скрипта
    pd.options.display.max_columns = 20

    if settings['add_date']:
        index_col = ['date', 'timeStart']
    else:
        index_col = ['timeStart']

    # Поиск всех подходящих файлов для получения данных из текущей папки

    filenames = find('.csv', PATH)
    if settings['make_table']:
        print('|| График || Ток на АКБ || Ток на USB || ')

    for fname in filenames:

        # Подготовить данные
        data = pd.read_csv(fname,
                           sep=';',
                           infer_datetime_format=False,
                           parse_dates=False,
                           header=None,
                           index_col=index_col,
                           names=[
                               'date', 'timeStart', 'chanel1', 'value1', '@1',
                               'timeMiddle', 'chanel2', 'value2', '@2',
                               'timeEnd'
                           ])
        data = data.drop(columns=['chanel1', '@1', 'chanel2', '@2'] +
                         ['timeMiddle', 'timeEnd'])

        # Обработать данные

        # Перевести во float
        data['value1'] = data['value1'].map(to_float)
        if settings['current']:
            data['value2'] = data['value2'].map(to_float)

        # Исключить лишние данные, меньше какого-то значения

        # В случае, если среднее значение меньше нуля, то инвертируем значение всех знаков
        if data['value1'].mean() < 0:
            data['value1'] = data['value1'].map(lambda x: -1 * x)

        if settings['current']:
            average = data['value2'].mean()

            if data['value2'].mean() < 0:
                data['value2'] = data['value2'].map(lambda x: -1 * x)
                average *= -1

            if settings['make_table']:
                print('| ' + fname + ' | ' + str(average)[:5] + ' A |  |')

        if settings['drop_value']:
            data = data.drop(data[data.value1 < MIN_VOLTAGE].index)
            data = data.drop(data[data.value1 > MAX_VOLTAGE].index)
            if settings['current']:
                data = data.drop(data[data.value2 < MAX_CURRENT].index)
                data = data.drop(data[data.value2 > MIN_CURRENT].index)

        # Настройка фигуры
        if settings['current']:
            fig, axes = plt.subplots(nrows=2, ncols=1, figsize=(24, 8))

            data['value1'].plot(ax=axes[0], color="orange")
            axes[0].minorticks_on()
            axes[0].set_xlabel(r'Время', fontsize=12)
            axes[0].set_ylabel(r'Напряжение', fontsize=12)
            axes[0].grid(which='minor', linewidth=0.4, alpha=0.3)
            axes[0].grid(which='major', linewidth=1, alpha=0.6)

            data['value2'].plot(ax=axes[1], color="blue")
            axes[1].minorticks_on()
            axes[1].set_xlabel(r'Время', fontsize=12)
            axes[1].set_ylabel(r'Ток', fontsize=12)
            axes[1].grid(which='minor', linewidth=0.4, alpha=0.3)
            axes[1].grid(which='major', linewidth=1, alpha=0.6)

        else:
            fig, axes = plt.subplots(nrows=1, ncols=1, figsize=(24, 8))

            data['value1'].plot(ax=axes, color="orange")
            axes.minorticks_on()
            axes.set_xlabel(r'Время', fontsize=12)
            axes.set_ylabel(r'Напряжение', fontsize=12)
            axes.grid(which='minor', linewidth=0.4, alpha=0.3)
            axes.grid(which='major', linewidth=1, alpha=0.6)

        outFileName = fname[:-4] + '.png'
        # fig.set_figwidth(12)
        # fig.set_figheight(8)

        # Результат
        plt.savefig('img_all_graph\\' + outFileName)
        mng = plt.get_current_fig_manager()
        mng.window.state('zoomed')
