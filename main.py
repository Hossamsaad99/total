#!/usr/bin/env python
# coding: utf-8

# In[1]:


# from google.colab import drive 
# drive.mount('/content/drive')
# %cd drive/MyDrive/


# # Install necessary packages

# In[2]:


# !pip install uvicorn
# !pip install fastapi
# !pip install nest_asyncio
# !pip install pystan
# !pip install prophet
# !pip install pyngrok 
# !pip install pmdarima
# !pip install -v scikit-learn==0.23.2


# # Importations

# In[5]:


# for FastAPI
from fastapi import FastAPI
import uvicorn
import pydantic
# from pyngrok import ngrok
# import nest_asyncio
# for FBprophet
from datetime import *
import pandas_datareader as pdr
import numpy as np
import pandas as pd
import holidays
from prophet import Prophet
# for arima
from statsmodels.tsa.arima_model import ARIMA
import pmdarima as pm
# for LSTM
from tensorflow.keras.models import load_model
import pickle
# for transformer
# from utils.Time2Vector import Time2Vector
# from utils.Attention import MultiAttention, SingleAttention
# from utils.Encoder import TransformerEncoder
# from tensorflow import keras


# In[6]:


# nest_asyncio.apply()


# # Models used

# In[10]:


def prophet (ticker):
  """
  Forcasting using prophet ! by Getting the desired data from yahoo, then doing some data manipulation, then the comes the prophet's turn
  Args:
      (str) ticket - the ticker of desired dataset (company)
  Returns:
      (float) prophet_output - the model out-put (the prediction of the next day)
  """

  # data_gathering
  df = pdr.DataReader(ticker, data_source='yahoo', start='2015-01-01')

  # data manipulation
  holiday = pd.DataFrame([])
  for date, name in sorted(holidays.UnitedStates(years=[2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021]).items()):
      holiday = holiday.append(pd.DataFrame({'ds': date, 'holiday': "US-Holidays"}, index=[0]), ignore_index=True)
  holiday['ds'] = pd.to_datetime(holiday['ds'], format='%Y-%m-%d', errors='ignore')

  # data frame modification to be accepted by prophet
  data = df['Close'].reset_index()
  data.columns = ['ds', 'y']

  # model building
  m = Prophet(holidays=holiday,seasonality_mode='additive', changepoint_prior_scale = 0.1, seasonality_prior_scale=0.01)
  m.fit(data)

  # model predictions
  future = m.make_future_dataframe(periods=1)
  model_prediction = m.predict(future) 
  prophet_prediction = float(model_prediction[ 'yhat'][-1:])
  return prophet_prediction


def arima(ticker):
  """
  Forcasting using ARIMA ! by Getting the desired data from yahoo, 
  then finding the best order of arima params then the comes the ARIMA's turn
  Args:
      (str) ticket - the ticker of desired dataset (company)
  Returns:
      (float) arima_output - the model out-put (the prediction of the next day)
      (float) diff - the model output - today's price (the diff between tomorrow's prediction and today's real value)
  """
    
  # data gathering
  df = pdr.DataReader(ticker, data_source='yahoo', start='2016-01-01')
  df.index = pd.to_datetime(df.index, format="%Y/%m/%d")
  df = pd.Series(df['Close'])
  last_day=df[-1]

  # finding the best order
  auto_order = pm.auto_arima(df, start_p=0, start_q=0, test='adf', max_p=3, max_q=3, m=1,d=None,seasonal=False   
                    ,start_P=0,D=0, trace=True,error_action='ignore',suppress_warnings=True,stepwise=True)
  best_order = auto_order.order

  # model fitting
  model = ARIMA(df, order=best_order)
  model_fit = model.fit(disp=0)
  arima_prediction ,se, conf = model_fit.forecast(1)
  
  diff = arima_prediction - last_day
  
  return arima_prediction , diff


