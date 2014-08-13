======================================================
SkewT -- Atmospheric Profile Plotting and Diagnostics
======================================================

SkewT provides a few useful tools to help with the plotting and analysis of 
upper atmosphere data. In particular it provides some useful classes to 
handle the awkward skew-x projection (provided by Ryan May, see notes in 
source code and LICENSE.txt).

It's most basic implementation is to read a text file of the format provided 
by the University of Wyoming's website: 

http://weather.uwyo.edu/upperair/sounding.html

Typical usage often looks like this::

    #!/usr/bin/env python

    from skewt import SkewT
    sounding = SkewT.Sounding(filename="soundingdata.txt")
    sounding.plot_skewt(color='r',lw=2)

Alternatively you may input the required data fields in a dictionary. The 
dictionary must have as a minimum the fields PRES and TEMP corresponding to 
pressure (hPa) and temperature (deg C). Soundings will typically have a dew 
point temperature trace and wind barbs as well, so it's best to include the 
dewpoint temp DWPT (deg C), wind speed SKNT (knots) and wind direction in 
degrees WDIR. Other fields may be included as per the docstring::

    #!/usr/bin/env python

    from skewt import SkewT
    sounding = SkewT.Sounding(data=data_dict)
    sounding.plot_skewt(color='r',lw=2)

One thing on my to-do list is to make the package a bit more user-friendly 
in that it will accept one of a number of moisture fields (e.g. dew-point 
temperature relative humidity, mixing ratio or vapour partial pressure) and 
fill in the others for you. For any moisture calculations, the module looks 
for DWPT, and if it's not there it complains.

News
====
Thanks for your interest in this package and I'd love to hear your feedback: 
thomas.chubb AT monash.edu

Here's a summary of what's new in Version 0.1.4:

* (Version 0.1.4r2) Bug fix in readfile. A long time ago I decided to ignore 
  the diagnostics at the end of the University of Wyoming sounding files by 
  chopping the last 34 lines from the file, so when a file containing only 
  the raw data was used, it was truncated half-way up. This has been 
  replaced by a routine that checks for valid pressure data in the right 
  place.

* A major-ish change to the layout. I'm planning on adding more diagnostics 
  as time goes by so I decided to get the test from the parcel and the 
  column diagnostics out of the plot area.

* The new release contains a diagnostic for Total Precipitable Water (TPW). 
  This is simply the total column-integrated water vapour, based on mixing 
  ratio derived from DWPT. It uses a trapezoidal approximation for 
  integration and gives values within about one percent of the values in the 
  UWyo text files (I have no idea how UWyo do their diagnostic). More 
  diagnostics to come!


Regarding the Examples in the Tarball
=====================================
Unfortunately, If you pip install this package I don't think you get the 
examples that are in the tarball (see the big green "Downloads" button?). In 
any case using the __main__ invocation (i.e. python SkewT.py) doesn't really 
make sense when you have SkewT.py installed in a system directory. The very 
easiest way to run the examples would be as per the typical usage above 
(e.g. in IPython) after having downloaded one of the example sounding files 
and placed it in you current directory. 

Alternatively, I have uploaded them as a separate file with a short script 
to run and show the output. Look for skewt_examples.tar.gz under 
"Downloads".


Sounding Files
==============
The format for the sounding files is very specific (sorry). You are best off 
using the example in "examples" as a template. Here's a sample of the first 
few lines::

    94975 YMHB Hobart Airport Observations at 00Z 02 Jul 2013

    -----------------------------------------------------------------------------
       PRES   HGHT   TEMP   DWPT   RELH   MIXR   DRCT   SKNT   THTA   THTE   THTV
	hPa     m      C      C      %    g/kg    deg   knot     K      K      K 
    -----------------------------------------------------------------------------
     1004.0     27   12.0   10.2     89   7.84    330     14  284.8  306.7  286.2
     1000.0     56   12.4   10.3     87   7.92    325     16  285.6  307.8  286.9
      993.0    115   12.8    9.7     81   7.66    311     22  286.5  308.1  287.9

The script defines columns by character number so you really do have to get 
the format *exactly* right. One day I will get around to writing a routine 
to output the text files properly.

Parcel Ascent
=============
Simple routine to calculate the characteristics of a parcel initialised with 
pressure, temperature and dew point temperature. You could do it like this::

    from skewt import SkewT

    sounding=SkewT.Sounding("examples/94975.2013070200.txt")
    sounding.make_skewt_axes()
    sounding.add_profile(color='r',lw=2)
    sounding.lift_parcel(1004.,17.4,8.6)
    draw()

Automatic Parcel Definition
--------------------------- 
You can still manually input a parcel as in the example above, but there is 
a new routine to automagically define a parcel from the sounding itself. You 
define a layer depth that you would like to characterise (say 100mb). The 
routine surface_parcel then returns

1. The surface pressure (just the pressure of the lowest level)
2. The characteristic dew-point temperature (from the average Qv in the layer)
3. The characteristic temperature (from the maximum Theta in the layer)

You could do it like this::

    from skewt import SkewT

    sounding=SkewT.Sounding("examples/94975.2013070200.txt")
    sounding.make_skewt_axes()
    sounding.add_profile(color='r',lw=2)
    parcel=sounding.surface_parcel(mixheight=100.)
    sounding.lift_parcel(*parcel)
    draw()

The above steps are also now included in the Sounding.plot_skewt() wrapper 
for your convenience, so all of the above can be condensed with::

    from skewt import SkewT

    sounding=SkewT.Sounding("examples/94975.2013070200.txt")
    sounding.plot_skewt(color='r',lw=2)


To-Do List
==========
* More diagnostics.

* The Sounding.readfile() routine is much smarter now.

* User-friendly moisture variable handling. At the moment it's best to just 
  make sure that you include DWPT.

* Hodographs? Anyone? 

Contributors
==============
* Simon Caine.

* Hamish Ramsay (Monash) has promised to at least think about adding some 
  extra diagnostics.

* The initial SkewX classes were provided by a fellow called Ryan May who 
  was a student at OU. I have not made contact with Ryan other than to 
  download his scripts and modify them for my own purposes.

Thanks Also
===========
* Thanks to Douglas Miller of UNC-Asheviller, who prompted me to get the TPW 
  routine up for a class exercise (yay!), and is checking for more bugs.



