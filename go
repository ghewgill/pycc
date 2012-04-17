#!/bin/sh

python3 testas.py && rm -f *.o && make && (cd ../applepy && python2.6 applepy.py -q --rom ../applepy/APPLE.ROM --ram ../pycc/life.ram --pc 2048)
