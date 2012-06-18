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
    frontend.gui

Purpose:
    Main interface to weigh boxes in Gleba.
"""
import time
import sys
from threading import Thread
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Gst
from gi.repository import GObject
import utils
import config

AWAITING_BATCH = 0
AWAITING_BOX = 1
AWAITING_PICKER = 2
AWAITING_VARIETY = 3
OVERWEIGHT_ADJUST = 4
UNDERWEIGHT_ADJUST = 5
AWAITING_CONFIRMATION = 6
REMOVE_BOX = 7
STATUS_MESSAGES = [
    'Awaiting batch',
    'Awaiting box',
    'Awaiting picker',
    'Awaiting variety',
    'Overweight, Adjust',
    'Underweight, Adjust',
    'Awaiting confirmation',
    'Remove box'
]

class DataModel:
    """
    Represents the model in the MVC paradigm.
    """
    def __init__(self):
        self.db_conn = utils.DBAPI()
        self.batches   = self.db_conn.get_active_batches_list()
        self.pickers   = self.db_conn.get_active_pickers_list()
        self.varieties = self.db_conn.get_active_varieties_list()
        self.inverted_index_picker = {}
        self.inverted_index_batch = {}
        self.inverted_index_variety = {}
        for i in range(len(self.pickers)):
            self.inverted_index_picker[int(self.pickers[i]['id'])] = i
        for i in range(len(self.batches)):
            self.inverted_index_batch[int(self.batches[i]['id'])] = i
        for i in range(len(self.varieties)):
            self.inverted_index_variety[int(self.varieties[i]['id'])] = i

    def batch_date_str(self, batch_id):
        """
        Returns a string representing the date of the batch batch_idx.
        """
        batch = self.batch(batch_id)
        return "{year}-{month}-{day}".format(
            year = batch['date']['year'],
            month = batch['date']['month'],
            day = batch['date']['day']
        )

    def picker(self, picker_id):
        """
        Returns the picker with picker_id as a dictionary.
        """
        return self.pickers[self.inverted_index_picker[picker_id]]

    def batch(self, batch_id):
        """
        Returns the batch with batch_id as a dictionary.
        """
        return self.batches[self.inverted_index_batch[batch_id]]

    def variety(self, variety_id):
        """
        Returns the variety with variety_id as a dictionary.
        """
        return self.varieties[self.inverted_index_variety[variety_id]]

class MainWindow:
    current_picker = None
    current_batch = None
    current_variety = None
    current_state = AWAITING_BATCH
    current_weight = 0
    current_picker_weight = 0
    show_weight = False
    min_weight = 0.0
    weight_window = [0.0 for i in range(config.args.weight_window_size)]
    weight_color = config.WHITE_COLOR

    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file('gui.ui')
        self.window = self.builder.get_object('window')
        self.window.set_default_size(config.args.window_width,
                                     config.args.window_height)
        self.builder.connect_signals(self)
        self.data_model = DataModel()
        self.gui_init()
        # sound stuff
        self.player = Gst.ElementFactory.make('playbin2', 'player')
        # Thread to read from scale (producer)
        self.serial_thread = utils.ThreadSerial()
        self.serial_thread.daemon = True
        self.serial_thread.start()
        # Thread to process stuff (consumer)
        self.keep_running = True
        self.reading_thread = Thread(target = self.consumer_thread)
        self.reading_thread.start()
        self.set_status_feedback()

    def gui_init(self):
        """
        Some additional behavioural initializations in the GUI.
        """
        # add batches
        batch_combo_box = self.builder.get_object('batch_combo_box')
        for batch in self.data_model.batches:
            batch_combo_box.append_text(config.BATCH_COMBO_FORMAT.format(
                batch_id = batch['id'],
                year = batch['date']['year'],
                month = batch['date']['month'],
                day = batch['date']['day'],
                room_number = batch['room_number']
            ))
        # add pickers
        picker_total = len(self.data_model.pickers)
        cols = config.PICKER_COLS
        rows = picker_total/cols + int(picker_total%cols != 0)
        picker_vbox = self.builder.get_object('picker_vbox')
        for row in range(0, rows):
            hbox = Gtk.HBox()
            for col in range(0, cols):
                idx = cols*row + col
                if idx >= picker_total:
                    break
                picker = self.data_model.pickers[idx]
                button = Gtk.Button(label = config.PICKER_BUTTON_FORMAT.format(
                    picker_id = picker['id'],
                    first_name = picker['first_name'],
                    last_name = picker['last_name']
                ))
                button.connect('clicked', self.select_picker_callback, idx)
                hbox.add(button)
            picker_vbox.add(hbox)
        # add varieties
        variety_total = len(self.data_model.varieties)
        cols = config.VARIETY_COLS
        rows = variety_total/cols + int(variety_total%cols != 0)
        variety_vbox = self.builder.get_object('variety_vbox')
        for row in range(0, rows):
            hbox = Gtk.HBox()
            for col in range(0, cols):
                idx = cols*row + col
                if idx >= variety_total:
                    break
                variety = self.data_model.varieties[idx]
                button = Gtk.Button(label = config.VARIETY_BUTTON_FORMAT.format(
                    variety_name = variety['name'],
                    min_weight = variety['minimum_weight'],
                    max_weight = variety['minimum_weight'] + variety['tolerance']
                ))
                button.connect('clicked', self.select_variety_callback, idx)
                hbox.add(button)
            variety_vbox.add(hbox)
        # edit window stuff
        combo_box = self.builder.get_object('edit_batch_combo')
        for batch in self.data_model.batches:
            combo_box.append_text(config.BATCH_COMBO_FORMAT.format(
                    batch_id = batch['id'],
                    year = batch['date']['year'],
                    month = batch['date']['month'],
                    day = batch['date']['day'],
                    room_number = batch['room_number']
            ))
        combo_box = self.builder.get_object('edit_picker_combo')
        for picker in self.data_model.pickers:
            combo_box.append_text(config.PICKER_BUTTON_FORMAT.format(
                picker_id = picker['id'],
                first_name = picker['first_name'],
                last_name = picker['last_name']
            ))
        combo_box = self.builder.get_object('edit_variety_combo')
        for variety in self.data_model.varieties:
            combo_box.append_text(config.VARIETY_BUTTON_FORMAT.format(
                variety_name = variety['name'],
                min_weight = variety['minimum_weight'],
                max_weight = variety['minimum_weight'] + variety['tolerance'],
            ))
        # add mappings for treeview columns
        for i in range(11):
            tvc = self.builder.get_object('hist_col' + str(i))
            cell_rend = self.builder.get_object('hist_cell' + str(i))
            tvc.add_attribute(cell_rend, "text", i)
        # Adjust sizes of various widgets
        self.builder.get_object('main_vbox').set_child_packing(
            self.builder.get_object('top_hbox'),
            False, False, 0, Gtk.PackType.START
        )
        self.builder.get_object('top_hbox').set_child_packing(
            self.builder.get_object('status_label'),
            False, False, 0, Gtk.PackType.START
        )
        self.builder.get_object('top_hbox').set_child_packing(
            self.builder.get_object('edit_button_hbox'),
            False, False, 0, Gtk.PackType.START
        )

    def exit_callback(self, widget, data = None):
        self.keep_running = False
        self.serial_thread.kill()
        del self.data_model # explicitly destroy data_model
        Gtk.main_quit()

    def exit_edit_window(self, widget):
        """
        Hides the edit window.
        """
        self.builder.get_object('edit_window').hide()

    def commit_callback(self, widget, data = None):
        """
        This callback is fired when the user presses the commit button.

        After this callback, the data in the history is sent to the server and
        committed to the database.
        """
        self.start_stop('button')
        boxes = []
        history_store = self.builder.get_object('history_store')
        for row in history_store:
            boxes.append({
                'picker':         row[0],
                'batch':          row[3],
                'variety':        row[6],
                'initial_weight': row[8],
                'final_weight':   row[9],
                'timestamp':      row[10]
            })
        self.data_model.db_conn.add_boxes(boxes)
        # clear the history
        history_store.clear()

    def edit_history_callback(self, button):
        """
        This callback is fired when an entry in the history list has been
        edited in the edit window.
        """
        self.start_stop('button')
        history_list = self.builder.get_object('history_list')
        model, iterator = history_list.get_selection().get_selected()
        picker_combo_box = self.builder.get_object('edit_picker_combo')
        batch_combo_box = self.builder.get_object('edit_batch_combo')
        variety_combo_box = self.builder.get_object('edit_variety_combo')
        selected_picker = self.data_model.pickers[picker_combo_box.get_active()]
        selected_batch = self.data_model.batches[batch_combo_box.get_active()]
        selected_variety = self.data_model.varieties[variety_combo_box.get_active()]
        model.set_value(iterator, 0,  selected_picker['id'])
        model.set_value(iterator, 1,  selected_picker['first_name'])
        model.set_value(iterator, 2,  selected_picker['last_name'])
        model.set_value(iterator, 3,  selected_batch['id'])
        model.set_value(iterator, 4,  self.data_model.
            batch_date_str(selected_batch['id'])
        )
        model.set_value(iterator, 5,  selected_batch['room_number'])
        model.set_value(iterator, 6,  selected_variety['id'])
        model.set_value(iterator, 7,  selected_variety['name'])
        model.set_value(iterator, 10, time.strftime('%Y-%m-%d %H:%M:%S',
                                      time.localtime() ))
        self.builder.get_object('edit_window').hide()

    def delete_history_callback(self, button):
        """
        Callback that gets called when user deletes a history entry.
        """
        history_list = self.builder.get_object('history_list')
        model, iterator = history_list.get_selection().get_selected()
        model.remove(iterator)
        self.builder.get_object('edit_window').hide()

    def select_picker_callback(self, widget, index):
        """
        This callback is fired when the user press a picker button.

        The result of this callback is that the current_picker is changed
        to be the actual picker the user has chosen.
        """
        self.start_stop('button')
        if self.current_state == AWAITING_PICKER:
            self.current_picker = index
            self.current_picker_weight = self.current_weight
            self.change_state()

    def select_variety_callback(self, widget, index):
        """
        This callback is fired when the user press a variety button.

        The result of this callback is that the current_variety is changed
        to be the actual variety the user has chosen.
        """
        self.start_stop('button')
        if self.current_state == AWAITING_VARIETY:
            self.current_variety = index
            self.change_state()

    def save_box(self):
        """
        Saves a box with the current picker, batch, variety, weight and timestamp.

        The information will map from -> to:
        - self.current_picker        -> box.picker
        - self.current_batch         -> box.batch
        - self.current_variety       -> box.variety
        - self.current_weight        -> box.final_weight
        - self.current_picker_weight -> box.initial_weight
        - self.timestamp             -> box.timestamp
        """
        self.start_stop('success')
        picker = self.data_model.pickers[self.current_picker]
        batch = self.data_model.batches[self.current_batch]
        variety = self.data_model.varieties[self.current_variety]
        history_store = self.builder.get_object('history_store')
        history_store.append((
            picker['id'],
            picker['first_name'],
            picker['last_name'],
            batch['id'],
            self.data_model.batch_date_str(batch['id']),
            batch['room_number'],
            variety['id'],
            variety['name'],
            self.current_picker_weight,        # initial_weight
            self.current_weight,               # final_weight
            time.strftime('%Y-%m-%d %H:%M:%S', # timestamp
                          time.localtime())
        ))
        self.current_picker = self.current_variety = None

    def open_edit_window(self, widget, data = None):
        """
        This callback is fired when editing an entry in the
        history list.
        """
        self.start_stop('button')
        history_list = self.builder.get_object('history_list')
        model, iterator = history_list.get_selection().get_selected()
        if iterator is not None:
            combo_box = self.builder.get_object('edit_batch_combo')
            batch_number = model.get(iterator, 3)[0]
            batch_idx = self.data_model.inverted_index_batch[batch_number]
            combo_box.set_active(batch_idx)
            combo_box = self.builder.get_object('edit_picker_combo')
            picker_number = model.get(iterator, 0)[0]
            picker_idx = self.data_model.inverted_index_picker[picker_number]
            combo_box.set_active(picker_idx)
            combo_box = self.builder.get_object('edit_variety_combo')
            variety_number = model.get(iterator, 6)[0]
            variety_idx = self.data_model.inverted_index_variety[variety_number]
            combo_box.set_active(variety_idx)
            self.builder.get_object('edit_window').show_all()

    def change_state(self, state = None):
        """
        This method is fired when the overall state of the program is updated.

        The natural order is: AWAITING_BATCH -> AWAITING_BOX ->
        AWAITING_VARIETY -> AWAITING_PICKER -> UNDERWEIGHT|OVERWEIGHT|REMOVE_BOX
        If state is not given, the "next" one in the list follows.
        """
        if state:
            self.current_state = state
            if state == AWAITING_BOX:
                self.show_weight = False
                self.weight_color = config.WHITE_COLOR
            elif state == OVERWEIGHT_ADJUST:
                self.weight_color = config.RED_COLOR
            elif state == UNDERWEIGHT_ADJUST:
                self.weight_color = config.BLUE_COLOR
            elif state == REMOVE_BOX:
                self.weight_color = config.GREEN_COLOR
        else:
            if self.current_state == AWAITING_BATCH:
                self.current_state = AWAITING_BOX
            elif self.current_state == AWAITING_BOX:
                self.current_state = AWAITING_VARIETY
            elif self.current_state == AWAITING_VARIETY:
                self.current_state = AWAITING_PICKER
            elif self.current_state == AWAITING_PICKER:
                self.show_weight = True
            elif self.current_state == REMOVE_BOX:
                self.show_weight = False
                self.current_state = AWAITING_BOX
        GObject.idle_add(self.set_status_feedback)

    def set_status_feedback(self):
        """
        This callback is fired when the status_label needs to be updated.
        """
        color = Gdk.Color(*self.weight_color) # unpack the tuple
        status_label = self.builder.get_object('status_label')
        weight_label = self.builder.get_object('weight_label')
        offset_label = self.builder.get_object('offset_label')
        weight_parent = self.builder.get_object('weight_event_box')
        offset_parent = self.builder.get_object('offset_event_box')
        weight_parent.modify_bg(Gtk.StateType.NORMAL, color)
        offset_parent.modify_bg(Gtk.StateType.NORMAL, color)
        markup = config.STATUS_STYLE.format(
            text = STATUS_MESSAGES[self.current_state])
        status_label.set_markup(markup)
        if self.show_weight is True:
            markup = config.WEIGHT_STYLE.format(self.current_weight)
            weight_label.set_markup(markup)
            offset = self.current_weight - self.min_weight
            markup = config.OFFSET_STYLE.format(offset)
            offset_label.set_markup(markup)
        else:
            weight_label.set_markup(config.NA_MARKUP)
            offset_label.set_markup(config.NA_MARKUP)

    def consumer_thread(self):
        """
        This is the main thread that consumes the stream given from a scale.
        """
        stable_weight = 0
        save_weight = False
        batch_combo_box = self.builder.get_object('batch_combo_box')
        while self.keep_running:
            self.current_weight = self.serial_thread.get_weight()
            if (self.current_state == AWAITING_BATCH and
                batch_combo_box.get_active() >= 0):
                self.current_batch = batch_combo_box.get_active()
                self.change_state()
            elif (save_weight and
                  self.current_weight < config.args.box_weight): # save the box
                save_weight = False
                self.current_weight = stable_weight
                self.save_box()
                self.change_state(AWAITING_BOX)
            elif (self.current_state == AWAITING_BOX and
                  self.current_weight > config.args.box_weight):
                self.change_state()
            elif (self.current_batch is not None and
                  self.current_weight < config.args.box_weight):
                self.change_state(AWAITING_BOX)
            elif self.show_weight:
                self.weight_window.pop(0)
                self.weight_window.append(self.current_weight)
                variety = self.data_model.varieties[self.current_variety]
                self.min_weight = variety['minimum_weight']
                weight_tolerance = variety['tolerance']
                if self.current_weight >= self.min_weight + weight_tolerance:
                    self.change_state(OVERWEIGHT_ADJUST)
                elif self.current_weight < self.min_weight:
                    self.change_state(UNDERWEIGHT_ADJUST)
                else: # within acceptable range
                    if self.current_state != REMOVE_BOX:
                        self.start_stop('green')
                    self.change_state(REMOVE_BOX)
                    if self.weight_window[0] == self.current_weight:
                        stable_weight = self.weight_window[0]
                        save_weight = True
                    if not save_weight:
                        stable_weight = self.current_weight
                        save_weight = True
            time.sleep(0.01)

    def start_stop(self, sound):
        """
        This method is used to play or stop a sound file.
        """
        self.player.set_state(Gst.State.NULL)
        if sound == 'success':
            self.player.set_property('uri', config.SUCCESS_SOUND)
        elif sound == 'green':
            self.player.set_property('uri', config.GREEN_SOUND)
        elif sound == 'button':
            self.player.set_property('uri', config.BUTTON_SOUND)
        self.player.set_state(Gst.State.PLAYING)

if __name__ == '__main__':
    GObject.threads_init()
    Gst.init(sys.argv)
    gui = MainWindow()
    gui.window.show_all()
    Gtk.main()
