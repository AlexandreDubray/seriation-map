from sklearn.preprocessing import MinMaxScaler, QuantileTransformer

def min_max_norm(df):
    scaler = MinMaxScaler()
    return scaler.fit_transform(df)

def quantile_norm(df):
    scaler= QuantileTransformer()
    return scaler.fit_transform(df)
