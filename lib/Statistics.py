from lib.Plotter import Plotter
from math import sqrt
from scipy.special import erf, erfinv
from collections import OrderedDict
from datetime import datetime
import numpy as np

COLOUR_GREEN = '\033[32m'
COLOUR_RED = '\033[31m'
COLOUR_END = '\033[0m'

class Statistics:
    def __init__(self, loader, tp, delIdle = False):
        self.table = loader.table
        self.lastTaskNum = None
        self.tasks = None
        
        self.getTasks()
        dls = loader.loadAllDeadlines(len(self.tasks))
        # Удаление баллов, которые можно было получить только должникам
        self.tasks = self.tasks[:15] + self.tasks[17:]
        dls = dls[:15] + dls[17:]
        del self.table['Зачетный тест']
        del self.table['Тест пересдача']
        ###
        self.sortTableTasks(dls)
        self.sortTasks(dls)
        if delIdle:
            self.deleteIdlers()
        self.setTimePoint(tp)
        self.mean, self.stdev = self.calcZ()
        self.statOldPos()

    def deleteIdlers(self):
        misses = []
        for x in zip(*self.table.values()):
            missed = sum([e == '' for e in list(x)[:self.lastTaskNum]])
            misses += [missed]
        mean = sum(misses) / len(misses)
        #d = [(x - mean) ** 2 for x in misses]
        #std = (sum(d) / len(d)) ** .5
        indexes = [x <= round(mean) for x in misses]
        oldkeys = list(self.table.keys())
        oldvals = list(zip(*self.table.values()))

        newvals = np.array(oldvals)[indexes].T
        self.table = dict(zip(oldkeys, newvals))

    def setTimePoint(self, tp):
        if (tp != '') and (int(tp) - 1 >= self.lastTaskNum):
            print(f"Ещё не наступил дедлайн задания №{tp}. Выберите число < {self.lastTaskNum + 1}.")
            exit(1)
        
        self.lastTaskNum = self.lastTaskNum if tp == '' else int(tp)
        
        keys = list(self.table.keys())
        to_delete = keys[self.lastTaskNum + 4 :]
        for key in to_delete:
            if key == 'Сумма':
                continue
            del self.table[key]
        
        matrix = []
        for i, key in enumerate(self.table.keys()):
            if (i >= 1) and (i <= self.lastTaskNum + 2):
                row = [float(x) if x != '' else 0 for x in self.table[key]]
                matrix += [row]

        self.table['Сумма'] = np.sum(np.array(matrix), axis = 0).tolist()

    def getTasks(self):
        tasks = list(self.table.keys())
        tasks = tasks[:tasks.index('Сумма')]
        self.tasks = list(OrderedDict.fromkeys(tasks))[1:]
    
    def sortTasks(self, dls):
        key = lambda pair: pair[0]
        srt = sorted(zip(dls, self.tasks), key=key)
        self.tasks = [x for _, x in srt]
        
        dls = sorted(dls)
        self.lastTaskNum = sum([datetime.now() > x for x in dls]) - 2
    
    def sortTableTasks(self, dls):
        tailIdx = list(self.table.keys()).index('Сумма') - 1
        tableTasks = list(self.table.items())[1:]
        tableTasks = tableTasks[:tailIdx]

        tableHead = list(self.table.items())[:1]
        tableTail = list(self.table.items())[tailIdx:]

        # Ключ: извлечение срока сдачи/рецензирования задания
        key = lambda pair: dls[self.tasks.index(pair[0])]
        tableTasks = sorted(tableTasks, key=key)
        
        table = tableHead + tableTasks + tableTail
        self.table = dict(table)

    def sortBy(self, name, desc = False):
        if isinstance(self.table[name][0], str):
            sortKey = lambda pair: float(pair[0].split()[-1]) if len(pair[0]) > 0 else 10**5
        else:
            sortKey = lambda pair: pair[0]
        
        for key in self.table.keys():
            if name == key:
                continue

            X = self.table[key]
            Y = self.table[name]

            srt = sorted(zip(Y, X), key=sortKey, reverse = desc)
            self.table[key] = [x for _, x in srt]
        
        self.table[name] = sorted(self.table[name], key=float, reverse = desc)
    
    def maxScore(self):
        score = 0
        keys = list(self.table.keys())
        for key in keys[1:keys.index('Сумма')]:
            score += max([float(x) if x != '' else 0 for x in self.table[key]])
        return score
    
    def calcZ(self):
        res = [float(x) if x != '' else 0 for x in self.table['Сумма']]
        mean = sum(res) / len(res)
        d = [(x - mean) ** 2 for x in res]
        stdev = (sum(d) / (len(d) - 1)) ** .5
        z = [round( (x - mean) / stdev, 2) for x in res]
        self.table['Z'] = z
        return round(mean, 2), round(stdev, 2)
    
    def statOldPos(self):
        task = self.tasks[self.lastTaskNum]
        
        studs = len(self.table['Сумма'])
        sumt = [0 for i in range(studs)]

        for v in list(self.table.keys())[1:]: # Первая колонка с именами
            sumt = [float(x if x != '' else 0) + y for x, y in zip(self.table[v], sumt)]

            if v.find(task) != -1:
                break
        
        self.table['Предыдущая сумма'] = sumt
        self.sortBy('Предыдущая сумма', desc = True)
        self.table['Предыдущая позиция'] = [i + 1 for i in range(studs)]
        self.sortBy('Сумма', True)

    def genShift(self, pos):
        shiftInt = self.table['Предыдущая позиция'][pos] - pos - 1
        if shiftInt > 0:
            shift = COLOUR_GREEN + '▲' + str(shiftInt) + COLOUR_END
        elif shiftInt < 0:
            shift = COLOUR_RED + '▼' + str(-shiftInt) + COLOUR_END
        elif shiftInt == 0:
            shift = '●'
        return shift

    def statName(self, name):
        def ratio(a, b):
            return round(100 - (a / b) * 100, 2)
        
        def erfarea(mark):
            p = (1.0 + erf(mark / sqrt(2.0))) / 2.0
            return round(p * 100, 2)
        
        def erfmark(area):
            return erfinv(2 * area - 1) * sqrt(2.0)
        
        def isNormal():
            # Критерий Шапиро-Уилка
            X = [float(x) for x in self.table['Сумма']]
            mean = sum(X) / len(X)
            D = [(x - mean) ** 2 for x in X]
            disp = sum(D)
            n = len(X)
            m = n // 2
            a_0 = 0.899 / (n - 2.4) ** 0.4162 - 0.02
            B = 0
            
            for j in range(1, m + 1):
                z = (n - 2 * j + 1) / (n - 0.5)
                b = 1483 / (3 - z) ** 10.845
                c = (71.6 * 10 ** (-10)) / (1.1 - z) ** 8.26
                a_j = a_0 * (z + b + c)
                B += a_j * (X[n-j] - X[j])
            
            W_1 = disp * (1 - 0.6695 / n ** 0.6518) / B ** 2
            
            return W_1
        
        def markRatio(r):
            maxScore = 514
            score = r * maxScore
            if score >= 360:
                mark = 5
            elif score >= 200:
                mark = 4
            elif score >= 70:
                mark = 3
            else:
                mark = 2
            return mark
        
        def ratioMark(score_now, maxScore_now, mark):
            maxScore = 514
            match mark:
                case 5:
                    score = 360
                case 4:
                    score = 200
                case 3:
                    score = 70
                case _:
                    score = 0
            result = (score * maxScore_now) / maxScore - score_now
            return result if result > 0 else 0
        
        pos = self.table['Имя'].index(name)
        max_pos = len(self.table['Имя'])
        
        score = float(self.table['Сумма'][pos])
        max_score = self.maxScore()
        score_mark = markRatio(score / max_score)
        
        mean, stdev = self.mean, self.stdev
        z = self.table['Z'][pos]
        
        maxarea = erfarea(self.table['Z'][0])
        nextarea = min(erfarea(z) + 10, maxarea) / 100
        score_nextz = round((erfmark(nextarea) - z) * stdev, 1)
        score_nextmark = round(ratioMark(score, max_score, score_mark + 1), 1)
        lastTaskName = list(self.table.items())[self.lastTaskNum + 2][0]

        shift = self.genShift(pos)
        
        line = 55
        
        print(f'{" %s " % name:=^{line}}')
        print(f'Баллов: {score} из {max_score}\t(Предварительная оценка -- {score_mark})')
        print(f'Z:\t{z}\t\t(лучше, чем {erfarea(z)}%)')
        print(f'Место:\t{pos + 1} из {max_pos}\t{shift}')
        print('-' * line)
        
        print(f'Чтобы обойти следующие 10%, нужно {score_nextz} баллов')
        print(f'Чтобы улучшить оценку на один балл, нужно {score_nextmark} баллов')
        print(f'Наиболее вероятное улучшение оценки: {self.errorPredict()} баллов')
        print(f'Изменение оценки: {self.getBetter(pos)} баллов [за {lastTaskName}]')
        
        print('-' * line)
        print(f'Среднее: {mean}, Стандартное отклонение: {stdev}')
        
        W = round(isNormal(), 2)
        
        if W >= 1:
            print(f'Распределение можно считать нормальным (W_1 = {W})')
        else:
            print(f'Существенное отклонение от нормального распределения (W_1 = {W})')
            
        pltr = Plotter(self.table['Сумма'])
        pltr.plot(mean, stdev, W) 
 
    def getBetter(self, pos):
        maxScore = 514
        
        last_sum = self.table['Предыдущая сумма'][pos]
        last_max = max(self.table['Предыдущая сумма'])
        
        sum_now = self.table['Сумма'][pos]
        max_now = max(self.table['Сумма'])
        
        diff = (sum_now / max_now) - (last_sum / last_max)
        res = round(diff * maxScore, 1)
        return ('+' if res > 0 else '') + str(res)
        
 
    def errorPredict(self):
        def decide(s):
            if s.split()[0] == 'Тест':
                return 0
            elif s.split()[-1] == '(unit-tests)':
                return 1
            elif s.split()[0] == 'Введение':
                return 1
            elif s.split()[-1] == '(ноутбук)':
                return 2
            elif s.split()[-1] == '(ML)':
                return 3
            else:
                raise Exception("Неизвестный класс задач: " + s)
        
        slice_people = 10 # Учёт только ТОП-10, именно они влияют на оценку больше всего
        tail = 4 # Столько используется служебных столбцов
        
        marks = [[], [], [], []]
        
        for i in range(1, self.lastTaskNum + 3):
            item = list(self.table.items())[i]
            task_str = item[1][:slice_people]
            task_float = [float(x) if x != '' else 0 for x in task_str]
            task = np.array(list(filter(lambda x: x > 0, task_float)))
            
            marks[decide(item[0])] += [np.max(task) - np.median(task)]

        av = [np.mean(np.array(x)) if len(x) > 0 else 0 for x in marks]

        error = 0
        for i in range(self.lastTaskNum + 3, len(self.table.items()) - tail):
            item = list(self.table.items())[i]
            error += av[decide(item[0])]
        
        return round(error, 1)
 
    def statTop(self, name):
        n = 10

        start = max(self.table['Имя'].index(name) - n // 2, 0) if name != '' else 0
        end = min(start + n, len(self.table['Имя']))
        
        x = len(str(end))
        maxName = max(map(len, self.table['Имя'][start:end])) + 2
        maxZ = max(map(lambda a: len(str(a)), self.table['Z'][start:end])) + 2
        maxScore = max(map(lambda a: len(str(a)), self.table['Сумма'][start:end])) + 2

        print(f'{"Имя":=^{maxName + x + 2}}{"Z":=^{maxZ}}{"Сумма":=<{maxScore}}')
        
        for i in range(start, end):
            name = self.table['Имя'][i]
            z = self.table['Z'][i]
            score = self.table['Сумма'][i]
            shift = self.genShift(i)
            print(f'{i+1:{x}}) {name:<{maxName}}{z:<{maxZ}}{score:<{maxScore}}  {shift}')
