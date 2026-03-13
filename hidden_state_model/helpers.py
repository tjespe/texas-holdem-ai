from datetime import datetime
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
        df = pd.read_parquet(full_fname)
        dfs.append(df)
    if file.endswith(".csv"):
        read.append(file)
        df = pd.read_csv(full_fname, index_col=0)
        dfs.append(df)

combined_df = pd.concat(dfs)

if len(dfs) > 10:
    print("Compacintg dfs")

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    combined_df.to_parquet(os.path.join(data_dir, f"combined_{timestamp}.parquet"))

    # Move files already in trash to trash within trash
    trash = os.path.join(data_dir, "trash")
    trash_in_trash = os.path.join(trash, f"trash_{timestamp}")
    os.makedirs(trash_in_trash, exist_ok=True)
    for f in os.listdir(trash):
        if f.endswith(".parquet") or f.endswith(".csv"):
            os.rename(os.path.join(trash, f), os.path.join(trash_in_trash, f))

    # Move read files to trash and write combined df to dfs/combined_{timestamp}.parquet
    for f in read:
        os.rename(os.path.join(data_dir, f), os.path.join(trash, f))

dfs = []  # Clear memory

# Initialize an observer with all stored data
complete_observer = Observer(df=combined_df)


def get_observer_with_all_data() -> Observer:
    return complete_observer.clone()


def get_observer_with_all_human_data() -> Observer:
    return Observer(
        df=combined_df[
            (combined_df["player_type"] == "HumanPlayer") | (
                combined_df["player_type"] == "WebPlayer"
            )
        ]
    )
