from lib.CacheManager import CacheManager
from lib.HTMLPage import HTMLPage
from datetime import datetime
import requests

class Loader:
    def __init__(self, headers, update = False):
        self.session = requests.session()
        self.headers = headers
        self.url = 'https://cv-gml.ru/course/2'
        self.head = []
        self.body = []
        self.table = {}
        self.update = update
        
        def updater(cache):
            self.loadTable()
            self.makeTable()
            cache.write(str(self.table) + '\n')
            return str(self.table)

        cache = CacheManager('table.cache', self.update)
        cache.ifOld(updater, cache)
        data = cache.decide()
        self.table = eval(data)

    def _loadPage(self, url, lifetime = 3):
        def updater(url, cache):
            data = self.session.get(url, headers=self.headers)
            data = data.content.decode('utf-8')
            cache.write(data)
            return data

        filename = url[url.rfind('/')+1:] + '.cache'
        cache = CacheManager(filename, self.update, lifetime)
        cache.ifOld(updater, url, cache)
        data = cache.decide()
        return HTMLPage(data)

    def loadTable(self, url = ''):
        if (url == ''):
            url = self.url + '/standings'

        page = self._loadPage(url)
        table = page.getBlocks('table')
        thead = table.getBlocks('thead')
        
        headleft = [x.data.strip() for x in thead.getBlocks('tr')[0].getBlocks('th')]
        headright = [x.data.strip() for x in thead.getBlocks('tr')[1].getBlocks('th')]
        
        head = ['Имя']
        bodySlice = [1]
        i_k = 0
        for i in range(0, len(headright)):
            if headright[i] == 'Оценка':
                i_k = i_k + 1
                head += [headleft[i_k]]
                bodySlice += [1]
            else:
                bodySlice += [0]
        
        head += ['Сумма']
        bodySlice += [1]

        tbody = table.getBlocks('tbody')
        trows = tbody.getBlocks('tr')
        body = []
        
        for x in trows:
            t = [el.data.strip() for el in x.getBlocks('td')]
            bodyPart = []

            for i, x in enumerate(bodySlice):
                if x == 1:
                    bodyPart += [t[i]]
            body += [bodyPart]

        self.head = head
        self.body = body
        
    def makeTable(self):
        for i, key in enumerate(self.head):
            t = []
            for x in self.body:
                t.append(x[i])
            
            self.table[key] = t

    def loadDeadline(self, taskNum):
        url = self.url + '/task/' + str(taskNum)
        page = self._loadPage(url, -1) # Кэш действует бессрочно

        blocks = page.getBlocks('h4')
        # Только у ноутбуков 2 дедлайна, у остальных заданий только одно
        if isinstance(blocks, list):
            date = ''
            for i in range(len(blocks)):
                if blocks[i].data.find('Срок') != -1:
                    date = blocks[i]
        else:
            date = blocks
        
        date = date.data.strip()
        date = date[date.find(' ', date.find(' ') + 1) + 1:]
        dt = datetime.strptime(date, "%d.%m.%Y в %H:%M")
        return dt
    
    def loadAllDeadlines(self, tasks):
        dls = []
        for t in range(1, tasks + 1):
            dls += [self.loadDeadline(t)]
        
        return dls