def lstm(data_set):
  """
  Getting the desired data from yahoo, then doing some data manipulation such as data
  reshaping
  Args:
      (str) data_set - the ticker of desired dataset (company)
  Returns:
      (float) diff_prediction - the model out-put (the prediction of the next day)
      (float) real_prediction - the model output + today's price (real price of tomorrow)
  """

  # data gathering
  df = pdr.DataReader(data_set, data_source='yahoo', start=date.today() - timedelta(100))

  # data manipulation

  # creating a new df with Xt - Xt-1 values of the close prices (most recent 60 days)
  close_df = df['2012-01-01':].reset_index()['Close'][-61:]
  close_diff = close_df.diff().dropna()
  data = np.array(close_diff).reshape(-1, 1)

  # reshaping the data to 3D to be accepted by our LSTM model
  model_input = np.reshape(data, (1, 60, 1))

  # loading the model and predicting
  loaded_model = load_model("lstm_f_60.hdf5")
  model_prediction = float(loaded_model.predict(model_input))
  real_prediction = model_prediction + df['Close'][-1]
  

  return model_prediction, real_prediction


def Regression(ticker):
  """
  Forcasting using an ensambled model between SVR, Ridge and Linear regression! by Getting the desired data from yahoo, 
  then doing some data manipulation
  Args:
      (str) ticket - the ticker of desired dataset (company)
  Returns:
      (float) arima_output - the model out-put (the prediction of the next day)
      (float) diff - the model output - today's price (the diff between tomorrow's prediction and today's real value)
  """
  start_date = datetime.now() - timedelta(1)
  start_date = datetime.strftime(start_date, '%Y-%m-%d')

  df = pdr.DataReader(ticker, data_source='yahoo', start=start_date)  # read data
  df.drop('Volume', axis='columns', inplace=True)
  X = df[['High', 'Low', 'Open', 'Adj Close']]  # input columns
  y = df[['Close']]  # output column
  input = X
  loaded_model = pickle.load(open('regression_model.pkl', 'rb'))
  reg_prediction = loaded_model.predict(input)
  reg_diff=reg_prediction-df.Close[-1]

  return  reg_prediction,reg_diff

# def Transformer(ticker):
#   seq_len = 32

#   start_date = datetime.now() - timedelta(48)
#   start_date = datetime.strftime(start_date, '%Y-%m-%d')

#   df = pdr.DataReader(ticker, data_source='yahoo', start=start_date)

#   df.drop('Volume', axis=1, inplace=True)

#   # df[df.columns] = scaler.fit_transform(df)
#   df = df[['High', 'Low', 'Open', 'Adj Close', 'Close']]

#   '''Create training, validation and test split'''

#   test_data = df.values

#   # Test data
#   X_test, y_test = [], []
#   for i in range(seq_len, len(test_data)):
#       X_test.append(test_data[i - seq_len:i])
#       y_test.append(test_data[:, 4][i])
#   X_test, y_test = np.array(X_test), np.array(y_test)

#   custom_objects = {"Time2Vector": Time2Vector,
#                     "MultiAttention": MultiAttention,
#                     'TransformerEncoder': TransformerEncoder}
#   with keras.utils.custom_object_scope(custom_objects):
#       final_model = load_model('Transformer+TimeEmbedding.hdf5')

#   trans_prediction = float(final_model.predict(X_test)[-1])
#   trans_difference = trans_prediction - df.Close[-1]

#   return trans_prediction, trans_difference


# # The APP

# In[12]:


app = FastAPI()


@app.get('/')
def index():
    return {'message': 'This is your fav stock predictor!'}


@app.post('/predict')
async def predict_price(data: str):
    if data == 'F':
      prophet_prediction = float(prophet(data))
      arima_prediction, diff = arima(data)
      model_prediction, lstm_prediction = lstm(data)
      reg_prediction,reg_diff = Regression(data)
#       trans_prediction, trans_difference = Transformer(data)

      return {
        'Prophet prediction': prophet_prediction,
        'Arima prediction' : arima_prediction[0],
        'LSTM prediction' : lstm_prediction,
        'regression prediction' : reg_prediction[0]
#         'Transformer prediction': trans_prediction
            }

    else:
      return {"the ticker not supported yet"}

    

if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8080)

