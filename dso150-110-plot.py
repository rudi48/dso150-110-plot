#! /usr/bin/env python3
"""
# DSO150-110-plot.py - capture DSO150 data and plot
# 2017-11-27 Rudolf Reuter, version 1.0, Python 2/3
# 2017-11-05 Rudolf Reuter, version 1.1
# waveform data are just time resolution (s) and 12 bit data (1024)
# firmware 110 and newer
#
# This software is public domain.
"""
from __future__ import print_function # make "print" Python 2/3 compatible
import glob
import locale
import optparse
import os
import platform
import serial
from subprocess import call
import sys
import time

# make the program universal for Python 2 and 3
from sys import version_info
python2 = False
if version_info.major == 2:
    python2 = True

# on which port should the tests be performed
# http://sourceforge.net/projects/osx-pl2303/

# for USB port use, adopt to your hardware
port = ""
os_name = platform.system()
if os_name == "Windows":
    port = "COM3:"
if os_name == "Linux":
    port = "/dev/ttyUSB0"
if os_name == "Darwin": # Mac OS X
    #port = "/dev/cu.usbserial-A4009RFD"
    #port = "/dev/cu.PL2303-0000103D"
    #port = "/dev/cu.wchusbserial14a120"  # CH340
    port = "/dev/cu.SLAB_USBtoUART"  # CP2102
# for debug only, command line argument
#sys.argv = ['dso150_p23.py', '-p']


parser = optparse.OptionParser(
    usage = "%prog [options] [port [baudrate]] version 1.1", 
    description = "DSO150_p23.py - capture DSO150 data."
)
parser.add_option("-d", "--data", dest="data", action="store_true",
                  help="data plot")
parser.add_option("-f", "--file", dest="filename",
                  help="Enter filename")
parser.add_option("-g", "--gport", dest="gport",
                  help="serial port, e.g. /dev/cu.xxx")
parser.add_option("-p", "--print", dest="printWS", action="store_true",
                  help="print waveform screen")
#parser.add_option("-q", "--quiet",
#                  action="store_false", dest="verbose", default=True,
#                  help="don't print status messages to stdout")
parser.add_option("-t", "--timeout", dest="timeout",
                    help="Enter timeout in sec.")
parser.add_option("-v", "--verbose", action="store_true", dest="verbose",
                  help="tell more internal values for debugging")

(options, args) = parser.parse_args()

if (len(sys.argv) < 2):  # no arguments given
    parser.print_help()
    print("Default Serial Port: " + port)

if options.printWS:
    # open USB-serial port, if waveform transfer is needed
    if options.gport:
        port = options.gport
    otimeout = 1              # 1 sec
    if options.timeout:
        otimeout = int(options.timeout)
    try:
        ser = serial.Serial(port, baudrate=115200, timeout=otimeout)
        if options.verbose:
            print(ser.name)
        ser.flushInput()
        #time.sleep(2)  # skip Arduino DTR toogle RESET
    except:
        sys.stderr.write("could not open port %r\n" % (port))
        if os_name == "Darwin": # Mac OS X
            print ("Found ports:")
            for name in glob.glob('/dev/cu.*'): # show available ports
                print("  "+name)
        if os_name == "Linux":
            for name in glob.glob('/dev/ttyUSB*'): # show available ports
                print("  "+name)
        sys.exit(1)
        
    
if options.printWS:  # Python 2/3 OK
    # find out decimal point character
    locale.setlocale(locale.LC_ALL, '')
    conv = locale.localeconv()
    dp =  conv["decimal_point"]
    #print(dp)
    print ("Push DSO150 ADJ + V/DIV.")
    
    # wait for data
    nwait = 60 # 60 seconds
    ncount = 1
    dsoHeader =[]  # 19 lines
    dsoData = []   # 1024 lines
    
    while (nwait > 0):
        sdat = ser.readline()  # includes CR + LF
        if len(sdat) < 1:
            nwait -= 1
            print (nwait)
        else:
            if ncount < 20:
                # convert byte array to string
                dsoHeader.append(sdat.decode("utf-8"))
                ncount += 1
            else:
                ncount += 1
                dsoData.append(sdat.decode("utf-8"))
                for i in range(0,1024,1):
                    sdat = ser.readline()
                    dsoData.append(sdat.decode("utf-8"))
                break
            #sys.exit(0)
    if nwait < 1:
        sys.exit(0)
        
    # produce csv file
    fname = "dso150-110-data.csv"
    if options.filename:
        fname = options.filename
    if options.verbose:
        print("DSO150 csv file: " + fname)
    f = open(fname, "w")
    now = time.strftime('%Y-%m-%d %H:%M:%S')
    if options.verbose:
        print(now)
        
    # write Header to file
    title = "File: " + fname + " " + now + "\n"
    f.write(title)
    for i in range(0,19,1):
        datLine = dsoHeader[i]
        f.write(datLine)
        
    # calculate Sample Interval
    timeFactor = {"s":1, "ms":1000, "us":1000000, "ns":1000000000}
    sdat = dsoHeader[18]
    cpos = sdat.find(",")
    tNum = int(sdat[cpos+1:cpos+6])
    tUnit = sdat[cpos+6:]
    tUnit = tUnit.rstrip('\r\n')
    if tUnit in timeFactor:
        tFactor = timeFactor[tUnit]
        sampleIntvl = tNum / tFactor
    else:
        print("Error time unit " + tUnit)
        sys.exit(1)
    
    for i in range(0,1024,1):
        datLine1 = str(dsoData[i])
        # process Sample Interval
        datLine2 = "{:.8f}".format(i * sampleIntvl) + "," + datLine1[17:]
        f.write(datLine2)
    f.close()
    

