# -*- coding: utf-8 -*-
"""Stock Price Prediction.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1td0y8jCAnBEKuwQsr2Vk2VOQOjBzCMB8
"""

#Import the libraries
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf

# Define the stock ticker and date range
start = '2012-01-01'
end = '2022-12-21'
stock = 'GOOG'

# Download stock data using yfinance with error handling
try:
    data = yf.download(stock, start=start, end=end)
    if data.empty:
        raise ValueError(f"No data found for ticker {stock} between {start} and {end}.")
except Exception as e:
    print(f"Error downloading data: {e}")
    exit()

# Reset index to move the date from index to a column
data.reset_index(inplace=True)

# Validate essential columns are present
required_columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
if not all(column in data.columns for column in required_columns):
    missing = list(set(required_columns) - set(data.columns))
    raise ValueError(f"Missing columns in data: {missing}")

# Display first few rows of the data
print("Downloaded Data:")
print(data.head())

"""
# -------------------- Moving Averages Calculation -------------------- #"""

# Calculate 100-day moving average
ma_100_days = data['Close'].rolling(window=100).mean()

# Plot 100-day moving average and closing price
plt.figure(figsize=(10, 6))
plt.plot(data['Date'], ma_100_days, 'r', label='100-Day MA')
plt.plot(data['Date'], data['Close'], 'g', label='Closing Price')
plt.title(f'{stock} Closing Price and 100-Day Moving Average')
plt.xlabel('Date')
plt.ylabel('Price (USD)')
plt.legend()
plt.show()

# Calculate 200-day moving average
ma_200_days = data['Close'].rolling(window=200).mean()

# Plot 100-day MA, 200-day MA, and closing price
plt.figure(figsize=(10, 6))
plt.plot(data['Date'], ma_100_days, 'r', label='100-Day MA')
plt.plot(data['Date'], ma_200_days, 'b', label='200-Day MA')
plt.plot(data['Date'], data['Close'], 'g', label='Closing Price')
plt.title(f'{stock} Closing Price with 100 & 200-Day Moving Averages')
plt.xlabel('Date')
plt.ylabel('Price (USD)')
plt.legend()
plt.show()

# Remove rows with NaN values resulting from moving averages
data.dropna(inplace=True)

"""# -------------------- Data Splitting -------------------- #"""

# Define training and testing split (80% train, 20% test)
train_size = int(len(data) * 0.80)
test_size = len(data) - train_size

# Ensure there is enough data for splitting
if train_size < 100:
    raise ValueError("Training data is too small. Consider adjusting the split ratio or the window size.")

data_train = data[['Close']].iloc[:train_size].copy()
data_test = data[['Close']].iloc[train_size:].copy()

print(f"Training data points: {data_train.shape[0]}")
print(f"Testing data points: {data_test.shape[0]}")

"""# -------------------- Data Scaling -------------------- #"""

# Initialize MinMaxScaler
scaler = MinMaxScaler(feature_range=(0, 1))

# Fit scaler on training data and transform
data_train_scale = scaler.fit_transform(data_train)

# Check for scaling errors
if np.isnan(data_train_scale).any():
    raise ValueError("Scaling resulted in NaN values in training data.")

"""# -------------------- Creating Training Sequences -------------------- #"""

# Define window size
window_size = 100

x_train = []
y_train = []

# Create sequences of 100 data points for training
for i in range(window_size, len(data_train_scale)):
    x_train.append(data_train_scale[i - window_size:i, 0])
    y_train.append(data_train_scale[i, 0])

# Convert lists to numpy arrays
x_train, y_train = np.array(x_train), np.array(y_train)

# Reshape x_train to be [samples, time_steps, features]
x_train = np.reshape(x_train, (x_train.shape[0], x_train.shape[1], 1))

# Validate shapes
print(f"x_train shape: {x_train.shape}")
print(f"y_train shape: {y_train.shape}")

"""# -------------------- Building the LSTM Model -------------------- #"""

# Initialize the Sequential model
model = Sequential()

# Add first LSTM layer with Dropout
model.add(LSTM(units=50, activation='relu', return_sequences=True, input_shape=(x_train.shape[1], 1)))
model.add(Dropout(0.2))

# Add second LSTM layer with Dropout
model.add(LSTM(units=60, activation='relu', return_sequences=True))
model.add(Dropout(0.3))

# Add third LSTM layer with Dropout
model.add(LSTM(units=80, activation='relu', return_sequences=True))
model.add(Dropout(0.4))

