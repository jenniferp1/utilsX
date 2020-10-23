"""Open and read files.

Functions associated with the process of finding, opening, or reading
files.
"""


############################################
# Import Packages
############################################


# import standard Python packages
import yaml
import os
import re
import glob
import chardet
import requests
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin


##########################################
# Functions
##########################################

def checkdir(folder):
    """Create a directory.

    Check to see if a directory exists and create
    it if it does not.

    Parameters
    -----------
    folder : str
        Fully qualified path and folder name.

    Returns
    --------
    None : None

    Examples
    ---------
    .. code-block:: python

        > folder = "C:/Users/doejohn/Documents/MyDir"
        > checkdir(folder)
    """

    if not os.path.exists(folder):
        os.makedirs(folder)
    return


def check_last_load(url, key_phrase):
    """Check for last file loaded on GitHub.

    Given a GitHub url and a dictionary with a regex pattern and
    load date, will check for a file that is more recent than the
    provided load date.

    Regex pattern should identify a date pattern in the file name string.
    Load date should be the most recent file a user previously downloaded.

    Parameters
    ------------
    url : str
        Github url where files are located.
    key_phrase : dict
        Dictionary with date regex pattern and last load date of most recent file.

    Returns
    --------
    url : str
        URL for a more recent file or None if user previously downloaded most recent file.

    See Also
    ---------
    utilsx.readin.date_in_str
    utilsx.readin.scan_csv_list

    Examples
    ---------
    Sample dictionary format

    .. code-block:: text

        {"pattern":"\\d{4}-\\d{2}-\\d{2}", "last_date":"2020-08-31"}
    """

    urls, names = scan_csv_list(url)
    new_date = None
    pos = -999
    for i, name in reversed(list(enumerate(names))):
        if name[:4].isdigit():
            new_date = date_in_str(key_phrase["pattern"],key_phrase["last_date"],name)
            if new_date:
                pos = i
                break

    if pos >= 0:
        url = urls[pos]
    else:
        url = None
    return url


def date_in_str(pattern, prev_date, string):
    """Extract date from a string.

    Given a string with a date pattern, extract the date.

    Parameters
    -----------
    pattern : regex
        Regex date pattern (e.g., "\\d{4}-\\d{2}-\\d{2}").
    prev_date: str
        Date to compare to date extracted with regex pattern (e.g., "2020-08-31").
    string : str
        String with a date in it that will be extracted.

    Returns
    ---------
    str
        Date match extracted from string if match is more recent than prev_date; otherwise returns None.

    See Also
    ---------
    utilsx.readin.check_last_load
    """

    if re.match(pattern, string):
        m = re.match(pattern, string).group(0)
        if m > prev_date:
            return m
    return None


def file_signature(fpath):
    """Get file format.

    Try to return file format based on file signature.
    May return multiple extensions if a file signature applies
    to more than one (see :ref:`filesig-reference-label`).
    If no matching file signatures found, returns "unknown".

    Requirements: a YAML file with file formats and signatures to run.
    The YAML should be called `fileformat.yml <./fileformatyml.html>`_ and saved in the `utilsx` package.

    Sample `fileformat.yml` structure:

    format description:
        | format: ["extension"]
        | offset: 0
        | signature: ["hexadecimal notation"]

    Format description helps the user understand what file type(s) the data block applies to,
    for example, MicroSoft Office.
    Examples for "extension" are "xlsx", "csv", "xml"
    inputs values for offset and the signature's hexadecimal notation can be found
    by referring to the `File Signatures Directory <https://filesignatures.net/index.php?search=json&mode=EXT>`_.

    .. tip:: A typical fileformat.yml example is found `here <./fileformatyml.html>`_

    Parameters
    -----------
    fpath : str
        Fully qualified file name (path+name).

    Returns
    ----------
    list
        File format extension(s).

    See Also
    ----------
    utilsx.readin.get_fnames


    .. _filesig-reference-label:

    References
    ------------
    `File Signature Directory <https://filesignatures.net/index.php?search=json&mode=EXT>`_

    `File Signatures <https://www.garykessler.net/library/file_sigs.html>`_

    `How to determine file format using Python <https://hackernoon.com/determining-file-format-using-python-c4e7b18d4fc4>`_
    """

    utilsx_dir = os.path.dirname(os.path.realpath(__file__))
    utilsx_dir = os.path.realpath(utilsx_dir)
    fileformats = f"{utilsx_dir}\\fileformat.yml"

    try:
        with open(fileformats) as ff:
            data = yaml.load(ff, Loader=yaml.FullLoader)
    except:
        print(f"\nError: fileformat.yml is missing from {utilsx_dir}")
        print("\tStopping run.  Replace fileformat.yml before running again.\n")
        exit()


    file = open(fpath,"rb").read(32)
    hex_bytes = " ".join(['{:02X}'.format(byte) for byte in file])

    for element, properties in data.items():
        for signature in properties["signature"]:
            offset = properties["offset"]*2+properties["offset"]
            if signature == hex_bytes[offset:len(signature)+offset].upper():
                ext = properties["format"]
                return ext
            else:
                ext = ["unknown"]

    return ext


