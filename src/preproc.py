import pandas as pd


def add_fips(df, fips_loc, left, right, level):

    if (level != "state") and (level != "county"):
        print("Error: set level to 'state' or 'county'")
        print("Exiting....\n")
        exit()

    fips = pd.read_csv(fips_loc, dtype={"fips":str})
    fips.rename(columns={"fips":"Fips"}, inplace=True)
    if level == "state":
        fips = fips[~fips.county.notnull()]

    fips_cols = right.copy()
    fips_cols.insert(0,"Fips")

    df = pd.merge(df,
                  fips[fips_cols],
                  left_on=left,
                  right_on=right,
                  how="left")

    df = df.iloc[:, :-2]

    return df


def add_regions(df, regions_loc, left, right):

    regions = pd.read_csv(regions_loc, dtype={"StateFips":str})
    df = pd.merge(df,
                  regions,
                  left_on=left,
                  right_on=right,
                  how="left")
    return df


def add_reportdate(df, filename):

    reportdate = re.findall(r"(\d{4}-\d{2}-\d{2})", filename)[0]
    df["Report Date"] = reportdate
    df["Report Date"] = pd.to_datetime(df["Report Date"], format="%Y-%m-%d")
    return df


def add_state_names(df, abbr_loc, left, right):

    abbr = pd.read_csv(abbr_loc)
    df[left] = df[left].str.upper()
    df = pd.merge(df,
                  abbr,
                  left_on=left,
                  right_on=right,
                  how="left")

    return df


def fix_headers(df, cols):

    newcols = [header.title() for header in cols]
    newcols = [header.replace(" ","") for header in newcols]
    df.columns = newcols
    return df


def keep_only(df, cols):
    return df[cols]


def load_dfs(files, has_fips, has_reportdate, skiprows=0):
    """
    has_fips: tuple (Boolean, str), indicates if the csv already has fips and
        if so what the column name is for the fips column

    has_reportdate: tuple (Boolean, Header, Date format), indicates if csv has
        report date and if so column name of the column and the date format
    """

    dfs = []

    if len(files) != len(has_fips) or len(files) != len(has_reportdate):
        print("Error in loading csvs to DataFrames.  files and has_fips or has_reportdate differ in length.")
        print("Exiting...\n")
        exit()

    for i in range(len(files)):
        if has_fips[i][0] and has_reportdate[i][0]:
            df = pd.read_csv(files[i], dtype={has_fips[i][1]:str}, skiprows=skiprows)
            df[has_reportdate[i][1]] = pd.to_datetime(df[has_reportdate[i][1]], format=has_reportdate[i][2], errors="coerce")
            df.rename(columns={has_reportdate[i][1]:"Report Date", has_fips[i][1]:"Fips"}, inplace=True)
        elif has_fips[i][0]:
            df = pd.read_csv(files[i], dtype={has_fips[i][1]:str}, skiprows=skiprows)
            df.rename(columns={has_fips[i][1]:"Fips"}, inplace=True)
            df = add_reportdate(df, files[i])
        elif has_reportdate[i][0]:
            df = pd.read_csv(files[i], skiprows=skiprows)
            df[has_reportdate[i][1]] = pd.to_datetime(df[has_reportdate[i][1]], format=has_reportdate[i][2], errors="coerce")
            df.rename(columns={has_reportdate[i][1]:"Report Date"}, inplace=True)
        else:
            df = pd.read_csv(files[i], skiprows=skiprows)
            df = add_reportdate(df, files[i])
        df = fix_headers(df, df.columns)
        dfs.append(df)

    print("\tDataFrames loaded to memory\n")

    return dfs
