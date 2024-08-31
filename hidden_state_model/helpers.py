import os

import pandas as pd

from hidden_state_model.observer import Observer


data_dir = os.path.join(os.path.dirname(__file__), "data")

# Iterate over files in data/*.parquet and combine to one df
dfs = []

read = []
for file in os.listdir(data_dir):
    full_fname = os.path.join(data_dir, file)
    if file.endswith(".parquet"):
        read.append(file)
        print(f"Reading {file}")
        df = pd.read_parquet(full_fname)
        dfs.append(df)
    if file.endswith(".csv"):
        read.append(file)
        df = pd.read_csv(full_fname, index_col=0)
        dfs.append(df)

combined_df = pd.concat(dfs)

dfs = []  # Clear memory

# Initialize an observer with all stored data
complete_observer = Observer(df=combined_df)


def get_observer_with_all_data() -> Observer:
    return complete_observer.clone()
