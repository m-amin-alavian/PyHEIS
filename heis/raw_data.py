from tqdm import tqdm
import pandas as pd
import numpy as np
import pyodbc
import sys

import pathlib
import logging
import os
import sqlite3

from .utils import build_year_interval, select_version, get_version
from .metadata import Defaults, Metadata

logging.basicConfig(filename="raw_data.log", level=logging.DEBUG)

class AccessFile:
    def __init__(self, year, raw_data_directory=Defaults.raw_dir):
        self.year = year
        self.raw_data_directory = raw_data_directory

    def make_connection_string(self, directory):
        if sys.platform == "win32":
            files = [f.lower() for f in os.listdir(directory)]
            join_string = "\\"
            driver = "Microsoft Access Driver (*.mdb, *.accdb)"
        else:
            files = [f for f in os.listdir(directory)]
            join_string = "/"   
            driver = "MDBTools"

        accdb_file = None
        for file in files:
            if (file.find('.mdb')>=0) or (file.find('.accdb')>=0):
                accdb_file = file
                break
        if accdb_file is None:
            raise FileNotFoundError

        conn_str = (
            f"DRIVER={{{driver}}};"
            f"DBQ={directory}{join_string}{accdb_file};"
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
        if table_name in Metadata.other['unusual_names_of_1380']:
            table_name = Metadata.other['unusual_names_of_1380'][table_name]
    return table_name


def _save_extracted_table(access_file, table_name, storage_technology, csv_directory, sql_directory):
    try:
        df = access_file.get_table(table_name)
    except (pyodbc.ProgrammingError, pyodbc.OperationalError):
        tqdm.write(f"table {table_name} from {access_file.year} failed to extract")
        return
    table_name = _change_1380_table_names(access_file.year, table_name)
    if storage_technology == "csv":
        year_directory = csv_directory.joinpath(str(access_file.year))
        pathlib.Path(year_directory).mkdir(parents=True, exist_ok=True)
        df.to_csv(year_directory.joinpath(f"{table_name}.csv"), index=False)
    elif storage_technology == "sql":
        with sqlite3.connect(sql_directory.joinpath("raw_data.db")) as sql_connection:
            df.to_sql(table_name, sql_connection, if_exists='replace', index=False)


def extract_tables_from_access_file(year:int, raw_data_directory=Defaults.raw_dir,
            storage_technology=Defaults.storage, csv_directory=Defaults.csv_dir, sql_directory=Defaults.local_dir):
    access_file = AccessFile(year, raw_data_directory)
    access_file.create_connection()
    available_tables = access_file.get_tables_list()
    for table_name in tqdm(available_tables, desc=f"Extracting data from HEIS{year}", unit="table"):
        _save_extracted_table(access_file=access_file,
            table_name=table_name,
            storage_technology=storage_technology,
            csv_directory=csv_directory,
            sql_directory=sql_directory)
    access_file.close_connection()


def extract_raw_data(from_year=None, to_year=None, raw_data_directory=Defaults.raw_dir,
            storage_technology=Defaults.storage, csv_directory=Defaults.csv_dir, sql_directory=Defaults.local_dir):
    # TODO change function name!
    from_year, to_year = build_year_interval(from_year=from_year, to_year=to_year)

    for year in range(from_year, to_year):
        extract_tables_from_access_file(year, raw_data_directory=raw_data_directory, storage_technology=storage_technology,
            csv_directory=csv_directory, sql_directory=sql_directory)


def _get_column_property(year, table_name, column, urban=None):
    if urban is None:
        try:
            all_columns = Metadata.columns_properties[table_name]["columns"]["both"]
        except KeyError:
            all_columns = Metadata.columns_properties[table_name]["columns"]
    elif urban is True:
        all_columns = Metadata.columns_properties[table_name]["columns"]["urban"]
    elif urban is False:
        all_columns = Metadata.columns_properties[table_name]["columns"]["rural"]
    try:
        column_property = all_columns[column]
    except KeyError:
        try:
            missing_treatment = Metadata.columns_properties[table_name]['property']['missings']
        except KeyError:
            missing_treatment = "pass"
        return missing_treatment
    logging.debug("{}: {}".format(column, column_property))
    selected_property = get_version(column_property, year)
    return selected_property


def _build_file_name(year:int, table:str, urban:bool):
    year_part = year % 100 if year < 1400 else year
    rural_urban = "U" if urban else "R"
    file_name = f"{rural_urban}{year_part}{table}.csv"
    return file_name


def _fix_bad_ids(df, year:int|None=None):
    if df.iloc[:, 0].dtype is str:
        if year == 1374:
            filt = df.iloc[:, 0].str.isnumeric()
            df = df.loc[filt]
    return df


def _clean_table(df:pd.DataFrame, year:int|None=None):
    df = df.copy()
    for column in df.columns:
        if pd.api.types.is_numeric_dtype(df[column]):
            continue
        for ch in ["\n", "\r", ",", "@", "-", "+"]:
            df.loc[:, column] = df.loc[:, column].str.replace(ch, "", regex=False)
    df = df.replace("\A\s*\Z", np.nan, regex=True)
    df = _fix_bad_ids(df, year)
    return df


def open_table(year:int, table_name:str, urban:bool, source=Defaults.storage):
    table_names = Metadata.columns_properties[table_name]["file_codes"]
    table_file_code = table_names[select_version(table_names, year)]

    file_name = _build_file_name(year=year, table=table_file_code, urban=urban)
    if source == "csv":
        table = pd.read_csv(f"D:\\PyHEIS_Data\\3_csv_files\\{year}\\{file_name}", low_memory=False)
    elif source == "sql":
        # TODO: add sql support
        return

    table = _clean_table(table, year)
    return table


def apply_columns_properties(table, year, table_name, urban=None):
    for column in table.columns:
        logging.debug("year: {}, table: {}, column: {}".format(year, table, column))
        column_props = _get_column_property(year, table_name, column, urban)
        if column_props == "pass":
            continue
        elif column_props == "drop":
            table = table.drop(columns=column)
            continue
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


def load_table(year:int, table_name:str):
    logging.debug(f"Loading {table_name} for {year}")
    try:
        urban_rural = Metadata.columns_properties[table_name]["property"]["urban_rural"]
        logging.debug(f"{table_name} table in {year} has separated rural and urban property")
    except KeyError:
        urban_rural = []

    dfs = []
    for urban in [True, False]:
        df = open_table(year=year, table_name=table_name, urban=urban)
        if year in urban_rural:
            df = apply_columns_properties(df, year=year, table_name=table_name, urban=urban)
        else:
            df = apply_columns_properties(df, year=year, table_name=table_name, urban=None)
        logging.debug("year: {}, table: {} poperties applied".format(year, table_name))
        dfs.append(df)
    df = pd.concat(dfs, axis="index", ignore_index=True)
    return df


def make_parquet(years:int|list|None=None, table_names:str|list|None=None, parquets_directory=Defaults.parquets_dir):
    """Make parquet data
       :param year: year to make data for
       :type year: int
       :param table_name: name of table to use
       :type table_name: str
       :param parquets_directory: directory for the file
       :type parquets_directory: str
       :return: A parquet table
       :rtype: parquet table
    """
    if years is None:
        years = list(range(Defaults.first_year, Defaults.last_year+1))
    elif type(years) is int:
        years = [years]
    if table_names is None:
        table_names = Defaults.table_names
    elif type(table_names) is str:
        table_names = [table_names]
    pbar = tqdm(total=len(years)*len(table_names), desc="Preparing ...", unit="Table")
    for year in years:
        for table_name in table_names:
            pbar.update()
            pbar.desc = f"Year: {year}, Table: {table_name}"
            table = load_table(year, table_name)
            pathlib.Path(parquets_directory).mkdir(exist_ok=True)
            table.to_parquet(parquets_directory.joinpath(f"{year}_{table_name}.parquet"))
    pbar.close()

