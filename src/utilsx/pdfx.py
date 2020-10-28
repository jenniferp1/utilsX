
# import standard Python packages
import camelot
import re
import pandas as pd
import numpy as np
from datetime import datetime, date

# import other homegrown modules
from utilsx.readin import read_yaml
from utilsx.readin import checkdir
from utilsx.opsys import mv_file

"""
This module contains functions for extracting data from pdf tables
It is broken into sections by function purpose
1. General functions - generic; setups configurations used by Specific functions
2. Specific functions - functions for specific processing based on data sources
3. Caller functions - short, single-purpose, only used to launch Specific functions from General functions
    Used so user can specify pages in pdf with tables to parse and identify the Specific functions
    needed to process the data source
"""

"""
# GENERAL FUNCTIONS
"""

def parse_pdf(url, txt, pdf_name):

    """
    Note: calling this function requires the user to set up a file called
    pdf_formatter.yml in their launch directory
    """

    curdir = os.getcwd()
    yaml_pdf = f"{curdir}/pdf_formatter.yml"  #this file is needed in your launch directory if downloading pdfs
    data = read_yaml([yaml_pdf, url])
    funct = data["function"]

    pdf_name = f"'{pdf_name}'"
    txt = f"'{txt}'"

    funct = funct.replace("pdf_name", pdf_name)
    funct = funct.replace("txt", txt)
    funct = str(funct)
    # print(f"\n\tCalling function to be used: {funct}\n")  # Uncomment for degbugging

    loc = {}
    exec(funct, globals(), loc)

    df = loc['dframe']

    if df.size > 0:
        return df

    return pd.DataFrame()


"""
# CALLER FUNCTIONS
"""

def call_parse_mn_weekly_report(name, txt, pgs):
    name = str(name)
    pgs = str(pgs)
    dframe = parse_mn_weekly_report(name, txt, pgs)
    return dframe


"""
# SPECIFIC FUNCTIONS
"""

# Minnesota Department of Health - COVID-19 data
def parse_mn_weekly_report(pdf_name, txt, pgs, ws=101):

    tables = camelot.read_pdf(pdf_name, pages=pgs)
    datatable = pd.DataFrame()

    for t in tables:
        whitespace = t.parsing_report["whitespace"]
        if whitespace < ws:
            ws = whitespace
            datatable = t

    dframe = datatable.df

    day = re.findall(r"(\d{1,2}\/\d{1,2}\/\d{4})", txt)[0]
    day = datetime.strptime(day,"%m/%d/%Y")
    day = day.strftime("%Y%m%d")

    main_folder = "./minnesota/original_docs"
    checkdir(main_folder)  # create folder if fpath does not exist
    file_weeklypos = f"{main_folder}/mdh_weekly_positivity_{day}.csv"

    dframe.to_csv(file_weeklypos,index=False)

    dframe = clean_mn_weekly_report(file_weeklypos)

    mv_file(pdf_name, main_folder)

    return dframe


def clean_mn_weekly_report(file_weeklypos):

    dframe = pd.read_csv(file_weeklypos, skiprows=1)

    partitions = 2
    dfs = np.array_split(dframe, partitions, axis=1)

    dfs[0].columns = ["County","Positive"]
    dfs[1].columns = ["County","Positive"]

    dframe = dfs[0].append(dfs[1], ignore_index=True)

    dframe.replace("%", "", regex=True, inplace=True)
    dframe.replace("\n", "", regex=True, inplace=True)
    dframe.replace("\t", "", regex=True, inplace=True)

    dframe['County'] = dframe['County'].str.replace("\-?(\d+\.?\d*|\d*\.?\d+)", "")

    dframe = dframe[~dframe.County.str.startswith("Unknown")]

    fips = pd.read_csv("/home/datasets/county_fips.csv", dtype={"fips":str})
    fips = fips[fips.stateiso=="MN"]
    fips["county"] = fips["county"].str.replace(" County","")

    dframe = pd.merge(dframe, fips, left_on="County", right_on="county", how="left")
    dframe.drop(columns=["county"], inplace=True)

    # print(dframe.head())

    return dframe
