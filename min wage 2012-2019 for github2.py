# Importing the required libraries.

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.stats.weightstats import DescrStatsW

# Defining a usefule function to fix the weights in the weighted standard deviation calculation.

def my_weights(w):
    return w * (len(w) / w.sum())

# Importing a file with the addresses and a file with data on minimum wages.

file_names = pd.read_csv(r'C:\Users\dtsj8\OneDrive\Documents\Work\Working Files\File Names.csv', index_col = 'Year')
min_wage_by_year = pd.read_csv(r'C:\Users\dtsj8\OneDrive\Documents\Work\Below Min\min_wage_by_year.csv')

# Defining a dictionary with the analysis period.

period = {'start' : 2012,
          'end' : 2019}

# Creating two empty DataFrames: one for the results and the other for concating all the DataFrames of different years.

results = pd.DataFrame()
all_prat = pd.DataFrame()

# Splitting the quarter column by comma, for later use.

min_wage_by_year['quarter'] = min_wage_by_year['quarter'].str.split(',')

# The loop that concats the different years to a single DataFrame.

for year, folder, prat_file in zip(np.arange(period['start'], period['end'] + 1), file_names.loc[period['start']:period['end'], 'Folder Address'], file_names.loc[period['start']:period['end'], 'Prat']):
    prat = pd.read_csv(r'G:\My Drive\k_data\CBS Households Expenditures Survey' + '\\' + folder + '\\' + prat_file + '.csv')
    
    # Making all the columns lower-cased and renaming the weights column.
    
    prat.columns = prat.columns.str.lower()
    prat.rename(columns = {'mishkal' : 'weight'}, inplace = True)
        
    all_prat = pd.concat([all_prat, prat])

# A loop for assigning the relevant minimum wage to each individual according to the interview quarter and year. 

for quarter, year, min_wage in zip(min_wage_by_year['quarter'], min_wage_by_year['year'], min_wage_by_year['min_wage']):    
    
    # Creating a list of quarter for changing strings to ints.
    
    quarter_int = []
    for elem in quarter:
        quarter_int.append(int(elem))
        
    # Masking the year and quarter.    
    mask_year = all_prat['s_seker'] == year 
    mask_quarter = all_prat['quarter'].isin(quarter_int)  
    
    # Assigning the minimum wage for each individual.
    
    all_prat.loc[mask_year & mask_quarter, 'min_wage'] = min_wage
        
# The main calculation loop. For each year it calculates the share and absolute number of salaried workers that earn minimum wage.   
    
for year in all_prat['s_seker'].drop_duplicates().sort_values():
    
    # Creating a filter for the year.
    mask_year = all_prat['s_seker'] == year
    
    # Creating a filter for salaried workers (i111prat) and exculding self-employed (i112prat).
    
    mask_waged = all_prat['i111prat'] > 0
    mask_self = all_prat['i112prat'] == 0
    
    # Creating a filter for individuals with positive monthly work hours (number of work hours per week times the number of working weeks per month).
    
    mask_hours = (all_prat['sh_shavua'] * all_prat['shavuot']) > 0
    
    # Filtering the DataFrame according to the filters above.
    
    temp = all_prat[mask_year & mask_waged & mask_self & mask_hours].copy()
    
    # Calculating monthly work hours by multipling weekly work hours by monthly work weeks.
    
    temp['hourly'] = temp['i111prat'] / (temp['sh_shavua'] * temp['shavuot'])
    
    # Filtering the DataFrame for workers that earn above 0.85 of the minimum wage to filter soldiers, problematic work hours reporting and workers that earn way below minimum wage.
    # All of those are not relevant for the analysis.
    
    temp = temp[temp['hourly'] > temp['min_wage'] * 0.85].copy()
    
    # Creating a filter slightly above the minimum wage by 5%.
    
    mask_min_wage = temp['hourly'] <= temp['min_wage'] * 1.05
    
    # Creating a filter for workers that work more than 40 hours per week and 1.15 time the minimum wage to account for extra work hours.
    
    mask_hours = (temp['sh_shavua'] > 40) & (temp['hourly'].between(temp['min_wage'] * 1.05, temp['min_wage'] * 1.15))
    
    # Calculating the absolute number and the ratio of minimum earners, by using the filters and summing the weights as per LAMAS instrcutions. 
    
    temp['below_or_min'] = 0
    temp.loc[mask_min_wage | mask_hours, 'below_or_min'] = 1
    results.loc[year, 'minimum'] = temp.loc[mask_min_wage | mask_hours, 'weight'].sum()
    results.loc[year, 'minimum ratio'] = np.average(temp['below_or_min'], weights = temp['weight']) * 100
    
    # Calculating standard deviation as well.
    
    results.loc[year, 'std'] = DescrStatsW(temp['below_or_min'], my_weights(temp['weight'])).std_mean * 100
    
# Creating the figure and plotting the data.
    
label = 'שיעור המשתכרים מינימום שעתי'
xline = 'שינוי מתודולוגי'
plt.figure(figsize = (10,5), dpi = 500)
plt.bar(results.index, results['minimum ratio'], yerr = results['std'])
plt.xlabel('שנה'[::-1], fontsize = 12)
plt.ylabel('אחוז'[::-1], fontsize = 12)
plt.title( '2012-2019 ' + label[::-1], fontsize = 15)
plt.yticks(plt.yticks()[0], ['{:.0f}'.format(x) + '%' for x in plt.yticks()[0]])
for year in results.index:
    plt.annotate(str(np.round(results.loc[year, 'minimum ratio'], 1)) + '%', 
                 xy = (year, results.loc[year, 'minimum ratio'] + 0.8), 
                 ha = 'center', 
                 va = 'center')

source = 'מקור: סקרי הוצאות משקי הבית 9102-2102, הלמ"ס'    
plt.annotate(source[::-1], xy = (2011, -2.5), annotation_clip = False)
plt.annotate('@tom_sadeh', xy = (2019, -2.5), annotation_clip = False)
plt.axvline(2018.5, label = xline[::-1], color = 'black')
plt.legend()