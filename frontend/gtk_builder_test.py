"""
Main interface to weigh boxes in Gleba.
"""
from gi.repository import Gtk
import utils
import config

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

    def picker_to_string(self, picker_number, full_name = False):
        """
        Returns a string representing picker picker_number.

        If full_name is True the surname is appended to the string.
        """
        if(full_name):
            return '{0}. {1} {2}'.format(
                self.pickers[picker_number]['id'],
                self.pickers[picker_number]['first_name'],
                self.pickers[picker_number]['last_name']
            )
        else:
            return '{0}. {1}'.format(
                self.pickers[picker_number]['id'],
                self.pickers[picker_number]['first_name']
            )

    def batch_to_string(self, batch_number):
        """
        Returns a string representing batch batch_number.
        """
        return 'Batch No. {} ({}/{}/{}) Room {}'.format(
            self.batches[batch_number]['id'],
            self.batches[batch_number]['date']['day'],
            self.batches[batch_number]['date']['month'],
            self.batches[batch_number]['date']['year'],
            self.batches[batch_number]['room_number']
        )

    def variety_to_string(self, variety_number):
        """
        Returns a string representing variety variety_number.
        """
        return '{0}'.format(
            self.varieties[variety_number]['name']
        )

class MainWindow:
    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file('gui.ui')
        self.window = self.builder.get_object('window')
        self.builder.connect_signals(self)
        self.data_model = DataModel()
        # add batches
        batch_combo_box = self.builder.get_object('batch_combo_box')
        for i, batch in enumerate(self.data_model.batches):
            batch_combo_box.append_text(self.data_model.batch_to_string(i))
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
                button = Gtk.Button(
                    label = self.data_model.picker_to_string(idx)
                )
                button.set_size_request(14, 10)
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
                button = Gtk.Button(
                    label = self.data_model.variety_to_string(idx)
                )
                button.set_size_request(14, 15)
                button.connect('clicked', self.select_variety_callback, idx)
                hbox.add(button)
            variety_vbox.add(hbox)

    def exit_callback(self, widget, data = None):
        Gtk.main_quit()

    def open_edit_window(self, widget, data = None):
        edit_window = self.builder.get_object('edit_window')
        edit_window.show_all()

    def commit_callback(self, widget, data = None):
        pass

    def modify_history_callback(self, widget, data):
        pass

    def select_picker_callback(self, widget, data):
        pass

    def select_variety_callback(self, widget, data):
        pass

if __name__ == '__main__':
    gui = MainWindow()
    gui.window.show_all()
    Gtk.main()
