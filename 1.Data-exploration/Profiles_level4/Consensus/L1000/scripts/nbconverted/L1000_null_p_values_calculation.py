#!/usr/bin/env python
# coding: utf-8

# ### Calculating Null Distribution
# 
# - Null distribution - is generated by getting the median correlation score of randomly combined compounds that do not share/come from the same MOAs.
# 
# 
# ### The goal here:
# - is to compute the p-value for each MOA per dose by evaluating the probability of random combinations of compounds (from different MOAs) having greater median correlation score than compounds of the same MOA.
# 
# 
# 
# 
# - In our case, we generated 1000 median correlation scores from randomly combined compounds as the **null distribution** for each MOA_SIZE class ***i.e. for a moa_size class - we have 1000 medians scores from randomly combined compounds of different MOAs.***
# 
# 
# 
# 
# - Moa_size is the number of compounds in a specific MOA and moa_size class is a specific group of MOAs that have the same number of compounds ***e.g all MOAs with just 2 compounds in them are in the same moa_size class.***
# 
# 
# ### Note:
# 
# To generate the null distribution for modz and rank level-5 data, you will have to execute this notebook twice for each of them.

# In[1]:


import os
import requests
import pickle
import argparse
import pandas as pd
import numpy as np
import re
from os import walk
from collections import Counter
import matplotlib.pyplot as plt
get_ipython().run_line_magic('matplotlib', 'inline')
import random
import shutil
from statistics import median


# #### - Load in the datasets required, 
# - They were generated from the `L1000_moa_median_scores_calculation.notebook`

# In[2]:


df_lvl5 = pd.read_csv(os.path.join('moa_sizes_consensus_datasets', 'modz_level5_data.csv'))
df_moa_vals = pd.read_csv(os.path.join('moa_sizes_consensus_datasets', 'modz_moa_median_scores.csv'))
df_moa_cpds = pd.read_csv(os.path.join('moa_sizes_consensus_datasets', 'L1000_moa_compounds.csv'))


# In[3]:


df_lvl5.shape


# In[4]:


df_moa_vals.shape


# In[5]:


df_moa_cpds.shape


# In[6]:


def conv_cols_to_list(df_moa_cpds):
    """This function convert string values in compound dataframe to lists"""
    
    moa_cpd_cols = [col for col in df_moa_cpds.columns.tolist() 
                 if (col.startswith("moa_cpds_"))]
    for col in moa_cpd_cols:
        df_moa_cpds[col] = df_moa_cpds[col].apply(lambda row: row.split(';'))
    return df_moa_cpds


# In[7]:


df_moa_cpds = conv_cols_to_list(df_moa_cpds)


# In[8]:


def get_cpd_agg(data_moa, dose_number):
    """
    This function aggregate values for a particular 
    dose by taking the mean value of distinct compounds in the dose
    """
    
    df_dose = data_moa[data_moa['dose'] == dose_number].copy()
    meta_cols = ['pert_id', 'dose', 'pert_idose', 'moa', 'sig_id']
    df_dose.drop(meta_cols, axis = 1, inplace = True)
    df_compound_agg = df_dose.groupby(['pert_iname']).agg(['mean'])
    df_compound_agg.columns  = df_compound_agg.columns.droplevel(1)
    df_compound_agg.rename_axis(None, axis=0, inplace = True)
    
    return df_compound_agg


# In[9]:


def cpds_found_in_all_doses(data_moa):
    """This function return a list of compounds found in all doses (1 - 6)"""
    cpds_fd = []
    for num in range(1,7):
        df_cpd_agg = get_cpd_agg(data_moa, num)
        all_cpds = df_cpd_agg.index.tolist()
        cpds_fd.append(all_cpds)
    
    cpds_fd_in_all = [cpd for list_cpds in cpds_fd 
                      for cpd in list_cpds 
                      if all(cpd in list_of_cpds for list_of_cpds in cpds_fd)]
    cpds_fd_in_all = list(set(cpds_fd_in_all))
    
    return cpds_fd_in_all


# In[10]:


cpds_fd_in_all = cpds_found_in_all_doses(df_lvl5)


# In[11]:


len(cpds_fd_in_all)


# In[12]:


all_moa_list = df_lvl5['moa'].unique().tolist()


