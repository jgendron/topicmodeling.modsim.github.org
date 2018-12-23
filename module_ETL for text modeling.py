#!/usr/bin/env python
# coding: utf-8

# In[1]:


'''
Purpose:
Create the final dataset for analysis with an ETL module
* Extract parameters about all MODSIM papers published from 2014 to 2018
* Transform parameters within a dataframe
* Load the text of the MODSIM papers into a working data set

Inputs:
The inputs for this procedure include:
* A list of MODSIM websites containing the papers for parsing HTML with BeautifulSoup
* Text files containing full text from each MODSIM Papers (2014 to 2018)
  ** Downloaded PDF from MODSIM website using Google Chrono Sniffer extension
  ** Converted to text using Mac OS Automator workflow
  ** Assumes a file structure ./data/<year>/ exists for years 2014-2018

Output:
The results of this module is a folder called ./data/abstracts/ containing .txt files each with a custom label and containing abstracts extracted from MODSIM papers.
'''

import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
import requests
from random import *
import re

# Provide list of all sites containing MODSIM Papers 2014-2018
sites = ['http://modsimworld.org/conference-papers/2014',
         'http://modsimworld.org/conference-papers/2015',
         'http://modsimworld.org/conference-papers/2016',
         'http://modsimworld.org/conference-papers/2017',
         'http://modsimworld.org/conference-papers/2018']
# Create an empty list to capture webscrape results 
records = [] 

# Extract: get parameters of papers into a dataframe
for site in sites:
    page = requests.get(site)
    soup = BeautifulSoup(page.text, 'html.parser')
    results = soup.find_all('table') # finds all tables on page, each is a track

    for result in results:
        for r in result.findAll('tr'):
            if r.find('td') is not None:
                track = result.find('th').text
                filename = r.find('a')['href'][13:]
                author = r.find('td').text
                team = round((len(r.find('td').text) +                              randint(-2,2)),0) #jitter added for six duplicate labels
                title = r.find('span').text
                year = r.find('a')['href'][8:12]
                records.append((track,filename,author,team,title,year))

df = pd.DataFrame(records, columns = ['track', 'filename', 'author_id', 'team','title', 'year'])

# Transform: relabel tracks into one of four categories
df['year'] = df['year'].apply(str)
mapped_sub = {'track': {'Training and Education': 'TE',
                        'Training': 'TE',
                        'Education': 'TE',
                        'Analytics and Decision Making': 'AT',
                        'Analytics and Decision-Making': 'AT',
                        'Science and Engineering': 'SE',
                        'Visualization and Gamification': 'VG',
                        'Entertainment, Sports, Media, & Visualization': 'VG',
                        'Cyber Security': 'VG'}
             }
df_mod = df.replace(to_replace=mapped_sub)

# Transform: convert .pdf filenames into .txt
df_mod['filename'] = df_mod['filename'].str.replace('pdf', 'txt')

# Transform: extract first occurence of last name as author tag
# create three individual series for three types of matches
a=df_mod['author_id'].str.extract(r'([a-zA-Z]+,)')
b=df_mod['author_id'].str.extract(r'([a-zA-Z]+ and)')
c=df_mod['author_id'].str.extract(r'([a-zA-Z]+$)')

# combine the three temp series with precedence for already filled rows
temp = a.combine_first(b).combine_first(c)
# remove the separator flags 
temp[0] = temp[0].str.replace(',','') # a series function
temp[0] = temp[0].str.replace(' and','')
df_mod['author_id'] = temp[0]

#Transform: convert team variable to string
df_mod['team'] = df_mod['team'].apply(str)

# Create doc labels in track-year-author format  
df_mod['label'] = './data/abstracts/' + df_mod['track'] + '-' +                 df_mod['year'] + '-' + df_mod['author_id'] +                 '[' + df_mod['team']  + '].txt'


# Create a zipped object of tuples (filename, label) to iterate through files
tup = zip(df_mod['filename'],df_mod['label'])

for file,label in tup:
    #create filename to open text file of MODSIM paper
    filename = './data/papers_text/' + label[20:24] + '/' + file
    try:
        f = open(filename, encoding='latin')
        raw = f.read()
    except ValueError:
        print(f'X: {filename}')
    
    abstract = re.search('ABSTRACT\n',raw)
    if not abstract:
        print(f'Need abstract tag: {filename}')
    author = re.search('ABOUT THE', raw)
    if not author:
        print(f'Need author tag: {filename}')
        
    begin = re.search('ABSTRACT\n', raw) #flag for beginning of abstract
    stop = re.search('ABOUT THE', raw) #flag for stop of abstract
    #ironic but we want the end of the begin flag and start of stop flag
    abstract = raw[begin.end():stop.start()] #extracts the abstract
    f.close()
    print(f'Opening {file} and extracting abstract') #output to show progress
    
    #Write the extracted abstract to text file 
    text = open(label, "w")
    text.write(abstract)
    text.close()
    print(f'Writing extracted abstract as file {label}\n') #output to show progress


# In[2]:


# Verify no duplicate labels
len(df_mod['label']) == len(set(df_mod['label']))

