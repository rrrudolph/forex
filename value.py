import pandas as pd
import sqlite3
from datetime import datetime
import time
from create_db import value_db, correlation_db
from symbols_lists import mt5_symbols, fin_symbols, spreads

CORR_CON = sqlite3.connect(correlation_db)
VAL_CON = sqlite3.connect(value_db)


''' 
The goal of this module is to read the raw correlation data and derive buy/sell values from it.
I'll do this by symbol and also by index.  So once I have the data for each symbol, I'll then
combine it similar to how I made the indexes, inverting when I need to and adding them all together.
There are up to 3 sets of data for each symbol and I'll want to keep them separated throughout.
'''

timeframes = [
    '_LTF',
    '_MTF',
    '_HTF',
]

# I don't know how to get a list of table names from the db so..
# Iter each symbol and try to open a table from each timeframe
for symbol in mt5_symbols['majors']:

    # This will end up holding the LTF, MTF and HTF value columns
    df = pd.DataFrame()

    for tf in timeframes:

        name = symbol + tf
        print(name)

        try:
            cor_df = pd.read_sql(f'SELECT * FROM {name}', CORR_CON)
        except:
            continue
        
        if len(cor_df) < 10:
            continue

        cor_df.index = pd.to_datetime(cor_df['index'])

        # Parse the column names because I need to multiply each symbols column by its corr column
        # I left myself some keys so I could easily grab what I need
        things_to_omit = [r'*', 'corr', 'index']
        cols = cor_df.columns.tolist()

        new_cols = []
        for col in cols:
            if all(x not in col for x in things_to_omit):
                new_cols.append(col)
        
        # Multiply the values
        temp_df = pd.DataFrame()
        for col in new_cols:
            temp_df[f'{col}'] = cor_df[f'{col}'] * cor_df[f'{col}_corr']
        
        temp_df = temp_df.fillna(0)
        cor_sum = temp_df.sum(axis=1)

        # This is what will be saved to the db
        df[f'{tf[1:]}'] = round(cor_sum - cor_df[fr'*{symbol}*'], 4)
        
    df.to_sql(symbol, VAL_CON, if_exists='replace', index=True)

        # print(cols)
        # quit()
        # time.sleep(99)