def getMeasure():  # read measurements
    datax = []

    
if options.data:  # Python 2/3 OK
    # write gnuplot parameter file, and call gnuplot
    # Set date and time
    if options.filename:
        fname = options.filename
    if options.verbose:
        print("DSO150 csv file: " + fname)
    now = time.strftime('%Y-%m-%d %H:%M:%S')
    if options.verbose:
        print(now)
    # create parameter file for gnuplot
    fnamePar = "dso150_gnuplot.par"
    f = open(fnamePar, "w")
    # default x-size = 672 pixel, use better 1200 x 675 ratio: 16:9
    if os_name == "Darwin":
        f.write('set terminal qt size 1200,675 font "Helvetica,14"'  + "\n")
    if os_name == "Linux":
        f.write('set terminal qt size 1200,675 font "Helvetica,12"'  + "\n") 
    if os_name == "Windows":
        f.write('set terminal qt size 1200,675'  + "\n") # ratio: 16:9 
    f.write('set datafile separator ","' + "\n")
    # get data title
    fd = open(fname)
    datTitle = fd.readline().rstrip('\r\n')
    f.write('set title ' + '"' + datTitle + '"' + '\n')
    f.write('set xlabel "Time (s)"' + "\n")
    f.write('set ylabel "Volt"' + "\n")
    f.write('set grid'  + "\n")
    
    # Label for measurements
    mLabel = []
    for i in range(1,19,1):
        mLabel.append(fd.readline().replace(",",":").rstrip('\r\n'))
    f.write('set label 1 at graph 0, 1.015 "' + mLabel[14] + '"\n')
    f.write('set label 2 at graph 0.1, 1.015 "' + mLabel[15] + '"\n')
    f.write('set label 3 at graph 0.19, 1.015 "' + mLabel[16] + '"\n')
    f.write('set label 4 at graph 0.28, 1.015 "' + mLabel[17] + '"\n')
    f.write('set label 5 at graph 0.63, 1.015 "' + mLabel[9] + '"\n')
    f.write('set label 6 at graph 0.71, 1.015 "' + mLabel[10] + '"\n')
    f.write('set label 7 at graph 0.79, 1.015 "' + mLabel[11] + '"\n')
    f.write('set label 8 at graph 0.87, 1.015 "' + mLabel[12] + '"\n')
    f.write('set label 9 at graph 0.94, 1.015 "' + mLabel[13] + '"\n')
    f.write('set label 10 at graph 0.0, -0.06 "' + mLabel[0] + '"\n')
    f.write('set label 11 at graph 0.1, -0.055 "' + mLabel[1] + '"\n')
    f.write('set label 12 at graph 0.2, -0.055 "' + mLabel[2] + '"\n')
    f.write('set label 13 at graph 0.3, -0.055 "' + mLabel[3] + '"\n')
    f.write('set label 14 at graph 0.6, -0.055 "' + mLabel[5] + '"\n')
    f.write('set label 15 at graph 0.73, -0.055 "' + mLabel[6] + '"\n')
    f.write('set label 16 at graph 0.88, -0.055 "' + mLabel[7] + '"\n')
    fd.close()
        
    # every ::21 skips first 20 lines
    f.write('plot "' + fname + '" every ::21  with lines' + "\n")
    f.write('pause -1 "Select terminal window, hit RETURN to continue "'  + "\n")
    f.close()
    print("Call GNUPlot")
    status = call(['gnuplot', 'dso150_gnuplot.par'])

if options.printWS:
    ser.close()
