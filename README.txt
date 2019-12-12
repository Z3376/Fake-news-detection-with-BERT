####README

##Author: Harsh Grover

To get dataset:
!wget "https://github.com/Tariq60/LIAR-PLUS/raw/master/dataset/train2.tsv"


To get BERT (required):
!wget "https://storage.googleapis.com/bert_models/2018_10_18/uncased_L-12_H-768_A-12.zip"
!unzip "uncased_L-12_H-768_A-12.zip"


Libraries required (All available through pip install):
keras
tensorflow
keras-bert
sklearn
Pandas
Numpy
NLTK
re
os
matplotlib
codecs
livelossplot
tqdm


To run the script:
Use python3. Enter mode as specified.
Kindly ignore the warnings.

Training on GPU will be required to load BERT. Took me 10 minutes per epoch with batch_size = 5 on a Tesla K80 (Google Colab).


Kindly let me know if any of the following steps didn't work.


