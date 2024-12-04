import fitdecode
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

def DecodeFit_DataFrame(file_path: str, frame_name: str = 'record', lat_long_update: bool = True, debug: bool = False) -> pd.DataFrame:
    """_summary_

    Args:
        file_path (str): path of raw fit file
        frame_name (str, optional): _description_. Defaults to 'record'.
        lat_long_update (bool, optional): _description_. Defaults to True.
        debug (bool, optional): _description_. Defaults to False.

    Returns:
        pd.DataFrame: processed dataframe from source fit file
    """
    # Initialize some useful variables for the loops
    check_list = good_list = []
    list_check = {}
    df_activity = pd.DataFrame([])

    # Open the file with fitdecode
    with fitdecode.FitReader(file_path) as file:
        
        # Iterate through the .FIT frames
        for frame in file:
            
            # Procede if the frame object is the correct data type
            if isinstance(frame, fitdecode.records.FitDataMessage):
                
                # Add the frames and their corresponding counts to a dictionary for debugging
                if frame.name not in check_list:
                    check_list.append(frame.name)
                    list_check[frame.name] = 1
                else:
                    list_check.update({frame.name: list_check.get(frame.name) + 1})
                
                # If the current frame is a record, we'll reset the row_dict variable
                # and add the field values for all fields in the good_list variable
                if frame.name == frame_name:
                    row_dict = {}
                    for field in frame.fields: 
                        if field.name.find('unknown') < 0:
                            if field.name not in good_list and field.name.find('unknown') < 0:
                                good_list.append(field.name)
                            row_dict[field.name] = frame.get_value(field.name)
                    
                    # Append this row's dictionary to the main dataframe
                    df_activity = pd.concat([df_activity, pd.DataFrame([row_dict])], ignore_index = True)
        
        # Update the Long/Lat columns to standard degrees
        if lat_long_update:
            for column in ['position_lat', 'position_long']:
                df_activity[column] = df_activity[column].apply(lambda x: x / ((2**32)/360))
        
        # If you want to check to see which frames are in the file, print the list_check variable
        if debug:
            print(list_check)

    return df_activity

def viz_dual_line(df, timestamp, col1, col2):
    """ Visualize two metrics on a dual-axis line chart

    Args:
        df (dataframe): input dataframe
        timestamp (timestamp): timestamp of metrics
        col1 (float): column 1 to viz
        col2 (float): column 2 to viz
    """
    # Create the figure and primary y-axis

    fig, ax1 = plt.subplots()

    # Plot the first line on the left axis
    ax1.plot(df[timestamp], df_activity[col1], color='blue', label='power')
    ax1.set_ylabel(col1, color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')

    # Create the second axis that shares the x-axis
    ax2 = ax1.twinx()

    # Plot the second line on the right axis
    ax2.plot(df_activity[timestamp], df_activity[col2], color='red', label=f'{col2}')
    ax2.set_ylabel(col2, color='red')
    ax2.tick_params(axis='y', labelcolor='red')

    # Add a legend
    fig.legend()

    plt.savefig(f'viz/{col1}_vs_{col2}.png')


# main
directory_path = 'fit_files'
file_list = []

for filename in os.listdir(directory_path):
    file_path = os.path.join(directory_path, filename)
    if os.path.isfile(file_path):
        filename = filename[:-4]
        file_list.append(filename)

print(file_list)

for file in file_list:

    df_activity = DecodeFit_DataFrame(f'{directory_path}/{file}.fit', frame_name = 'record')

    df_activity['elapsed_time'] = df_activity['timestamp'].apply(lambda x: x - df_activity.loc[0, 'timestamp'])
    df_activity['distance_miles'] = df_activity['distance']*0.000621371192
    df_activity['altitude_feet'] = df_activity['altitude']*3.28084
    df_activity['pace_minutes_per_mile'] = 26.8224/df_activity['speed']
    df_activity['timestamp'] = pd.to_datetime(df_activity['timestamp'])

    viz_dual_line(df = df_activity, timestamp = 'timestamp', col1 = 'power', col2 = 'pace_minutes_per_mile')
    viz_dual_line(df = df_activity, timestamp = 'timestamp', col1 = 'cadence', col2 = 'heart_rate')

    df_activity.to_csv(f'decoded_csv/{file}.csv')