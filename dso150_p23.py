#! /usr/bin/env python3
"""
# DSO150_p23.py - capture DSO150 data
# 2017-10-06 Rudolf Reuter, version 1.0, Python 2/3
# waveform data are just time resolution (s) and 12 bit data (1024)
# firmware must have toshi extension 60B
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
    usage = "%prog [options] [port [baudrate]] version 1.0", 
    description = "DSO150_p23.py - capture DSO150 data."
)
parser.add_option("-d", "--date", dest="date", action="store_true",
                  help="set date and plot")
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

# open USB-serial port
if options.gport:
    port = options.gport
otimeout = 1              # 1 sec
if options.timeout:
    otimeout = int(options.timeout)
try:
    ser = serial.Serial(port, baudrate=38400, timeout=otimeout)
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
    print ("Push the DSO150 encoder button.")
    
    fname = "dso150-data.csv"
    if options.filename:
        fname = options.filename
    if options.verbose:
        print("DSO150 csv file: " + fname)
    
    # wait for data
    nwait = 60 # 60 seconds
    ncount = 1
    dsoData = []
    while (nwait > 0):
        sdat = ser.readline()
        if len(sdat) < 1:
            nwait -= 1
            print (nwait)
        else:
            if ncount == 1:
                timeRes = float(sdat)
                ncount += 1
                #print(timeRes)
            else:
                ncount += 1
                for i in range(1,1024,1):
                    sdat = ser.readline()
                    dsoData.append(float(sdat))
                break
            #sys.exit(0)
    if nwait < 1:
        sys.exit(0)
        
    # produce csv file
    f = open(fname, "w")
    dsoTime = timeRes
    datLine = str(dsoData[0]) + ";" + "0.0" + "\n"
    datLine = datLine.replace(".", dp)
    f.write(datLine)
    for i in range(1,1023,1):
        datLine = str(dsoData[i]) + ";" + "{:.8f}".format(dsoTime) + "\n"
        datLine = datLine.replace(".", dp)
        f.write(datLine)
        dsoTime += timeRes
    f.close()
    
if options.date:  # Python 2/3 OK
    # write gnuplot parameter file, and call gnuplot
    # Set date and time
    now = time.strftime('%Y-%m-%d %H:%M:%S')
    if options.verbose:
        print(now)
    # create parameter file for gnuplot
    fname = "dso150_gnuplot.par"
    f = open(fname, "w")
    # default x-size = 672 pixel, use better 1200 x 675 ratio: 16:9
    if os_name == "Darwin":
        f.write('set terminal qt size 1200,675 font "Helvetica,14"'  + "\n")
    if os_name == "Linux":
        f.write('set terminal qt size 1200,675 font "Helvetica,12"'  + "\n") 
    else:
        f.write('set terminal qt size 1200,675'  + "\n") # ratio: 16:9 
    f.write('set datafile separator ";"' + "\n")
    if os_name == "Windows":
        f.write('set decimalsign locale "German_Germany.1252"' + "\n")
    else:
        f.write('set decimalsign locale "de_DE.UTF-8"' + "\n")
    f.write('set title "File: dso150-data.csv ' + now + '"' + "\n")
    f.write('set xlabel "Time (s)"' + "\n")
    f.write('set ylabel "Volt"' + "\n")
    f.write('set grid'  + "\n")
    # "using 2:1" swaps the columns
    f.write('plot "dso150-data.csv" using 2:1 with lines' + "\n")
    f.write('pause -1 "Select terminal window, hit RETURN to continue "'  + "\n")
    f.close()
    status = call(['gnuplot', 'dso150_gnuplot.par'])

ser.close()
