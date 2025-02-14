# -*- coding: utf-8 -*-
"""

Automatically generated by Colaboratory.

Author: Harsh Grover

Original file is located at
    https://colab.research.google.com/drive/11rhvw3g-oI6RpWrOYjVoUYFXa13JlpBe
"""

import pandas as pd
import numpy as np
import os
import sys
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
import re
import nltk
nltk.download('stopwords')
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer
from tqdm import tqdm
import codecs
import keras
import keras_bert
import tensorflow as tf
from livelossplot import PlotLossesKeras
import matplotlib.pyplot as plt

"""# Functions"""

def NaNimputer(arr):
    l = len(arr)
    imp = SimpleImputer(missing_values=np.nan,strategy='constant',fill_value='NaN')
    arr = imp.fit_transform(arr.reshape(-1,1)).reshape(l)
    return arr

def label_classes(arr):
    label = LabelEncoder()
    label.fit(arr)
    return label.classes_

def onehot(arr):
    oh = OneHotEncoder()
    arr = oh.fit_transform(arr.reshape(-1,1)).toarray()
    return arr

def label(arr):
    lab = LabelEncoder()
    arr = lab.fit_transform(arr)
    return arr

def text_preprocess(arr):
    l = len(arr)
    arr = NaNimputer(arr)
    arr_re = [re.sub('[^a-zA-Z0-9]',' ',arr[i]).lower() for i in range(l)]
    ps = PorterStemmer()
    arr_stp = np.array([' '.join([ps.stem(word) for word in arr_re[i].split() if not word in set(stopwords.words('english'))]) for i in tqdm(range(l))])
    return arr_stp

def lower(arr):
    return np.array([arr[i].lower() for i in range(len(arr))])

"""# Data"""

df = pd.read_csv('train2.tsv',delimiter='\t',header=None)

df = df.iloc[[i for i in range(2142)]+[i for i in range(2143,9375)]+[i for i in range(9376,len(df))]]

