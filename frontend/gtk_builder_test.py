from gi.repository import Gtk

class MainWindow:
    def __init__(self):
        builder = Gtk.Builder()
        builder.add_from_file('gui.ui')
        self.window = builder.get_object('window')
        builder.connect_signals(self)

    def exit_callback(self, widget, data = None):
        Gtk.main_quit()

    def open_edit_window(self, widget, data = None):
        pass

    def commit_callback(self, widget, data = None):
        pass

if __name__ == '__main__':
    gui = MainWindow()
    gui.window.show_all()
    Gtk.main()
