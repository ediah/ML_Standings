from lib.Plotter import Plotter
from math import sqrt
from scipy.special import erf, erfinv

class Statistics:
    def __init__(self, table):
        self.table = table
        
        self.sortBy('Сумма', True)
        self.mean, self.stdev = self.calcZ()
    
    def sortBy(self, name, desc = False):
        for key in self.table.keys():
            X = self.table[key]
            Y = self.table[name]
            srt = sorted(zip(Y, X), key=lambda pair: 
                float(pair[0].split()[-1]) if len(pair[0]) > 0 else 10**5,
                reverse = desc)
            self.table[key] = [x for _, x in srt]
    
    def maxScore(self):
        score = 0
        for key in self.table.keys():
            if key.find('Оценка') != -1:
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
            
        pos = self.table['Имя'].index(name)
        max_pos = len(self.table['Имя'])
        
        score = float(self.table['Сумма'][pos])
        max_score = self.maxScore()
        score_mark = markRatio(score / max_score)
        
        mean, stdev = self.mean, self.stdev
        z = self.table['Z'][pos]
        
        maxarea = erfarea(self.table['Z'][0])
        nextarea = min(erfarea(z) + 10, maxarea) / 100
        score_nextz = round((erfmark(nextarea) - z) * stdev)
        
        line = 55
        
        print(f'{" %s " % name:=^{line}}')
        print(f'Баллов: {score} из {max_score}\t(Предварительная оценка -- {score_mark})')
        print(f'Z:\t{z}\t\t(лучше, чем {erfarea(z)}%)')
        print(f'Место:\t{pos + 1} из {max_pos}')
        print('-' * line)
        
        print(f'Чтобы обойти следующие 10%, нужно {score_nextz} баллов')
        
        print('-' * line)
        print(f'Среднее: {mean}, Стандартное отклонение: {stdev}')
        
        W = round(isNormal(), 2)
        
        if W >= 1:
            print(f'Распределение можно считать нормальным (W_1 = {W})')
        else:
            print(f'Существенное отклонение от нормального распределения (W_1 = {W})')
            
        pltr = Plotter(self.table['Сумма'])
        pltr.plot(mean, stdev, W) 
 
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
            print(f'{i+1:{x}}) {name:<{maxName}}{z:<{maxZ}}{score:<{maxScore}}')
