Processing data
===============

``process_magnetograms.py`` contains code to trace field lines through sets of PFSS solutions.
At the top of this file you will need to fill in the directory you have downloaded magnetograms to
(``magnetogram_dir``) and the directory you would like to output the results to (``output_dir``).

Running ``python process_magnetograms.py [source]``, where ``[source]`` is one of
``['gong', 'kpvt', 'solis', 'mdi']`` will process all the magnetograms from that source.
This will take a little while, but not too long; it takes about half a day to get through
all of the sources on my 7-year old MacBook Pro.