df = df[:len(df)//2]

ln = len(df)

y = df.iloc[:,2].values
statement = df.iloc[:,3].values
subject = df.iloc[:,4].values
speaker = df.iloc[:,5].values
title = df.iloc[:,6].values
state = df.iloc[:,7].values
party = df.iloc[:,8].values
record = df.iloc[:,9:14].values
context = df.iloc[:,14].values
justification = df.iloc[:,15].values

"""## Preprocessing

### output
"""

label_dict = {'true':1,'mostly-true':1,'half-true':1,'barely-true':0,'false':0,'pants-fire':0}
y_multi = label(y)
y_multi = keras.utils.to_categorical(y_multi)
y_binary = np.array([label_dict[y[i]] for i in range(len(y))])

"""### statement"""

statement_stp = lower(statement)

"""### subject"""

subject = lower(subject)
subject_classes = label_classes(subject)
subject_dict = {}
for i in range(len(subject_classes)):
    dum = subject_classes[i].split(',')
    for j in range(len(dum)):
        if(dum[j] not in subject_dict):
            subject_dict[dum[j]] = len(subject_dict)
subject_enc = np.zeros((ln,len(subject_dict)),dtype=int)
for i in range(ln):
    dum = subject[i].split(',')
    for j in range(len(dum)):
        subject_enc[i][subject_dict[dum[j]]] = 1

"""### speaker"""

speaker_enc = onehot(lower(speaker))[:,1:]

"""### job_title"""

title = lower(NaNimputer(title))
title_enc = onehot(title)[:,1:]

"""### state"""

state = lower(NaNimputer(state))
state_enc = onehot(state)[:,1:]

"""### party"""

party_enc = onehot(lower(party))[:,1:]

"""### context"""

print('Encoding Contexts:')
context_stp = text_preprocess(context)

"""###  justification"""

print('Encoding Justifications:')
justification_stp = text_preprocess(justification)

"""### BERT Embeddings"""

print('Generating BERT-Embeddings:')

pretrained_path = 'uncased_L-12_H-768_A-12'
config_path = os.path.join(pretrained_path,'bert_config.json')
ckpt_path = os.path.join(pretrained_path,'bert_model.ckpt')
vocab_path = os.path.join(pretrained_path,'vocab.txt')

token_dict = {}
with codecs.open(vocab_path, 'r', 'utf8') as reader:
    for line in reader:
        token = line.strip()
        token_dict[token] = len(token_dict)
tokenizer = keras_bert.Tokenizer(token_dict)

max_len = 512
ind_array = []
seg_array = []
cont_ind = []
for i in tqdm(range(ln)):
    ind,seg = tokenizer.encode(statement_stp[i],justification_stp[i],max_len=max_len)
    ind_c,_ = tokenizer.encode(context_stp[i],max_len=16)
    ind_array.append(ind)
    seg_array.append(seg)
    cont_ind.append(ind_c)
ind_array = np.array(ind_array)
seg_array = np.array(seg_array)
cont_ind = np.array(cont_ind)

sc = StandardScaler()
cont_ind = sc.fit_transform(cont_ind)

param = np.array([np.concatenate([subject_enc[i],speaker_enc[i],title_enc[i],state_enc[i],party_enc[i],record[i],cont_ind[i]]) for i in range(ln)])

"""# Mode"""
mode = input('Enter 1 for binary and 2 for six-way classification: ')
flag = 1
while(flag):
    if(mode=='1'):
        y_enc = y_binary
        flag = 0
    elif(mode=='2'):
        y_enc = y_multi
        flag = 0
    else:
        mode = raw_input('Enter either 1 or 2 only. Enter 1 for binary and 2 for six-way classification: ')

classes_dict = {'1':1,'2':6}
activation_dict = {'1':'sigmoid','2':'softmax'}
loss_dict = {'1':'binary_crossentropy','2':'categorical_crossentropy'}


"""#Model"""

bert = keras_bert.load_trained_model_from_checkpoint(config_path,ckpt_path,training=True,trainable=True,seq_len=max_len)

ind,seg = bert.inputs[:2]
bert_out = bert.get_layer('MLM-Norm').output
bert_out = keras.layers.Dense(2,activation='relu')(bert_out)
bert_out = keras.layers.Dropout(0.5)(bert_out)
bert_out = keras.layers.Lambda(lambda x:tf.unstack(x,axis=-1))(bert_out)
inpt2 = keras.layers.Input((len(param[0]),))
x = keras.layers.Dense(64,activation='relu')(inpt2)
x = keras.layers.Dropout(0.5)(x)
f = keras.layers.Concatenate()([bert_out[0],x])
f = keras.layers.Dense(32,activation='relu')(f)
f = keras.layers.Dropout(0.5)(f)
outpt = keras.layers.Dense(classes_dict[mode],activation=activation_dict[mode])(f)
model = keras.models.Model([ind,seg,inpt2],outpt)

# model.summary()

# keras.utils.plot_model(model,'model.png')

"""#Train"""

batch_size=5
epochs=60

decay_steps, warmup_steps = keras_bert.calc_train_steps(4*ln//5,batch_size=batch_size,epochs=epochs)
adawarm = keras_bert.AdamWarmup(decay_steps=decay_steps,warmup_steps=warmup_steps,lr=1e-4)

model.compile(optimizer=adawarm,loss=loss_dict[mode],metrics=['acc'])
# model.compile(optimizer='adam',loss='binary_crossentropy',metrics=['acc'])

es = keras.callbacks.EarlyStopping(monitor='val_loss',patience=10,restore_best_weights=True)
cp = keras.callbacks.ModelCheckpoint('best_acc_model.h5',monitor='val_acc')
csvl = keras.callbacks.CSVLogger('train_log.csv')

history = model.fit([ind_array,seg_array,param],y_enc,epochs=epochs,batch_size=batch_size,validation_split=0.2,callbacks=[es,cp,csvl,PlotLossesKeras()])

model.save_weights('best_model.h5')

# log = pd.read_csv('NUS.csv')

plt.figure()
plt.title('Loss')
plt.plot(history.history['loss'])
plt.plot(history.history['val_loss'])
plt.legend(['loss','val_loss'])
plt.grid()
plt.figure()
plt.title('Acc')
plt.plot(history.history['acc'])
plt.plot(history.history['val_acc'])
plt.legend(['acc','val_acc'])
plt.grid()
plt.show()

