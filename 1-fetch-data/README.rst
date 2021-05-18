Fetching data
=============

``get_data.py`` contains individual functions for download synoptic maps from each
data source. At the top of this file you will need to fill in the directory you
want to download the data to (``local_dir``) and your JSOC username (``jsoc_user``).

Running ``python get_data.py`` will automatically run each of the four download
functions in sequence, downloading all the data. Note that this will take a while!
