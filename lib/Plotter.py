import matplotlib.pyplot as plt
import numpy as np
import datetime
import os

class Plotter:
    def __init__(self, var):
        self.img_dir = './img/'
        self.var = var
        
        if not os.path.exists(self.img_dir):
            os.makedirs(self.img_dir)
        
    def plot(self, mean, sd, w):
        varUnique = list(set(self.var))
        varCounts = [self.var.count(x) for x in varUnique]
        varInt = list(map(round, map(float, self.var)))
        varKoef = sum(varCounts)
        varMax  = max(varCounts)
                
        fig, ax = plt.subplots()
        ax.set_ylim([0, max(100, varMax)])
        n, bins, patches = ax.hist(varInt, len(varUnique))
        y = (1 / (np.sqrt(2 * np.pi) * sd)) * np.exp(-0.5 * ((bins - mean) / sd)**2)
        ax.plot(bins, varKoef * y, '--')
        
        now = datetime.datetime.now()
        name = str(now).split()[0]
        ax.set_title(name + ' ($\mu=' + str(mean) + '$, $\sigma=' + str(sd) + '$, $W_1=' + str(w) + '$)')
        
        pathname = self.img_dir + name + '.png'
        plt.savefig(pathname, format='png') 
