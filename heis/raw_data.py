from tqdm import tqdm
import pandas as pd
import numpy as np
import pyodbc

import pathlib
import os
import sqlite3

from .utils import build_year_interval
from .general import Defults, other_metadata, columns_properties


class AccessFile:
    def __init__(self, year, raw_data_directory=Defults.raw_dir):
        self.year = year
        self.raw_data_directory = raw_data_directory

    def make_connection_string(self, directory):
        files = [f.lower() for f in os.listdir(directory)]
        accdb_file = None
        for file in files:
            if (file.find('.mdb')>=0) or (file.find('.accdb')>=0):
                accdb_file = file
                break
        if accdb_file is None:
            raise FileNotFoundError

        conn_str = (
            r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};'
            f"DBQ={directory}\\{accdb_file};"
            )
        return conn_str

    def create_connection(self):
        year_directory = pathlib.PurePath(self.raw_data_directory).joinpath(f"HEIS{self.year}")
        connection_string = self.make_connection_string(year_directory)
        self.connection = pyodbc.connect(connection_string)
        self.cursor = self.connection.cursor()

    def close_connection(self):
        self.cursor.close()
        self.connection.close()

    def get_tables_list(self):
        available_tables = []
        for row in self.cursor.tables():
            table_name = row.table_name
            if (table_name.find("MSys")==-1):
                available_tables.append(table_name)
        return available_tables

    def get_table(self, table_name):
        rows = self.cursor.execute(f"SELECT * FROM [{table_name}]").fetchall()
        headers = [c[0] for c in self.cursor.description]
        df = pd.DataFrame.from_records(rows, columns=headers)
        return df

    def read_table(self, table_name):
        self.create_connection()
        df = self.get_table(table_name=table_name)
        self.close_connection()
        return df



def _change_1380_table_names(year, table_name):
    if year == 1380:
        if table_name in other_metadata['unusual_names_of_1380']:
            table_name = other_metadata['unusual_names_of_1380'][table_name]
    return table_name


def extract_tables_as_csv(year:int, raw_data_directory=Defults.raw_dir, csv_directory=Defults.csv_dir):
    year_directory = csv_directory.joinpath(str(year))
    pathlib.Path(year_directory).mkdir(parents=True, exist_ok=True)
    access_file = AccessFile(year, raw_data_directory)
    access_file.create_connection()
    available_tables = access_file.get_tables_list()
    for table_name in tqdm(available_tables, desc=f"Extracting csv from HEIS{year}", unit="table"):
        try:
            df = access_file.get_table(table_name)
        except (pyodbc.ProgrammingError, pyodbc.OperationalError):
            tqdm.write(f"table {table_name} from {year} failed to convert")
            continue
        table_name = _change_1380_table_names(year, table_name)
        df.to_csv(year_directory.joinpath(f"{table_name}.csv"), index=False)
    access_file.close_connection()


def extract_csv_files(from_year=None, to_year=None, raw_data_directory=Defults.raw_dir, csv_directory=Defults.csv_dir):
    from_year, to_year = build_year_interval(from_year=from_year, to_year=to_year)

    for year in range(from_year, to_year):
        extract_tables_as_csv(year, raw_data_directory=raw_data_directory, csv_directory=csv_directory)


def extract_raw_data_to_db(from_year=None, to_year=None, raw_data_directory=Defults.raw_dir, directory=Defults.local_directory):
    from_year, to_year = build_year_interval(from_year=from_year, to_year=to_year)
    sql_connection = sqlite3.connect(directory.joinpath("raw_data.db"))
    for year in range(from_year, to_year):
        access_file = AccessFile(year, raw_data_directory)
        access_file.create_connection()
        available_tables = access_file.get_tables_list()
        for table_name in tqdm(available_tables, desc=f"Extracting tables from HEIS{year}", unit="table"):
            try:
                df = access_file.get_table(table_name)
            except (pyodbc.ProgrammingError, pyodbc.OperationalError):
                tqdm.write(f"table {table_name} from {year} failed to convert")
                continue
            table_name = _change_1380_table_names(year, table_name)
            for column in df.columns:
                try:
                    df.loc[:, column] = pd.to_numeric(df[column], downcast='unsigned')
                except ValueError:
                    continue
            df.to_sql(table_name, sql_connection, if_exists='replace', index=False)


