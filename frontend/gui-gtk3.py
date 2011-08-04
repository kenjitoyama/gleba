#!/usr/bin/python
"""
This is the main client the end-user will interact with.
"""
from gi.repository import Gtk
from gi.repository import Gdk
from threading import Thread
import time
import gobject
import utils
import pygst
pygst.require("0.10")
import gst
import os
import config

gobject.threads_init()

DB = utils.DBAPI()

STATUS_MESSAGES = ['Awaiting\nbatch',
                  'Awaiting\nbox',
                  'Awaiting\npicker',
                  'Awaiting\nvariety',
                  'Overweight,\nAdjust',
                  'Underweight,\nAdjust',
                  'Awaiting\nconfirmation',
                  'Remove box']
AWAITING_BATCH = 0
AWAITING_BOX = 1
AWAITING_PICKER = 2
AWAITING_VARIETY = 3
OVERWEIGHT_ADJUST = 4
UNDERWEIGHT_ADJUST = 5
AWAITING_CONFIRMATION = 6
REMOVE_BOX = 7

WINDOWW = config.WINDOW_WIDTH
WINDOWH = config.WINDOW_HEIGHT

class MainWindow(Gtk.Window):
    save_weight = False
    weight_color = config.WHITE_COLOR
    current_batch = None
    current_picker = None
    current_variety = None
    current_picker_weight = 0
    current_weight = 0
    current_state = AWAITING_BATCH
    stable_weight = 0
    show_weight = False
    min_weight = 0.0
    weight_window = []
    history_entries = []

    def __init__(self):
        super(MainWindow, self).__init__()

        # set minimum size and register the exit button
        self.set_size_request(int(WINDOWW), int(WINDOWH))
        self.connect('destroy', self.exit_callback)

        self.add_widgets()
        self.add_initial_data()
        self.set_status_feedback()

        self.player = gst.element_factory_make('playbin2', 'player')
        fakesink = gst.element_factory_make('fakesink', 'fakesink')
        self.player.set_property('video-sink', fakesink)
        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.connect('message', self.on_message)

        # Thread to read from scale (producer)
        self.serial_thread = utils.ThreadSerial()
        self.serial_thread.daemon = True
        self.serial_thread.start()

        # Thread to process stuff (consumer)
        self.keep_running = True # Kenji: flag to stop the consumer thread
        self.reading_thread = Thread(target = self.consumer_thread)
        self.reading_thread.start()
        self.show_all()


    def add_widgets(self):
        """
        Adds GUI widgets to this object.
        """
        #Main HBox, pack into main window
        main_hbox = Gtk.HBox()
        self.add(main_hbox)

        #Leftmost VBox (batches, status, messages, weight and offset)
        left_vbox = Gtk.VBox()
        #Extra Frame for Batch ComboBox, add to leftmost VBox
        batch_frame = Gtk.Frame(label = 'Batch')
        batch_frame.set_size_request(0, 0) # minimum as possible
        left_vbox.add(batch_frame)
        #Batch ComboBox, pack into batch HBox
        self.batch_combo_box = Gtk.ComboBoxText()
        batch_frame.add(self.batch_combo_box)
        #Status feedback label
        self.status_label = Gtk.Label()
        self.status_label.set_size_request(250, 200)
        left_vbox.add(self.status_label)
        #Weight and offset display labels 
        weight_display_frame = Gtk.Frame(label = 'Weight')
        self.weight_label = Gtk.Label()
        self.event_box = Gtk.EventBox()
        self.event_box.add(self.weight_label)
        weight_display_frame.add(self.event_box)
        left_vbox.add(weight_display_frame)
        offset_display_frame = Gtk.Frame(label = 'Offset')
        self.offset_label = Gtk.Label()
        self.event_box1 = Gtk.EventBox()
        self.event_box1.add(self.offset_label)
        offset_display_frame.add(self.event_box1)
        left_vbox.add(offset_display_frame)

        # Center VBox (Pickers)
        center_vbox = Gtk.VBox()
        picker_frame = Gtk.Frame(label = 'Pickers')
        picker_frame.set_size_request(int(WINDOWW/2), int(WINDOWH/6))
        self.picker_vbox = Gtk.VBox()
        picker_frame.add(self.picker_vbox)
        center_vbox.add(picker_frame)

        # Rightmost VBox (varieties, history and buttons)
        right_vbox = Gtk.VBox()
        varieties_frame = Gtk.Frame(label = 'Varieties')
        varieties_frame.set_size_request(int(WINDOWW/2), int(WINDOWH/2))
        right_vbox.add(varieties_frame)
        self.varieties_vbox = Gtk.VBox()
        varieties_frame.add(self.varieties_vbox)
        adj1 = Gtk.Adjustment(0.0, 0.0, 101.0, 0.1, 1.0, 1.0)
        scrolled_window = Gtk.ScrolledWindow(adj1)
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC,
                                   Gtk.PolicyType.AUTOMATIC)
        right_vbox.add(scrolled_window)
        self.history_list = Gtk.TreeView()
        self.history_store = Gtk.ListStore(str)
        column = Gtk.TreeViewColumn('History', Gtk.CellRendererText(), text=0)
        column.set_resizable(True)
        column.set_sort_column_id(0)
        self.history_list.append_column(column)
        self.history_list.set_model(self.history_store)
        scrolled_window.add(self.history_list)
        edit_button_box = Gtk.HBox()
        right_vbox.add(edit_button_box)
        edit_button = Gtk.Button(label='Edit')
        edit_button.set_size_request(20, 20)
        edit_button_box.add(edit_button)
        edit_button.connect('clicked', self.open_edit_window)
        commit_button = Gtk.Button(label='Commit')
        commit_button.connect('clicked', self.commit_callback)
        edit_button_box.add(commit_button)

        main_hbox.add(left_vbox)
        main_hbox.add(center_vbox)
        main_hbox.add(right_vbox)

    def add_initial_data(self):
        """
        Alleviates the burden of adding data from __init__().
        """
        self.batches   = DB.get_active_batches_xml()
        self.pickers   = DB.get_active_pickers_xml()
        self.varieties = DB.get_active_varieties_xml()
        # add batches
        batch_text_format = 'Batch No. {} ({}) Room {}'
        for batch in self.batches:
            self.batch_combo_box.append_text(batch_text_format.format(
                batch[0], batch[1], batch[2]
            ))
        # add pickers
        picker_total = len(self.pickers)
        cols = config.PICKER_COLS
        rows = picker_total/cols + int(picker_total%cols != 0)
        for row in range(0, rows):
            hbox = Gtk.HBox()
            for col in range(0, cols):
                idx = cols*row + col
                if idx >= picker_total:
                    break
                text = '{0}. {1}'.format(self.pickers[idx][0],
                                         self.pickers[idx][1])
                button = Gtk.Button(label = text)
                button.set_size_request(14, 10)
                button.connect('clicked', self.select_picker_callback, idx)
                hbox.add(button)
            self.picker_vbox.add(hbox)
        # add varieties
        variety_total = len(self.varieties)
        cols = config.VARIETY_COLS
        rows = variety_total/cols + int(variety_total%cols != 0)
        for row in range(0, rows):
            hbox = Gtk.HBox()
            for col in range(0, cols):
                idx = cols*row + col
                if idx >= variety_total:
                    break
                text = '{0}'.format(self.varieties[idx][1])
                button = Gtk.Button(label = text)
                button.set_size_request(14, 15)
                button.connect('clicked', self.select_variety_callback, idx)
                hbox.add(button)
            self.varieties_vbox.add(hbox)
        # initialize weight_window
        for i in range(0, config.WEIGHT_WINDOW_SIZE):
            self.weight_window.append(0)
        
    def open_edit_window(self, button):
        """
        This callback is fired when editing an entry in the
        history list.
        """
        # add widgets
        self.start_stop('button')
        selection, iterator = self.history_list.get_selection().get_selected()
        if iterator is not None:
            edit_dialog = Gtk.Window()
            edit_vbox = Gtk.VBox()
            edit_batch_frame = Gtk.Frame(label = 'Batch')
            edit_picker_frame = Gtk.Frame(label = 'Picker')
            edit_variety_frame = Gtk.Frame(label = 'Variety')
            edit_vbox.add(edit_batch_frame)
            edit_vbox.add(edit_picker_frame)
            edit_vbox.add(edit_variety_frame)
            # Kenji: TODO row is super ugly. change this later.
            row = int(str(selection.get_path(iterator)))
            index_list = self.history_entries[row][6]
            # get batches
            edit_batch_combo = Gtk.ComboBoxText()
            for batch in self.batches:
                edit_batch_combo.append_text(
                    'Batch No. {} ({}) Room {}'.format(
                        batch[0], batch[1], batch[2]
                ))
            edit_batch_combo.set_active(index_list[0])
            # get pickers
            edit_picker_combo = Gtk.ComboBoxText()
            for picker in self.pickers:
                edit_picker_combo.append_text('{}. {} {}'.format(
                    picker[0], picker[1], picker[2]
                ))
            edit_picker_combo.set_active(index_list[2])
            # get varieties
            edit_varieties_combo = Gtk.ComboBoxText()
            for variety in self.varieties:
                edit_varieties_combo.append_text('{}. {}'.format(
                    variety[0], variety[1]
                ))
            edit_varieties_combo.set_active(index_list[1])
            # pack everything and show window
            edit_batch_frame.add(edit_batch_combo)
            edit_picker_frame.add(edit_picker_combo)
            edit_variety_frame.add(edit_varieties_combo)
            edit_delete_button = Gtk.Button(label = 'Delete Record')
            edit_delete_button.connect('clicked',
                                       self.modify_history_callback,
                                       iterator, row, True,
                                       edit_batch_combo,
                                       edit_varieties_combo,
                                       edit_picker_combo,
                                       edit_dialog)
            edit_delete_button.set_size_request(10, 15)
            edit_apply_button = Gtk.Button(label = 'Apply Changes')
            edit_apply_button.set_size_request(10, 35)
            edit_apply_button.connect('clicked',
                                      self.modify_history_callback,
                                      iterator, row, False,
                                      edit_batch_combo,
                                      edit_varieties_combo,
                                      edit_picker_combo,
                                      edit_dialog)
            edit_vbox.add(edit_apply_button)
            edit_vbox.add(edit_delete_button)
            edit_dialog.add(edit_vbox)
            edit_dialog.set_size_request(int(WINDOWW/2.7),
                                         int(WINDOWH/1.6))
            edit_dialog.show_all()
    
    def modify_history_callback(self, button, iterator, row, delete,
                                      batch_combobox,
                                      varieties_combobox,
                                      picker_combobox,
                                      edit_dialog):
        """
        This callback is fired when an entry in the history list has been
        edited in the edit window.
        """
        self.start_stop('button')
        self.history_store.remove(iterator)
        if delete:
            self.history_entries.pop(row)
        else:
            entry = self.history_entries[row]
            #modify      
            self.current_batch = batch_combobox.get_active()
            self.current_variety = varieties_combobox.get_active()
            self.current_picker = picker_combobox.get_active()
            index_list = (self.current_batch,
                          self.current_variety,
                          self.current_picker)
            #retain
            self.current_picker_weight = entry[3]
            self.current_weight = entry[4]
            self.history_entries[row] = (self.pickers[self.current_picker][0],
                                        self.batches[self.current_batch][0],
                                        self.varieties[self.current_variety][0],
                                        self.current_picker_weight,
                                        self.current_weight,
                                        time.strftime('%Y-%m-%d %H:%M:%S',
                                                      time.localtime()),
                                        index_list)
            #modify treeView model
            temp = []
            text = ('Picker {picker_number} ' +
                   '({picker_firstname} {picker_lastname}), ' +
                   'Variety {variety_number} ({variety_name}), ' +
                   'Batch {batch_number} ({batch_date}), ' +
                   'Room {room_number}, ' +
                   'Picker Weight: {picker_weight}, ' +
                   'Final Weight: {final_weight}, Time: {timestamp}')
            temp.append(text.format(
                picker_number    = self.pickers[self.current_picker][0],
                picker_firstname = self.pickers[self.current_picker][1],
                picker_lastname  = self.pickers[self.current_picker][2],
                variety_number   = self.varieties[self.current_variety][0],
                variety_name     = self.varieties[self.current_variety][1],
                batch_number     = self.batches[self.current_batch][0],
                batch_date       = self.batches[self.current_batch][1],
                room_number      = self.batches[self.current_batch][2],
                picker_weight    = self.current_picker_weight,
                final_weight     = self.current_weight,
                timestamp        = time.strftime('%Y-%m-%d %H:%M:%S',
                                                 time.localtime())
            ))
            self.history_store.insert(row, temp)
        edit_dialog.destroy()

    def exit_callback(self, widget):
        """
        This callback is fired when the user exits the program.
        """
        self.keep_running = False
        self.serial_thread.kill()
        Gtk.main_quit()

    def select_picker_callback(self, button, index):
        """
        This callback is fired when the user press a picker button.

        The result of this callback is that the current_picker is changed
        to be the actual picker the user has chosen.
        """
        self.start_stop('button')
        self.current_picker = index
        if self.current_state == AWAITING_PICKER:
            self.current_picker_weight = self.current_weight
            self.change_state()

    def select_variety_callback(self, button, index):
        """
        This callback is fired when the user press a variety button.

        The result of this callback is that the current_variety is changed
        to be the actual variety the user has chosen.
        """
        self.start_stop('button')
        self.current_variety = index
        if self.current_state == AWAITING_VARIETY:
            self.change_state()

    def commit_callback(self, button):
        """
        This callback is fired when the user presses the commit button.

        After this callback, the data in the history is sent to the server and
        committed to the database.
        """
        self.start_stop('button')
        for (picker, batch, variety, init_weight,
             final_weight, timestamp, index_list) in self.history_entries:
            DB.add_box(picker, batch, variety, init_weight,
                      final_weight, timestamp)
        # clear the history
        self.history_store.clear()
        self.history_entries = []
        self.show_all()

    def history_callback(self, button):
        """
        This callback is fired when any entry in the history list has been
        added, deleted or modified.
        """
        self.start_stop('success')
        self.current_weight = self.stable_weight
        temp = []
        index_list = []
        index_list.append(self.current_batch)
        index_list.append(self.current_variety)
        index_list.append(self.current_picker)
        text = ('Picker {picker_number} ' +
               '({picker_firstname} {picker_lastname}), ' +
               'Variety {variety_number} ({variety_name}), ' +
               'Batch {batch_number} ({batch_date}), Room {room_number}, ' +
               'Picker Weight: {picker_weight}, ' +
               'Final Weight: {final_weight}, Time: {timestamp}')
        temp.append(text.format(
            picker_number    = self.pickers[self.current_picker][0],
            picker_firstname = self.pickers[self.current_picker][1],
            picker_lastname  = self.pickers[self.current_picker][2],
            variety_number   = self.varieties[self.current_variety][0],
            variety_name     = self.varieties[self.current_variety][1],
            batch_number     = self.batches[self.current_batch][0],
            batch_date       = self.batches[self.current_batch][1],
            room_number      = self.batches[self.current_batch][2],
            picker_weight    = self.current_picker_weight,
            final_weight     = self.current_weight,
            timestamp        = time.strftime('%Y-%m-%d %H:%M:%S',
                                             time.localtime())
        ))

        self.history_entries.append((self.pickers[self.current_picker][0],
                                    self.batches[self.current_batch][0],
                                    self.varieties[self.current_variety][0],
                                    self.current_picker_weight,
                                    self.current_weight,
                                    time.strftime('%Y-%m-%d %H:%M:%S',
                                                  time.localtime()),
                                    index_list))
        self.history_store.append(temp)
        self.history_list.set_model(self.history_store)
        self.show_all()

    def set_status_feedback(self):
        """
        This callback is fired when the status_label needs to be updated.
        """
        color = Gdk.Color(*self.weight_color) # unpack the tuple
        self.event_box.modify_bg(Gtk.StateType.NORMAL, color)
        self.event_box1.modify_bg(Gtk.StateType.NORMAL, color)
        markup = config.STATUS_STYLE.format(
            text = STATUS_MESSAGES[self.current_state])
        self.status_label.set_markup(markup)
        if self.show_weight is True:
            markup = config.WEIGHT_STYLE.format(self.current_weight)
            self.weight_label.set_markup(markup)
            offset = self.current_weight - self.min_weight
            markup = config.OFFSET_STYLE.format(offset)
            self.offset_label.set_markup(markup)
        else:
            self.weight_label.set_markup(config.NA_MARKUP)
            self.offset_label.set_markup(config.NA_MARKUP)

    def consumer_thread(self):
        """
        This is the main thread that consumes the stream given from a scale.
        """
        while self.keep_running:
            self.current_batch = self.batch_combo_box.get_active()
            self.current_weight = self.serial_thread.get_weight()
            if self.current_state == AWAITING_BATCH:
                if (self.current_batch is not None and
                    self.current_batch >= 0): # -1 if no active item
                    self.current_batch = self.batch_combo_box.get_active()
                    self.change_state()
            elif self.save_weight and self.current_weight < 0.4:
                self.save_weight = False
                self.current_weight = self.stable_weight
                self.change_state(AWAITING_BOX)
                self.history_callback(None)
            elif self.current_state == AWAITING_BOX:
                if self.current_weight > config.BOX_WEIGHT:
                    self.change_state()
            elif (self.current_batch is not None and
                  self.current_weight < config.BOX_WEIGHT):
                self.change_state(AWAITING_BOX)
            if self.show_weight:
                self.weight_window.pop(0)
                self.weight_window.append(self.current_weight)
                self.min_weight = self.varieties[self.current_variety][2]
                weight_tolerance = self.varieties[self.current_variety][3]
                if self.current_weight >= self.min_weight + weight_tolerance:
                    self.change_state(OVERWEIGHT_ADJUST)
                elif self.current_weight < self.min_weight:
                    self.change_state(UNDERWEIGHT_ADJUST)
                else: # within acceptable range
                    if self.weight_color != config.GREEN_COLOR:
                        self.start_stop('green')
                    self.change_state(REMOVE_BOX)
                    if self.weight_window[0] == self.current_weight:
                        self.stable_weight = self.weight_window[0]
                        self.save_weight = True
                    if not self.save_weight:
                        self.stable_weight = self.current_weight
                        self.save_weight = True
            time.sleep(0.01)

    def change_state(self, state = None):
        """
        This method is fired when the overall state of the program is updated.

        The natural order is: AWAITING_BATCH -> AWAITING_BOX ->
        AWAITING_VARIETY -> AWAITING_PICKER -> UNDERWEIGHT|OVERWEIGHT|REMOVE_BOX
        If state is not given, the "next" one in the list follows.
        """
        if state == None:
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
        else:
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
        gobject.idle_add(self.set_status_feedback)

    def start_stop(self, sound):
        """
        This method is used to play or stop a sound file.
        """
        path = 'file://{0}/'.format(os.getcwd())
        if sound == 'success':
            self.player.set_property('uri', path + 'success.ogg')
        elif sound == 'green':
            self.player.set_property('uri', path + 'green.ogg')
        elif sound == 'button':
            self.player.set_property('uri', path + 'button.ogg')
        self.player.set_state(gst.STATE_PLAYING)

    def on_message(self, bus, message):
        """
        This callback is fired when messages for GStreamer happen.
        """
        message_type = message.type
        if message_type == gst.MESSAGE_EOS:
            self.player.set_state(gst.STATE_NULL)
        elif message_type == gst.MESSAGE_ERROR:
            self.player.set_state(gst.STATE_NULL)
            err, debug = message.parse_error()
            print('Error: {}'.format(err), debug)
            print('Bus: {}'.format(str(bus)))

if __name__ == '__main__':
    main_window = MainWindow()
    Gtk.main()