def get_absolute_path(url, doc_url):
    """Create absolute url.

    Creates the full URL of the page that you want the link to
    by combining the protocol, domain name and location following the root domain.

    Parameters
    ------------
    url : str
        Protocol (https) and root domain parts of the absolute url.
    doc_url : str
        Location following the root domain.

    Returns
    ---------
    str
        Absolute url (entire address).

    Examples
    ----------
    The function returns an absolute url based on it's protocol+domain name
    and relative url.  An example of the components is shown below.

    Absolute URL:

        https://www.example.com/xyz.html

    Relative URL (i.e., this is the location following the domain):

        /xyz.html

    Domain name:

        www.example.com

    Protocol:

        https
    """

    return urljoin(url,doc_url)


def get_fnames(dpath):
    """Get list of file names.

    Given a directory path, return a dictionary of file names.
    The dictionary key-value structure is {file_name:[file_extension]}.
    The file extension can later be used to identify file type or format if
    needed.

    Parameters
    ------------
    dpath : str
        Directory path to be scanned for files.

    Returns
    ----------
    dict
        Dictionary with file names as keys and file extension as values.

    See Also
    ----------
    utilsx.readin.file_signature
    """

    fdict = {}

    # get list of full path and name of files in directory (subdirectories removed)
    files = [f.absolute().as_posix() for f in Path(dpath).glob("*") if f.is_file()]


    # use file signatures to get file format (if possible)
    # if extension is unknown use extension from file name
    # if multiple extensions returned, match to file name
    for file in files:
        ext = file_signature(file)

        if "." in file:
            fext = file.split(".")[-1]
        else:
            fext = None

        if ext[0] == "unknown":
            print(f"\nWarning: unknown signature for {file}")
            if fext:
                print("\t using file name's extension as file type\n")
                ext = [fext]
            else:
                print("\t no known extension available\n")
                ext = ["unknown"]

        elif len(ext) > 1:
            print(f"\nWarning: multiple possible format types for {file}")
            print("\t will try to select best option using file name's extension\n")
            if fext in ext:
                ext = [fext]
            else:
                print(f"\nWarning: could not match extension to list of options {file}")
                ext = ["unknown"]

        fdict[file] = ext

    return fdict


def most_recent(filedir):
    """Find most recent file in directory.

    Scan files in a directory and return the most recently
    modified file name.

    Parameters
    ------------
    filedir : str
        Full directory path to scan.

    Returns
    --------
    str
        Most recently modified file name.
    """
    file = max(glob.iglob(filedir),key=os.path.getmtime)
    return file


