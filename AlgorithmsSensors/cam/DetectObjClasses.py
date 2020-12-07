import numpy as np
import cv2
from abc import abstractmethod
from os import listdir
from os.path import isfile
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.decomposition import PCA
import pickle

from keras.preprocessing.image import img_to_array
from keras.models import Model,model_from_json

class DetectBase:
    def __init__(self,config):
        self.config = config

    @abstractmethod
    def detect(self,frameAtual,frameInicial=None):
        pass

class DetectMog(DetectBase):
    def detect(self, frameAtual,frameInicial=None):
        # Aplicando operações basicas no primeiro frame
        primeroFrame = frameInicial.copy()
        primeroFrame = cv2.cvtColor(primeroFrame, cv2.COLOR_BGR2GRAY)
        primeroFrame = cv2.GaussianBlur(primeroFrame, (21, 21), 0)
        # Aplicando operações basicas no frame atual
        frame = cv2.cvtColor(frameAtual, cv2.COLOR_BGR2GRAY)
        frame = cv2.GaussianBlur(frame, (21, 21), 0)
        # calculanod diferença entre os frames
        frameDelta = cv2.absdiff(primeroFrame, frame)
        thresh = cv2.threshold(frameDelta, 25, 255, cv2.THRESH_BINARY)[1]
        # Dilatando o thresholded image para preencher os buracos e encontrar os contornos
        thresh = cv2.dilate(thresh, None, iterations=2)
        cnts, hierarchy = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
                                           cv2.CHAIN_APPROX_SIMPLE)
        # procurando maior boundbox encontrado
        if type(cnts) is None or len(cnts) <= 0:
            return None
        max_cnts = cnts[0]
        for c in cnts:
            if cv2.contourArea(c) > cv2.contourArea(max_cnts):
                max_cnts = c
        # Verificando se o maior contorno é maior que minimo da configuração
        if cv2.contourArea(max_cnts) < self.config['algorithm']['vision']['min_area']:
            return None
        else:
            print("Area:", cv2.contourArea(max_cnts))
        # Buncando tamanho do boundbox e retornando
        (x, y, w, h) = cv2.boundingRect(max_cnts)
        return (x, y, w, h)

class DetectMLBase(DetectBase):
    def __init__(self, config,nameModel=None,namePrepDataModel=None):
        print("Detect Base")
        self.config = config
        self.depth = False
        self.nameModel = nameModel
        self.namePrepDataModel = namePrepDataModel
        self.windowSizeX = self.config['algorithm']['vision']['windowSizeX']
        self.windowSizeY = self.config['algorithm']['vision']['windowSizeY']
        #load models
        self.dirModel = self.config['algorithm']['vision']['dirModels']+self.nameModel+'.sav'
        print("Load model in path:",self.dirModel)
        self.model = pickle.load(open(self.dirModel, 'rb'))
        if namePrepDataModel:
            dirModelPrepData = self.config['algorithm']['vision']['dirModels'] + self.namePrepDataModel + '.sav'
            self.prepData = pickle.load(open(dirModelPrepData, 'rb'))

    def detect(self, frame, primeiroFrame=None):
        stepSize = 20
        if not self.depth:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        for y in range(0, frame.shape[0], stepSize):
            if (y + self.windowSizeY > frame.shape[0]):
                y = frame.shape[0] - self.windowSizeY
            for x in range(0, frame.shape[1], stepSize):
                if (x + self.windowSizeX > frame.shape[1]):
                    x = frame.shape[1] - self.windowSizeX
                crop_img = frame[y:y + self.windowSizeY, x:x + self.windowSizeX]
                data = crop_img.reshape(-1)
                if self.namePrepDataModel :
                    data = self.prepData.transform([data])
                predito = self.model.predict(data)
                if predito[0] == 1:
                    bbox = (x, y, self.windowSizeX, self.windowSizeY)
                    return bbox
        return None


class DetectSVM(DetectMLBase):
    def __init__(self, config,nameModel='lgb_new',namePrepDataModel='pca'):
        print("Detect SVM")
        DetectMLBase.__init__(self,config, nameModel=nameModel, namePrepDataModel=namePrepDataModel)

