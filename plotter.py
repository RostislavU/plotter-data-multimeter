# -*- coding: utf-8 -*-

import os
import pandas as pd
import json
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.ticker import MultipleLocator, FormatStrFormatter, AutoMinorLocator, NullFormatter

import argparse

PATH = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = 'images'

# TODO: Локализация и сохранение пиков
# TODO: Расчёт времени между пиками (указать примерное место можно даже)

to_float = lambda x: float(x.replace(',', '.'))

# Получение параметров
parser = argparse.ArgumentParser()

parser.add_argument("--drop",
                    action="store_true",
                    dest="drop_value",
                    default=False)

parser.add_argument("--table",
                    action="store_true",
                    dest="make_table",
                    default=False)

parser.add_argument("--format",
                    action="store",
                    dest="format",
                    default="format.json")

settings = vars(parser.parse_args())


with open(settings['format']) as f:
    frm = json.load(f)['data']
    columns = frm['columns']
    borders = frm['borders']
    fig_size = tuple(frm['fig_size'])

    focus_keys = frm['focus_keys']
    focus_numbers = list(map(lambda item: item.get('value'), focus_keys.values()))
    focus_numbers += list(filter(lambda item: item, map(lambda item: item.get('task'), focus_keys.values())))

    # Задание псевдо_констант
    SEP = frm.get('sep', ";")
    DATE_COLUMN = columns.get(str(focus_keys['date']['value']), None)
    TIME_COLUMN = columns.get(str(focus_keys['time']['value']))

    CHANEL1 = {
        'task':  columns.get(str(focus_keys['chanel1']['task']), None),
        'task_label': focus_keys.get('chanel1', None).get('task_label', None),
        'value': columns.get(str(focus_keys['chanel1']['value'])),
        'value_label': focus_keys.get('chanel1', None).get('value_label', None)
    }

    CHANEL2 = {
        'task': columns.get(str(focus_keys['chanel2']['task']), None),
        'task_label': focus_keys.get('chanel2', None).get('task_label', None),
        'value': columns.get(str(focus_keys['chanel2']['value']), None),
        'value_label': focus_keys.get('chanel2', None).get('value_label', None)
    }


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

    index_col = []
    if DATE_COLUMN:
        index_col.append(DATE_COLUMN)
    index_col.append(TIME_COLUMN)

    # Поиск всех подходящих файлов для получения данных из текущей папки

    filenames = find('.csv', PATH)

    if settings['make_table']:
        print('|| График || Ток на АКБ || Ток на USB || Длительность || ')

    for fname in filenames:

        # Подготовить данные
        all_columns = list(columns.values())
        focus_columns = list(map(lambda x: x[1], list(filter(lambda item: int(item[0]) in focus_numbers, columns.items()))))

        data = pd.read_csv(fname,
                           sep=SEP,
                           infer_datetime_format=False,
                           parse_dates=False,
                           header=None,
                           index_col=index_col,
                           names=all_columns)

        data = data.drop(columns=list(set(all_columns)-set(focus_columns)))

        # Перевести во float

        for column in {CHANEL1['task'], CHANEL1['value'], CHANEL2['task'], CHANEL2['value']}:
            if column:
                if ',' in str(data[column].values[1]):
                    data[column] = data[column].map(to_float)
        # Исключить лишние данные, меньше какого-то значения

        # В случае, если среднее значение меньше нуля, то инвертируем значение всех знаков
        if data[CHANEL1['value']].mean() < 0:
            data[CHANEL1['value']] = data[CHANEL1['value']].map(lambda x: -1 * x)

        if CHANEL2['value']:
            average = data[CHANEL2['value']].mean()

            if data[CHANEL2['value']].mean() < 0:
                data[CHANEL2['value']] = data[CHANEL2['value']].map(lambda x: -1 * x)
                average *= -1

            if settings['make_table']:
                print('| ' + fname + ' | ' + str(average)[:5] + ' A | |  |')

        if settings['drop_value']:

            data = data.drop(data[data[CHANEL1['value']] > borders['max_chanel1']].index)
            data = data.drop(data[data[CHANEL1['value']] < borders['min_chanel1']].index)

            if CHANEL1['task']:
                data = data.drop(data[data[CHANEL1['task']] > borders['max_chanel1']].index)
                data = data.drop(data[data[CHANEL1['task']] < borders['min_chanel1']].index)

            if CHANEL2['task']:
                data = data.drop(data[data[CHANEL2['task']] > borders['max_chanel2']].index)
                data = data.drop(data[data[CHANEL2['task']] < borders['min_chanel2']].index)

            if CHANEL2['value']:
                data = data.drop(data[data[CHANEL2['value']] > borders['max_chanel2']].index)
                data = data.drop(data[data[CHANEL2['value']] < borders['min_chanel2']].index)

        if not data.size:
            msg = 'После всех преобразований данных не осталось.\n'
            if settings['drop_value']:
                msg += 'Попробуйте запустить без ключа --drop.'
            print(msg)
            exit(-1)

        # Настройка фигуры
        if CHANEL2['value']:
            fig, axes = plt.subplots(nrows=2, ncols=1, figsize=fig_size)

            data[CHANEL1['value']].plot(ax=axes[0], color="orange", label=CHANEL1['value_label'])
            if CHANEL1['task']:
                data[CHANEL1['task']].plot(ax=axes[0], color='#FF7600', linestyle='--', label=CHANEL1['task_label'])

            axes[0].legend(loc='right', bbox_to_anchor=(1.12, 0.5), shadow=True)
            axes[0].minorticks_on()
            axes[0].set_xlabel(r'Время', fontsize=12)
            axes[0].set_ylabel(r'Температура', fontsize=12)
            axes[0].grid(which='minor', linewidth=0.4, alpha=0.3)
            axes[0].grid(which='major', linewidth=1, alpha=0.6)

            data[CHANEL2['value']].plot(ax=axes[1], color="blue", label=CHANEL2['value_label'])
            if CHANEL2['task']:
                data[CHANEL2['task']].plot(ax=axes[1], color='#009999', linestyle='--', label=CHANEL2['task_label'])
            axes[1].legend(loc='right', bbox_to_anchor=(1.12, 0.5), shadow=True)
            axes[1].minorticks_on()
            axes[1].set_xlabel(r'Время', fontsize=12)
            axes[1].set_ylabel(r'Влажность', fontsize=12)
            axes[1].grid(which='minor', linewidth=0.4, alpha=0.3)
            axes[1].grid(which='major', linewidth=1, alpha=0.6)

        else:
            fig, axes = plt.subplots(nrows=1, ncols=1, figsize=fig_size)

            data[CHANEL1['value']].plot(ax=axes, color="orange", label=CHANEL1['value_label'])
            if CHANEL1['task']:
                data[CHANEL1['task']].plot(ax=axes, color='#FF7600', linestyle='--', label=CHANEL1['task_label'])
            axes.minorticks_on()
            axes.set_xlabel(r'Время', fontsize=12)
            axes.set_ylabel(r'Напряжение', fontsize=12)
            axes.grid(which='minor', linewidth=0.4, alpha=0.3)
            axes.grid(which='major', linewidth=1, alpha=0.6)
            axes.legend(loc='upper center', bbox_to_anchor=(1.12, 0.5), shadow=True)

        outFileName = fname[:-4] + '.png'
        # fig.set_figwidth(12)
        # fig.set_figheight(8)

        if not os.path.exists(OUTPUT_PATH):
            os.mkdir(OUTPUT_PATH)

        # Результат
        plt.savefig(os.path.join(OUTPUT_PATH, outFileName))
        mng = plt.get_current_fig_manager()
        mng.window.state('zoomed')
