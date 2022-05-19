#Setup Script
from setuptools import setup

setup(name='<name>',
      version='0.0',
      description='<description>',
      packages=['pkgName'],
      author= 'name',
      author_email='email',
      zip_safe=T/F)


#EDA script
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500) 
pd.set_option('display.width', 1000)

class EDA:
  def __init__(self, data): 
    self.data = data
    
  def auto_eda(self):
    print('\n')
    print('The dataset has {} rows & {} columns \n'.format(self.data.shape[0], self.data.shape[1]))
    print('\n**********************************************************\n')
    print(self.data.info())
    print('\n**********************************************************\n')
    print(self.data.describe())
    '\n**********************************************************\n')
