import pandas as pd
import numpy as np


def dataframe_to_dict(df: pd.DataFrame) -> dict:

    df_dict = {}
    for i in range(len(df)):
        row = df.iloc[i]
        df_dict[f"exercise_{row.id}"] = {
            "name_exercise": row.name_exercise,
            "movement_pattern": row.movement_pattern, 
            "movement_type":row.movement_type,
            "body_region": row.body_region,
            "load_class": row.load_class,
            "muscles": row.muscles,
            "equipments": row.equipments
        }

    return df_dict