# In[13]:


len(all_moa_list)


# In[14]:


#moa with their corresponding compounds
all_moa_dict = {moa: [cpd for cpd in df_lvl5['pert_iname'][df_lvl5['moa']== moa].unique().tolist() 
                      if cpd in cpds_fd_in_all] 
                for moa in all_moa_list}
all_moa_dict = {kys:all_moa_dict[kys] for kys in all_moa_dict if all_moa_dict[kys]}


# In[15]:


def generate_moa_size_dict(df_moa_cpds):
    """
    Generates a dictionary with distinct moa_sizes 
    (moa_size == number of compounds that is present in each MOA) 
    as the keys and all compounds of MOAs with that particular size as the values
    """
    moa_size_dict = {}
    for size in df_moa_cpds['moa_size'].unique():
        size_df = df_moa_cpds[df_moa_cpds['moa_size'] == size].drop(['moa_size', 'moa'], axis = 1)
        size_df_values = size_df.values.tolist()
        size_df_vals = list(set([cpd for size_list in size_df_values for sizes in size_list for cpd in sizes]))
        moa_size_dict[size] = size_df_vals
    return moa_size_dict


# In[16]:


moa_sizes_dict = generate_moa_size_dict(df_moa_cpds)


# In[17]:


len(df_moa_cpds['moa_size'].unique())


# In[18]:


len(moa_sizes_dict)


# In[19]:


def check_similar_cpds(cpds, moa_dict):
    """This function checks if two compounds are found in the same moa"""
    
    for x in range(len(cpds)):
        for y in range(x+1, len(cpds)):
            for kys in moa_dict:
                if all(i in moa_dict[kys] for i in [cpds[x], cpds[y]]):
                    return True
    return False


# In[20]:


def get_random_cpds(all_cpds, moa_size, moa_cpds, all_moa_cpds):
    """
    This function return a list of random cpds that are not of the same moas 
    or found in the current moa cpd's list
    """
    while (True):
        random_cpds = random.sample(all_cpds, moa_size)
        if not (any(cpds in moa_cpds for cpds in random_cpds) & (check_similar_cpds(random_cpds, all_moa_cpds))):
            break
    return random_cpds


# In[21]:


def get_null_distribution_cpds(moa_size_dict, cpds_list, all_moa_dict, rand_num = 1000):
    
    """
    This function returns a null distribution dictionary, with MOA_SIZEs as the keys and 
    1000 lists of randomly selected compounds combinations as the values for each moa_size class
    """
    null_distribution_moa = {}
    for size in moa_size_dict:
        moa_cpds = moa_size_dict[size]
        moa_cpds_list = []
        for idx in range(rand_num):
            start_again = True
            while (start_again):
                rand_cpds = get_random_cpds(cpds_list, size, moa_cpds, all_moa_dict)
                if rand_cpds not in moa_cpds_list:
                    start_again = False
            moa_cpds_list.append(rand_cpds)
        null_distribution_moa[size] = moa_cpds_list
    
    return null_distribution_moa


# In[22]:


null_distribution_moa = get_null_distribution_cpds(moa_sizes_dict, cpds_fd_in_all, all_moa_dict)


# In[23]:


#save the null_distribution_moa to pickle, you only need to run the code once
with open(os.path.join('moa_sizes_consensus_datasets', 'null_distribution.pickle'), 'wb') as handle:
    pickle.dump(null_distribution_moa, handle, protocol=pickle.HIGHEST_PROTOCOL)


# In[24]:


##load the null_distribution_moa from pickle
with open(os.path.join('moa_sizes_consensus_datasets', 'null_distribution.pickle'), 'rb') as handle:
    null_distribution_moa = pickle.load(handle)


# In[25]:


print('moa_size', '\tnumber of generated lists of randomly combined compounds')
for keys in null_distribution_moa:
    print(keys, '\t\t', len(null_distribution_moa[keys]))


# In[26]:


