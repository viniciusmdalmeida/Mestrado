import numpy as np
import cv2
from os import listdir
from os.path import isfile
import pickle
#sklearn
from sklearn.model_selection import cross_val_score
#sklearn models
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.decomposition import PCA
#lightgbm
import lightgbm as lgb

import random


def get_dict_dados(windowSizeY,windowSizeX,negativeImg_path,positiveImg_path):
    dim = (windowSizeY, windowSizeX)
    imgs = []
    datas = []
    target = []
    list_paths = [negativeImg_path,positiveImg_path]
    # Dados Negativos: Sem o avião
    num_class = 0
    for path in list_paths:
        for file_name in listdir(path):
            file_path = path + file_name
            if isfile(file_path):
                image = cv2.imread(file_path, 0)
                image = cv2.resize(image, dim, interpolation=cv2.INTER_AREA)
                imgs.append(image)
                datas.append(image.reshape(-1))
                target.append(num_class)
        num_class += 1
    dict = {'img': imgs, 'target': target, 'data': datas}
    return dict


def train_model(dict_data,model,prep_data_model=None,model_name=None,save_path='../data/models/',prep_model_name=None):
    X = dict_data['data']
    X = prep_data_model.fit_transform(X)
    y = dict_data['target']
    model.fit(X,y)
    if model_name:
        pickle.dump(model, open(save_path+model_name, 'wb'))
    if prep_model_name:
        pickle.dump(prep_data_model, open(save_path+prep_data_model, 'wb'))
    return model

def normalize_class(X,y):
    print("normalize class")
    #separando dados em um dicionario
    dict_class_data = {}
    for num_item in range(len(X)):
        item = X[num_item]
        classe = y[num_item]
        if not classe in dict_class_data:
            dict_class_data[classe] = [item]
        else:
            dict_class_data[classe].append(item)
    #calculando classe com menos itens
    cont_min_class = np.inf
    for classe in dict_class_data:
        if len(dict_class_data[classe]) < cont_min_class:
            cont_min_class = len(dict_class_data[classe])
    #normalizando classes
    for classe in dict_class_data:
        random.shuffle(dict_class_data[classe])
        dict_class_data[classe] = dict_class_data[classe][:cont_min_class]
    #Voltando a ser uma lista
    X = []
    y = []
    for classe in dict_class_data:
        num_items = len(dict_class_data[classe])
        X += dict_class_data[classe]
        y += [classe]*num_items
    return X,y

def cross_over_train_model(dict_data,model,prep_model,save_path='../../../data/models/',model_name=None,prep_model_name='prep_model.sav'):
    X = np.array(dict_data['data'])
    y = dict_data['target']
    if prep_model:
        X,y = normalize_class(X,y)
        X = prep_model.fit(X).transform(X)
        pickle.dump(prep_model, open(save_path + prep_model_name, 'wb'))
    #calc_cross Validade
    print("Start cross validade")
    scores = cross_val_score(model, X, y, cv=5)
    #train
    print("Start train")
    model.fit(X,y)
    if model_name:
        pickle.dump(model, open(save_path+model_name, 'wb'))
    return model,scores


negativeImg_path = 'C:/Users/vinic/OneDrive/Mestrado/Programa/Python/data/imagens/RGB/windows/background/'
positiveImg_path = 'C:/Users/vinic/OneDrive/Mestrado/Programa/Python/data/imagens/RGB/windows/plane/'
img_width = 80
img_height = 80
#get data
dict_data = get_dict_dados(80,80,negativeImg_path,positiveImg_path)
#load model
prep_model = PCA(n_components=150, svd_solver='randomized', whiten=True)
model = lgb.LGBMClassifier()
#dict_models = {'svm':SVC(C=100, gamma=0.01),'lgb':lgb.LGBMClassifier(),'rf':RandomForestClassifier()}
#train
file_name = 'lgb_new.sav'
model,cross_validade = cross_over_train_model(dict_data,model,prep_model,model_name=file_name,prep_model_name='pca.sav')
print(cross_validade,":",cross_validade.sum()/len(cross_validade))
#Save status
with open('../../../data/models/models.csv','a') as file:
    model = 'LGBMClassifier'
    prep_model = 'PCA'
    mean_acu = cross_validade.sum() / len(cross_validade)
    obs = ''
    file.write(f'{model};{prep_model};{file_name};{mean_acu},{obs}\n')