class DetectNeural(DetectMLBase):
    def __init__(self, config,nameModel='neural network',namePrepDataModel='pca'):
        if namePrepDataModel == 'pca':
            # PCA
            n_components = 150
            self.prepData = PCA(n_components=n_components, svd_solver='randomized', whiten=True)
        # SVM
        self.model = MLPClassifier(hidden_layer_sizes=(75,20))
        DetectMLBase.__init__(self,config, nameModel=nameModel, namePrepDataModel=namePrepDataModel)

class DetectKeras(DetectMLBase):
    def __init__(self, config,nameModel='keras_Xception',namePrepDataModel=None):
        # Keras
        DetectMLBase.__init__(self,config, nameModel=nameModel, namePrepDataModel=namePrepDataModel)

    def load_model(self):
        json_path = self.config['algorithm']['vision']['dirModels']+self.nameModel+'.json'
        json_file = open(json_path, 'r')
        model_json = json_file.read()
        json_file.close()
        weights_file = self.config['algorithm']['vision']['dirModels']+self.nameModel+'.h5'
        self.model = model_from_json(model_json)
        self.model.load_weights(weights_file)
        self.model.compile(optimizer='Adam', loss='categorical_crossentropy', metrics=['accuracy'])

    def detect(self, frame, primeiroFrame=None):
        stepSize = 60
        # frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        cont = 0
        list_image = []
        for y in range(0, frame.shape[0], stepSize):
            if (y + self.windowSizeY > frame.shape[0]):
                y = frame.shape[0] - self.windowSizeY
            for x in range(0, frame.shape[1], stepSize):
                if (x + self.windowSizeX > frame.shape[1]):
                    x = frame.shape[1] - self.windowSizeX
                crop_img = frame[y:y + self.windowSizeY, x:x + self.windowSizeX]
                list_image.append({'image':crop_img,'x':x,'y':y})
        print("iniciando predito")
        predito = self.keras_predict(list_image)
        if predito is not None:
            bbox = (predito['x'], predito['y'], self.windowSizeX, self.windowSizeY)
            return bbox
        return None

    def keras_predict(self, list_image, threshold=0.997):
        list_data = []
        for image_data in list_image:
            image = img_to_array(image_data['image'])
            data = image.astype('float32') / 255.0
            list_data.append(data)
        list_predict = self.model.predict(np.array(list_data))
        for cont in range(len(list_predict)):
            predict = list_predict[cont]
            if predict.argmax() == 1 and predict[1] >= threshold:
                print(predict)
                return list_image[cont]
        return None
    """
    def detect(self, frame, primeiroFrame=None):
        stepSize = 20
        #frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        print(frame.shape,stepSize)
        for y in range(0, frame.shape[0], stepSize):
            if (y + self.windowSizeY > frame.shape[0]):
                y = frame.shape[0] - self.windowSizeY
            for x in range(0, frame.shape[1], stepSize):
                if (x + self.windowSizeX > frame.shape[1]):
                    x = frame.shape[1] - self.windowSizeX
                crop_img = frame[y:y + self.windowSizeY, x:x + self.windowSizeX]
                predito = self.keras_predict(crop_img)
                if predito == 1:
                    bbox = (x, y, self.windowSizeX, self.windowSizeY)
                    return bbox
        return None

    def keras_predict(self,windows,threshold=0.7):
        image = img_to_array(windows)
        image = image.astype('float32') / 255.0
        image = np.expand_dims(image, 0)
        y_predi = self.model.predict(image)[0]
        print('y_predi',y_predi)
        if y_predi.argmax() == 0 and y_predi[0] >= threshold:
            return 1
        return 0
    """
    """
    def classifier_keras(self, img, class_num=1, threshold=0.5):
        list_output = []
        obj_img = Imagem_data(img, keras=True)
        dici_windows = obj_img.slidingWindows(stepSize=20)
        for num_image in range(len(dici_windows['windows'])):
            image = dici_windows['windows'][num_image]
            image = img_to_array(image)
            image = image.astype('float32') / 255.0
            image = np.expand_dims(image, 0)
            y_predi = self.model.predict(image)
            if y_predi[0].argmax() == class_num and y_predi[0][class_num] >= threshold:
                x = dici_windows['x'][num_image]
                y = dici_windows['y'][num_image]
                list_output.append({'window': image, 'x': x, 'y': y})
        return list_output
    """




