#!/usr/bin/python
"""
Copyright (C) 2010 Simon Dawson, Meryl Baquiran, Chris Ellis
and Daniel Kenji Toyama 
Copyright (C) 2011 Simon Dawson, Daniel Kenji Toyama

This file is part of Gleba 

Gleba is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Gleba is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Gleba.  If not, see <http://www.gnu.org/licenses/>.

Path: 
    frontend.scale

Purpose:
    Scale simulator.
    It writes a chosen weight to a serial port, just like a normal scale.
"""
import serial
from gi.repository import Gtk
import multiprocessing
import Queue # for Queue.Empty Exception
import subprocess, shlex # for "forking socat"

SOCAT_EXECUTABLE = '/usr/bin/socat'
SOCAT_ARGS = '-d -d -u pty,raw,echo=0 pty,raw,echo=0'
CYCLE_TIME = 0.2

class ScaleProcess(multiprocessing.Process):
    def __init__(self, output_format = None, *args, **kwargs):
        super(ScaleProcess, self).__init__(None, args, kwargs)
        if 'port' in kwargs:
            self.serial_port = serial.Serial(kwargs['port'])
        else:
            self.serial_port = serial.Serial()
        if 'queue' not in kwargs:
            raise Exception('A multiprocessing.Queue is necessary')
        self.queue = kwargs['queue']
        if output_format == None:
            self.output_format = 'ST,GS, {:f}KG,'
        else:
            self.output_format = output_format

    def run(self):
        weight = '0.000'
        while self.is_alive():
            try:
                weight = self.queue.get(True, CYCLE_TIME)
            except Queue.Empty:
                pass
            self.serial_port.write(self.line(weight))

    def line(self, weight):
        """
        Returns the 'line' as given by a scale.
        """
        return (self.output_format + '\n').format(float(weight))

def extract_device_from_line(line):
    """
    Given a line with format '..... some_device' returns
    the string 'some_device'.
    """
    return line[line.rfind(' ') + 1 : -1]

class Scale(Gtk.Window):
    def __init__(self, *args, **kwargs):
        command = SOCAT_EXECUTABLE + ' ' + SOCAT_ARGS
        self.socat_process = subprocess.Popen(shlex.split(command),
                                              shell = False,
                                              stderr = subprocess.PIPE)
        # first line of socat output (writing end of the connection)
        socat_error = self.socat_process.stderr.readline()
        device_for_writes = extract_device_from_line(socat_error)
        # second line of socat output (reading end of the connection)
        socat_error = self.socat_process.stderr.readline()
        device_for_reads = extract_device_from_line(socat_error)
        # consume last line (some extra info)
        socat_error = self.socat_process.stderr.readline()
        print ('Writing to {0} port. You can read from {1}'.format(
            device_for_writes,
            device_for_reads
        ))
        self.queue = multiprocessing.Queue(1)
        self.scale_process = ScaleProcess(port = device_for_writes,
                                          queue = self.queue)
        self.scale_process.start()
        # GTK related stuff
        super(Scale, self).__init__()
        self.set_title("Scale simulator")
        self.connect("delete_event", self.delete_event)
        self.connect("destroy", self.destroy)
        self.main_container = Gtk.HBox()
        self.main_container.set_size_request(800, 40)
        adj = Gtk.Adjustment(0.0,   # initial value
                             0.0,   # lower bound
                             10.0,  # upper bound
                             0.001, # step increment
                             0,     # page increment
                             0)     # page size
        adj.connect('value_changed', self.slider_change)
        self.slider = Gtk.HScale.new(adj)
        self.slider.set_size_request(700, 20)
        self.slider.set_digits(3)
        self.slider.set_value_pos(Gtk.PositionType.TOP)
        self.slider.set_draw_value(True)
        self.main_container.add(self.slider)
        self.add(self.main_container)
        self.show_all()

    def delete_event(self, widget, event, data = None):
        return False

    def destroy(self, widget, data = None):
        self.scale_process.terminate()
        self.scale_process.serial_port.close() # close serial port
        self.socat_process.terminate()
        Gtk.main_quit()

    def slider_change(self, slider):
        """
        Puts the current value of self.slider into self.queue.
        """
        weight = str(slider.get_value())
        try:
            self.queue.put(weight, True, CYCLE_TIME)
            print '' # bug in Python? See commit notes
        except Queue.Full:
            pass

if __name__ == '__main__':
    scale = Scale()
    Gtk.main()
