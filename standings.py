#!/usr/bin/env python3
from lib.Loader import Loader
from lib.Statistics import Statistics
from lib.Utils import get_headers, login

import gettext
import argparse

tr = gettext.translation('argparse', 'translation', ['ru'], fallback=True)
argparse._ = tr.gettext
argparse.ngettext = tr.ngettext

cool_msg = """
     __  __ _      ___ _                _ _              
    |  \/  | |    / __| |_ __ _ _ _  __| (_)_ _  __ _ ___
    | |\/| | |__  \__ \  _/ _` | ' \/ _` | | ' \/ _` (_-<
    |_|  |_|____| |___/\__\__,_|_||_\__,_|_|_||_\__, /__/
                                                |___/    

    Статист по машинке (C) ediah & s0ko1ex

"""

def new_help(func):
    def printer():
        print(cool_msg)
        func()
    return printer

if __name__ == '__main__':
    parser = argparse.ArgumentParser(usage = f'{__file__} [-h] [-u] [-t T] (-l | -s | -n N)')

    old_help = parser.print_help
    parser.print_help = new_help(old_help)

    group = parser.add_argument_group('обязательные аргументы (должен присутствовать хотя бы один)')
    parser.add_argument('-u', action='store_true', help='обновить принудительно')
    group.add_argument('-l', action='store_true', help='войти в систему из терминала')
    group.add_argument('-s', action='store_true', help='общая статистика')
    group.add_argument('-n', default='', help='поиск по фамилии с именем')
    group.add_argument('-t', default='', help='установить номер задачи для вывода смещения в позиции')
    args = parser.parse_args()

    if not (args.s or args.n or args.l):
        print(f'{__file__}: ошибка: аргументы -s, -n, -l: ожидался хотя бы один аргумент из группы')
        exit(1)

    if args.l:
        login()
        exit(0)
    
    if args.t != '' and int(args.t) < 1:
        print(f"Ожидалось T > 0, но получено {args.t} <= 0")
        exit(1)

    headers = get_headers()

    ldr = Loader(headers, args.u)
    sts = Statistics(ldr.table)

    sts.getTasks()
    dls = ldr.loadAllDeadlines(len(sts.tasks))
    sts.prepare(args.t, dls)
    
    if args.s:
        try:
            sts.statTop(args.n)
        except ValueError as err:
            if 'is not in list' in str(err):
                print('Ошибка! Имя в таблице не найдено')
                exit(1)
    else:
        if args.n == '':
            print('Не указано имя для поиска!')
            exit(1)
        
        try:
            sts.statName(args.n)
        except ValueError:
            print('Ошибка! Имя в таблице не найдено')
            exit(1)