def read_yaml(params, abort=True):
    """Read a yaml file.

    Scan a yaml file for user specified data block and then
    read that data block and return contents to user.

    Parameters
    ------------
    params : list
        Two itemed list: (1) fully qualified path and name of yaml (2) data block header name.
    abort : bool
        True if program should exit upon error; False to continue running. (default is True).

    Returns
    ---------
    dict
        Data block read from yaml; stored as a dictionary.

    Notes
    ------
    **Error Handling Options**

    There are two options if an error is encountered during read.

    * abort = True: calling program will exit (run aborts)
    * abort = False: continues running but will return False instead of a data block.

    If abort = False is used, user can error check returned value by verifying if False.

    Examples
    ---------
    The function reads a yaml and extarcts a data block based on a user-supplied
    header name.  A sample yaml and example call are provided below.

    **yaml sample structure**

    MyHeader:
        | keyword1: <some value>
        | keyword2: <another value>
        | ...
        | ...
        | keywordn: <last value>

    MyHeader2:
        | keyword1: <some value>
        | keyword2: <another value>
        | ...
        | ...
        | keywordn: <last value>

    | ...
    | ...

    MyHeaderN:
        | keyword1: <some value>
        | keyword2: <another value>
        | ...
        | ...
        | keywordn: <last value>

    .. note:: Note: keyword values can be strings, lists, dictionarys, numeric, etc.

    Using the sample yaml above, you implement read_yaml as follows

    .. code-block:: python

        data_block = read_yaml(["Path/to/your/yaml.yml","MyHeader1"])

    This will return a dictionary with the key-value pairs from the MyHeader1
    data block.
    """

    # params list with yaml file name, header

    file_name = params[0]
    header = params[1]

    try:
        with open(file_name) as f:
            data = yaml.load(f, Loader=yaml.FullLoader)
        return data[header]
    except Exception as error:
        if abort:
            print("\nError in reading user supplied yaml")
            print(error)
            print("Exiting....")
            exit()
        else:
            return False


def scan_csv_list(url):
    """Scan list of files on GitHub.

    Given a GitHub repo url, scan the list of files
    and return urls for all CSV files found and the names
    of those files.

    Parameters
    -----------
    url : str
        GitHub repo url.

    Returns
    ----------
    urls : list
        List of urls ending in .csv.
    names : list
        List of .csv file names.

    See Also
    ---------
    utilsx.readin.check_last_load

    References
    ------------
    `Get list of CSVs from GitHub repo <https://stackoverflow.com/questions/60924860/python-get-list-of-csv-files-in-public-github-repository>`_
    """

    # Issue request: r => requests.models.Response
    r = requests.get(url)

    # Extract text: html_doc => str
    html_doc = r.text

    # Parse the HTML: soup => bs4.BeautifulSoup
    soup = BeautifulSoup(html_doc, 'html.parser')

    # Find all 'a' tags (which define hyperlinks): a_tags => bs4.element.ResultSet
    a_tags = soup.find_all('a')

    # Store a list of urls ending in .csv: urls => list
    urls = ['https://raw.githubusercontent.com'+re.sub('/blob', '', link.get('href'))
            for link in a_tags  if '.csv' in link.get('href')]

    # Store a list of file names
    list_names = [url.split('.csv')[0].split('/')[url.count('/')] for url in urls]

    return urls, list_names


def unicodify(seq, min_confidence=0.5):
    """Check encoding and covert to unicode.

    Take some raw data of unknown character encoding and ensure it is unicode
    before further processing.  Helps avoid codec decode errors.

    Parameters
    -----------
    seq : str
        Raw text of unknown encoding.
    min_confidence : float
        Confidence level [0-1] for determining encoding. (default = 0.5)

    Returns
    ----------
    str
        Raw data converted to Unicode.

    References
    ------------
    `Check encoding and convert to unicode <https://stackoverflow.com/questions/14856872/check-encoding-and-convert-to-unicode>`_
    """

    guess = chardet.detect(seq)
    if guess["confidence"] < min_confidence:
        # chardet isn't confident enough in its guess, so:
        raise UnicodeDecodeError

    return seq.decode(guess["encoding"])
