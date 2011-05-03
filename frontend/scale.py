#!/usr/bin/python
import serial
import random
import pygtk
pygtk.require('2.0')
import gtk
import multiprocessing
import Queue # for Queue.Empty Exception
import time
import gobject

import subprocess, shlex # for "forking socat"

SOCAT_EXECUTABLE = '/usr/bin/socat'
SOCAT_ARGS = '-d -d -u pty,raw,echo=0 pty,raw,echo=0'

# user random.uniform(0,10) for generating a random float

class ScaleProcess(multiprocessing.Process):
    def __init__(self, output_format=None, *args, **kwargs):
        super(ScaleProcess, self).__init__(None, args, kwargs)
        if 'port' in kwargs:
            self.serial_port = serial.Serial(kwargs['port'])
        else:
            self.serial_port = serial.Serial()
        if 'queue' not in kwargs:
            raise Exception('A multiprocessing.Queue is necessary')
        self.queue = kwargs['queue']
        if output_format==None:
            self.output_format = 'ST,GS, {:f}KG,'
        else:
            self.output_format = output_format

    def run(self):
        weight = '0'
        while self.is_alive():
            try:
                time.sleep(0.01)
                item = self.queue.get(False) # don't block if there's no item
                weight = item
            except Queue.Empty:
                pass
            self.serial_port.write(self.line(weight))

    def line(self, weight):
        """
        Returns the 'line' as given by a scale.
        """
        try:
            return (self.output_format+'\n').format(float(weight))
        except:
            pass

class Scale(gtk.Window):
    def __init__(self, *args, **kwargs):
        command = SOCAT_EXECUTABLE + ' ' + SOCAT_ARGS
        self.socat_process = subprocess.Popen(shlex.split(command),
                                              shell=False,
                                              stderr=subprocess.PIPE)
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
            device_for_reads)
        )
        self.queue = multiprocessing.Queue()
        self.scale_process = ScaleProcess(port = device_for_writes,
                                          queue = self.queue)
        self.scale_process.start()

        # GTK related stuff
        super(Scale, self).__init__()
        self.set_title("Scale simulator")
        self.connect("delete_event", self.delete_event)
        self.connect("destroy", self.destroy)

        self.main_container = gtk.HBox()
        self.main_container.set_size_request(800, 40)
        #self.weight_input = gtk.Entry(max=10)
        #self.weight_input.connect('activate', self.set_weight_cb)
        adj = gtk.Adjustment(0.0,  # initial value
                             0.0,  # lower bound
                             10.0, # upper bound
                             0.001, # step increment
                             0,    # page increment
                             0)    # page size
        adj.connect('value_changed', self.slider_change)
        self.slider = gtk.HScale(adj)
        self.slider.set_size_request(700, 20)
        self.slider.set_update_policy(gtk.UPDATE_CONTINUOUS)
        self.slider.set_digits(3)
        self.slider.set_value_pos(gtk.POS_TOP)
        self.slider.set_draw_value(True)
        self.display = gtk.Label()
        self.display.set_size_request(100,20)
        #self.main_container.add(self.weight_input)
        self.main_container.add(self.slider)
        self.main_container.add(self.display)
        self.add(self.main_container)

        self.show_all()

    def delete_event(self, widget, event, data=None):
        return False

    def destroy(self, widget, data=None):
        self.scale_process.terminate()
        self.scale_process.serial_port.close() # close serial port
        self.socat_process.terminate()
        gtk.main_quit()

    def update_display(self, weight):
        """
        Simply updates the display Label widget to the current weight.
        """
        self.slider.set_value(float(weight))
        #self.weight_input.text = weight
        self.display.set_markup("{0} Kg".format(weight))

    def slider_change(self, slider):
        """
        Puts the current value of self.slider into self.queue.
        """
        weight = str(slider.get_value())
        try:
            self.queue.put(weight, False, 0.1) # wait only 0.1s
        except Queue.Full:
            pass
        self.update_display(weight)

    def set_weight_cb(self, entry):
        """
        Puts the current value of self.weight_input into self.queue.
        """
        weight = entry.get_text()
        try:
            self.queue.put(weight, False, 0.1) # wait only 0.1s
        except Queue.Full:
            pass
        self.update_display(weight)

def remove_box(self, button):
    """
    Simulates the removal of a box.

    At the moment it is a simple linear function, but we can
    easily incorporate something more sophisticated.
    """
    while self.weight>0:
        self.weight = self.weight - 0.05
        self.update_display()
    self.weight = 0.0


def extract_device_from_line(line):
    """
    Given a line with the format '..... some_device' returns
    the string 'some_device'.
    """
    return line[line.rfind(' ')+1:-1]

if __name__=='__main__':
    scale = Scale()
    gtk.main()