# Add fourth LSTM layer with Dropout
model.add(LSTM(units=120, activation='relu'))
model.add(Dropout(0.5))

# Add the output layer
model.add(Dense(units=1))

# Compile the model with Adam optimizer and Mean Squared Error loss
model.compile(optimizer='adam', loss='mean_squared_error')

# Display model summary
model.summary()

"""# -------------------- Training the Model -------------------- #"""

# Train the model with validation split and early stopping
from keras.callbacks import EarlyStopping

# Define early stopping to prevent overfitting
early_stop = EarlyStopping(monitor='loss', patience=10, restore_best_weights=True)

# Fit the model
history = model.fit(x_train, y_train, epochs=50, batch_size=32, verbose=1, callbacks=[early_stop])

# Plot training loss
plt.figure(figsize=(8,6))
plt.plot(history.history['loss'], label='Training Loss')
plt.title('Model Loss During Training')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.legend()
plt.show()

"""# -------------------- Preparing Test Data -------------------- #"""

# Get the last 100 days from training data to create the initial test sequence
past_100_days = data_train.tail(window_size).copy()

# Combine past 100 days with test data for scaling
data_test_combined = pd.concat([past_100_days, data_test], ignore_index=True)

# Scale the combined test data
data_test_scale = scaler.transform(data_test_combined)

# Check for scaling errors
if np.isnan(data_test_scale).any():
    raise ValueError("Scaling resulted in NaN values in test data.")

# Create test sequences
x_test = []
y_test = []

for i in range(window_size, len(data_test_scale)):
    x_test.append(data_test_scale[i - window_size:i, 0])
    y_test.append(data_test_scale[i, 0])

# Convert lists to numpy arrays
x_test, y_test = np.array(x_test), np.array(y_test)

# Reshape x_test to be [samples, time_steps, features]
x_test = np.reshape(x_test, (x_test.shape[0], x_test.shape[1], 1))

# Validate shapes
print(f"x_test shape: {x_test.shape}")
print(f"y_test shape: {y_test.shape}")

"""# -------------------- Making Predictions -------------------- #"""

# Predict using the trained model
y_pred_scaled = model.predict(x_test)

# Inverse transform the scaled predictions and actual values
y_pred = scaler.inverse_transform(y_pred_scaled)
y_actual = scaler.inverse_transform(y_test.reshape(-1, 1))

"""# -------------------- Evaluating the Model -------------------- #"""

# Calculate evaluation metrics
from sklearn.metrics import mean_squared_error, mean_absolute_error

mse = mean_squared_error(y_actual, y_pred)
mae = mean_absolute_error(y_actual, y_pred)
print(f"Mean Squared Error on Test Data: {mse}")
print(f"Mean Absolute Error on Test Data: {mae}")

# Plot the predictions vs actual prices
plt.figure(figsize=(14, 7))

import matplotlib.pyplot as plt

# Assuming 'Date' is the correct column name and exists in data_test
# If the column name is different, update it accordingly
# Example: If the column is named 'date', use data_test['date'] instead

# Check if 'Date' column exists in data_test
if 'Date' in data_test.columns:
    plt.plot(data_test['Date'].iloc[window_size:].values, y_pred, 'r', label='Predicted Price')
else:
    print("Error: 'Date' column not found in data_test DataFrame. Please check your data.")
    # If 'Date' column is not found, you might need to:
    # 1. Load the data again, making sure the 'Date' column is included.
    # 2. Check for any data manipulation steps that might have removed or renamed the column.
    # 3. Adjust the column name in the code if it's different (e.g., 'date', 'DATE').

plt.title(f'{stock} Predicted vs Actual Closing Prices')
plt.xlabel('Date')
plt.ylabel('Price (USD)')
plt.legend()
plt.show()

"""# -------------------- Saving the Model -------------------- #"""

# Define the model save path
model_filename = 'Stock_Predictions_Model.keras'

import os  # Import the os module

# Define the model save path
model_filename = 'Stock_Predictions_Model.keras'

# Check if the directory exists, if not, create it
save_dir = os.path.dirname(model_filename)
if save_dir and not os.path.exists(save_dir):
    os.makedirs(save_dir)

# Check if the directory exists, if not, create it
save_dir = os.path.dirname(model_filename)
if save_dir and not os.path.exists(save_dir):
    os.makedirs(save_dir)

# Save the trained model
model.save(model_filename)
print(f"Model saved to {model_filename}")