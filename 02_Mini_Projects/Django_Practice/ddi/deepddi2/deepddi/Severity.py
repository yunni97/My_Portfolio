import os
import glob
import pickle
import copy
import argparse
import numpy as np
import time

import pandas as pd
from keras.models import model_from_json 
from sklearn.preprocessing import MultiLabelBinarizer

def predict_severity(output_dir, output_file, df, trained_model, trained_weight, threshold):
    with open('./data/multilabelbinarizer_severity.pkl', 'rb') as fid:
        lb = pickle.load(fid)
    
    #df = pd.read_csv(ddi_input_file, index_col=0)    
    import joblib
    ddi_pairs = list(df.index)
    X = df.values    
    
    clf = joblib.load(trained_model)
    lb = None
    try:
        with open('./data/multilabelbinarizer_severity.pkl', 'rb') as fid:
            lb = pickle.load(fid)
    except Exception:
        pass

    with open(output_file, 'w', encoding='utf-8') as fp:
        fp.write('Drug pair\tPredicted class\tScore\tSTD\n')

        if hasattr(clf, "predict_proba"):
            proba = clf.predict_proba(X)

            # 단일 다중분류 (ex: ['Minor','Moderate','Major'])
            if proba.ndim == 2 and (lb is None):
                classes = getattr(clf, "classes_", np.arange(proba.shape[1]))
                for i, pair in enumerate(ddi_pairs):
                    c = int(np.argmax(proba[i]))
                    label = str(classes[c])
                    fp.write(f'{pair}\t{label}\t{proba[i, c]}\t0.0\n')

            # 멀티라벨 (OVR)
            elif lb is not None:
                bin_ = (proba >= float(threshold)).astype(int)
                inv = lb.inverse_transform(bin_)
                classes = list(lb.classes_)
                for i, pair in enumerate(ddi_pairs):
                    for lab in inv[i]:
                        idx = classes.index(lab)
                        fp.write(f'{pair}\t{lab}\t{proba[i, idx]}\t0.0\n')

            else:
                # 예외: 확률은 있는데 LB 없음 → 최대값만
                for i, pair in enumerate(ddi_pairs):
                    c = int(np.argmax(proba[i]))
                    fp.write(f'{pair}\t{c}\t{proba[i, c]}\t0.0\n')

        else:
            # 확률 미지원 모델 → 예측 라벨만
            pred = clf.predict(X)
            for i, pair in enumerate(ddi_pairs):
                fp.write(f'{pair}\t{pred[i]}\t1.0\t0.0\n')