def assert_null_distribution(null_distribution_moa):
    
    """
    This function assert that each of the list in the 1000 lists of 
    random compounds combination for each MOA are distinct with no duplicates
    """
    
    duplicates_moa = {}
    for keys in null_distribution_moa:
        null_dist = null_distribution_moa[keys]
        for cpds_moa in null_dist:
            cpds_duplicates = []
            new_list = list(filter(lambda cpds_list: cpds_list != cpds_moa, null_dist))
            if (len(new_list) != len(null_dist) - 1):
                cpds_duplicates.append(cpds_moa)
        if cpds_duplicates:
            duplicates_moa[keys] = cpds_duplicates
    return duplicates_moa


# In[27]:


duplicates_cpds_list = assert_null_distribution(null_distribution_moa)


# In[28]:


duplicates_cpds_list ##no duplicate found


# In[29]:


def calc_null_dist_median_scores(data_moa, dose_num, moa_cpds_list):
    """
    This function calculate the median of the correlation 
    values for each of the list in the 1000 lists of 
    random compounds combination for each MOA
    """
    df_cpd_agg = get_cpd_agg(data_moa, dose_num)
    median_corr_list = []
    for list_of_cpds in moa_cpds_list:
        df_cpds = df_cpd_agg.loc[list_of_cpds]
        cpds_corr = df_cpds.T.corr(method = 'spearman').values
        median_corr_val = median(list(cpds_corr[np.triu_indices(len(cpds_corr), k = 1)]))
        median_corr_list.append(median_corr_val)
    return median_corr_list


# In[30]:


def get_null_dist_median_scores(null_distribution_moa, df_moa):
    """ 
    This function calculate the median correlation scores for all 
    1000 lists of randomly combined compounds for each moa_size class 
    across all doses (1-6)
    """
    null_distribution_medians = {}
    for key in null_distribution_moa:
        median_score_list = []
        for num in range(1,7):
            moa_size_median_scores = calc_null_dist_median_scores(df_moa, num, null_distribution_moa[key])
            median_score_list.append(moa_size_median_scores)
        null_distribution_medians[key] = median_score_list
    return null_distribution_medians


# **A P value can be computed nonparametrically by evaluating the probability of random compounds of different MOAs having greater median similarity value than compounds of the same MOAs.**

# In[31]:


null_distribution_medians = get_null_dist_median_scores(null_distribution_moa, df_lvl5)


# In[32]:


def get_p_value(median_scores_list, df_moa_values, dose_name, moa_name):
    """
    This function calculate the p-value from the 
    null_distribution median scores for each MOA
    """
    actual_med = df_moa_values.loc[moa_name, dose_name]
    p_value = np.sum(median_scores_list >= actual_med) / len(median_scores_list)
    return p_value


# In[33]:


def get_moa_p_vals(null_dist_median, df_moa_values):
    """
    This function returns a dict, with MOAs as the keys and the MOA's 
    p-values for each dose (1-6) as the values
    """
    null_p_vals = {}
    df_moa_values = df_moa_values.set_index('moa').rename_axis(None, axis=0)
    for key in null_dist_median:
        df_moa_size = df_moa_values[df_moa_values['moa_size'] == key]
        for moa in df_moa_size.index:
            dose_p_values = []
            for num in range(1,7):
                dose_name = 'dose_' + str(num)
                moa_p_value = get_p_value(null_dist_median[key][num-1], df_moa_size, dose_name, moa)
                dose_p_values.append(moa_p_value)
            null_p_vals[moa] = dose_p_values
    sorted_null_p_vals = {key:value for key, value in sorted(null_p_vals.items(), key=lambda item: item[0])}
    return sorted_null_p_vals


# In[34]:


null_p_vals = get_moa_p_vals(null_distribution_medians, df_moa_vals)


# In[35]:


df_null_p_vals = pd.DataFrame.from_dict(null_p_vals, orient='index', 
                                        columns = ['dose_' + str(x) 
                                                   for x in range(1,7)]).reset_index().rename(columns={"index": "moa"})


# In[36]:


df_null_p_vals['moa_size'] = df_moa_vals['moa_size']


# In[37]:


df_null_p_vals.head(10)


# In[38]:


def save_to_csv(df, path, file_name):
    """saves moa dataframes to csv"""
    
    if not os.path.exists(path):
        os.mkdir(path)
    
    df.to_csv(os.path.join(path, file_name), index = False)


# In[39]:


save_to_csv(df_null_p_vals, 'moa_sizes_consensus_datasets', 'modz_null_p_values.csv')