def _select_year(dictionary:dict, year:int) -> int|None:
    pattern_list = list(dictionary.keys())
    if len(pattern_list) == sum([True for element in pattern_list if type(element) is str]):
        return None
    selected_pattern = None
    for pattern in pattern_list:
        if pattern <= year:
            if (selected_pattern is None) or (selected_pattern <= pattern):
                selected_pattern = pattern
    return selected_pattern

def _get_column_property(year, table_name, column, urban=None):
    if urban is None:
        try:
            property_collection = columns_properties[table_name]["columns"]["both"][column]
        except KeyError:
            property_collection = columns_properties[table_name]["columns"][column]
    elif urban is True:
        property_collection = columns_properties[table_name]["columns"]["urban"][column]
    elif urban is False:
        property_collection = columns_properties[table_name]["columns"]["rural"][column]
    print(f"{column}: {property_collection}")
    selected_year = _select_year(property_collection, year)
    if selected_year is None:
        selected_property = property_collection
    else:
        selected_property = property_collection[selected_year]
    return selected_property

def _build_file_name(year:int, table:str, urban:bool):
    year_part = year % 100 if year < 1400 else year
    rural_urban = "U" if urban else "R"
    file_name = f"{rural_urban}{year_part}{table}.csv"
    return file_name

def _clean_table(df:pd.DataFrame):
    df = df.copy()
    for column in df.columns:
        if pd.api.types.is_numeric_dtype(df[column]):
            continue
        for ch in ["\n", "\r", ",", "@", "-"]:
            df.loc[:, column] = df.loc[:, column].str.replace(ch, "")
    df = df.replace("\A\s*\Z", np.nan, regex=True)
    return df

def open_table_csv(year:int, table_name:str, urban:bool|None=None):
    table_names = columns_properties[table_name]["file_codes"]
    table_file_code = table_names[_select_year(table_names, year)]
    if urban is None:
        urban = [True, False]
    else:
        urban = [urban]
    dfc = []
    for t in urban:
        file_name = _build_file_name(year=year, table=table_file_code, urban=t)
        df = pd.read_csv(f"D:\\PyHEIS_Data\\3_csv_files\\{year}\\{file_name}", low_memory=False)
        dfc.append(df)
    table = pd.concat(dfc, axis="index", ignore_index=True)
    table = _clean_table(table)
    return table

def apply_columns_properties(table, year, table_name, urban=None):
    for column in table.columns:
        print(f"year: {year} column: {column}   ", end="\r")
        column_props = _get_column_property(year, table_name, column, urban)

        if "drop" in column_props:
            table = table.drop(columns=column)
            continue
        if "replace" in column_props:
            table[column] = table[column].replace(column_props["replace"])
        if "type" in column_props:
            if column_props["type"] == "boolean":
                filt = table[column].notna()
                table.loc[filt, column] = (table[column] == column_props["true_condition"])
            elif column_props["type"] == "category":
                table[column] = table[column].astype("Int32").astype("category")
                table[column] = table[column].cat.rename_categories(column_props["categories"])
            elif column_props["type"] == "string":
                pass
            else:
                table[column] = pd.to_numeric(table[column], downcast=column_props["type"])
        if "new_name" in column_props:
            table = table.rename(columns={column: column_props["new_name"]})
    return table

def load_table_from_csv(year:int, table_name:str):
    try:
        urban_rural = columns_properties[table_name]["property"]["urban_rural"]
        if year in urban_rural:
            dfs = []
            for urban in [True, False]:
                df = open_table_csv(year=year, table_name=table_name, urban=urban)
                df = apply_columns_properties(df, year=year, table_name=table_name, urban=urban)
                dfs.append(df)
            return pd.concat(dfs, axis="index", ignore_index=True)
    except KeyError:
        pass
    df = open_table_csv(year=year, table_name=table_name)
    df = apply_columns_properties(df, year=year, table_name=table_name)
    return df

def make_parquet(year:int, table_name:str, parquets_directory=Defults.parquets_dir):
    table = open_table_csv(year, table_name)
    table = apply_columns_properties(table, year, table_name)
    pathlib.Path(parquets_directory).mkdir(exist_ok=True)
    table.to_parquet(parquets_directory.joinpath(f"{year}_{table_name}.parquet"))
