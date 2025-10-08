from kaggle.api.kaggle_api_extended import KaggleApi
from pathlib import Path
import os
import streamlit as st

def download_dataset(dataset):
    os.environ["KAGGLE_USERNAME"] = st.secrets["kaggle"]["username"]
    os.environ["KAGGLE_KEY"] = st.secrets["kaggle"]["key"]
    
    api = KaggleApi()
    api.authenticate()

    data_dir = Path('data')
    data_dir.mkdir(exist_ok=True)

    api.dataset_download_files(dataset, path=data_dir, unzip=True)
