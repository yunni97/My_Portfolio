import os
import glob
import time

import pickle
import copy
import argparse
import numpy as np
import pandas as pd
import sys
import json as json_module

# TensorFlow와 Keras import
# import tensorflow as tf
# from tensorflow import keras
from sklearn.preprocessing import MultiLabelBinarizer

# sklearn 버전 호환성을 위한 모듈 경로 리다이렉트
if 'sklearn.preprocessing.label' not in sys.modules:
    import sklearn.preprocessing
    sys.modules['sklearn.preprocessing.label'] = sklearn.preprocessing

def predict_DDI(output_file, df, trained_model, trained_weight, threshold, binarizer_file, model_type):
    import warnings
    warnings.filterwarnings('ignore', category=UserWarning)  # sklearn 버전 경고 무시
    
    import joblib
    import pandas as pd
    
    with open(binarizer_file, 'rb') as fid:
        lb = pickle.load(fid)

    #df = pd.read_csv(ddi_input_file, index_col=0)
    ddi_pairs = list(df.index)
    X = df.values
    
    clf = joblib.load(trained_model)
    
    Y_proba = clf.predict_proba(X)    
    Y_std = np.zeros_like(Y_proba)
    Y_bin = (Y_proba >= float(threshold)).astype(int)
    y_inv = lb.inverse_transform(Y_bin)

    # Keras 2.x 모델 로딩 (Keras 3 호환)
    with open(output_file, 'w', encoding='utf-8') as fp:
        fp.write('Drug pair\tPredicted class\tScore\tSTD\n')
        classes = list(lb.classes_)
        for i, each_ddi in enumerate(ddi_pairs):
            scores = Y_proba[i]
            stds   = Y_std[i]
            for cls in y_inv[i]:
                idx = classes.index(cls)
                cls_out = (cls + 113) if model_type == 'model2' else cls
                fp.write(f'{each_ddi}\t{cls_out}\t{scores[idx]}\t{stds[idx]}\n')
                
    # Keras 3에서 Keras 2 모델을 로드하려면 Model을 custom_objects에 등록
    # from tensorflow.keras.models import Model as KerasModel

    # try:
    #     # Model 클래스를 custom_objects로 제공
    #     model = keras.Model.from_config(
    #         model_config['config'],
    #         custom_objects={'Model': KerasModel}
    #     )
    # except Exception as e1:
    #     print(f"Error loading model: {e1}")
    #     print("Attempting alternative loading method...")

    #     try:
    #         # 대안: model_from_json 사용
    #         from tensorflow.keras.models import model_from_json
    #         model = model_from_json(loaded_model_json, custom_objects={'Model': KerasModel})
    #     except Exception as e2:
    #         print(f"Error with model_from_json: {e2}")
    #         # 최후의 수단: H5 가중치 파일에서 직접 로드
    #         raise ValueError(f"Cannot load model. Original error: {e1}\nSecond attempt error: {e2}")

    # # 가중치 로드
    # model.load_weights(trained_weight)

    # mc_predictions = []
    # iter_num = 10
    # for i in range(iter_num):
    #     y_predicted = model.predict(X)
    #     mc_predictions.append(y_predicted)

    # arr = np.asarray(mc_predictions)
    
    # y_predicted_mean = np.mean(arr, axis=0)
    # y_predicted_std = np.std(arr, axis=0)
    
    # original_predicted_ddi = copy.deepcopy(y_predicted_mean)
    # original_predicted_ddi_std = copy.deepcopy(y_predicted_std)

    # y_predicted_mean[y_predicted_mean >= threshold] = 1
    # y_predicted_mean[y_predicted_mean < threshold] = 0
    
    # y_predicted_inverse = lb.inverse_transform(y_predicted_mean)   
    
    # fp = open(output_file, 'w')
    # fp.write('Drug pair\tPredicted class\tScore\tSTD\n')
    # for i in range(len(ddi_pairs)):
    #     predicted_ddi_score = original_predicted_ddi[i]
    #     predicted_ddi_std = original_predicted_ddi_std[i]
    #     predicted_ddi = y_predicted_inverse[i]
    #     each_ddi = ddi_pairs[i]           
    #     for each_predicted_ddi in predicted_ddi:
    #         if model_type == 'model2':
    #             fp.write('%s\t%s\t%s\t%s\n'%(each_ddi, each_predicted_ddi+113, predicted_ddi_score[each_predicted_ddi-1], predicted_ddi_std[each_predicted_ddi-1]))

    #         else:
    #             fp.write('%s\t%s\t%s\t%s\n'%(each_ddi, each_predicted_ddi, predicted_ddi_score[each_predicted_ddi-1], predicted_ddi_std[each_predicted_ddi-1]))

    # fp.close()

