#!/usr/bin/python
from threading import Thread
import time
import gtk
import gobject
import utils
import pygst
pygst.require("0.10")
import gst
import os, sys

db = utils.DBAPI()
statusMessages = ["Awaiting \n batch",
                  "Awaiting \n box",
                  "Awaiting \n picker",
                  "Awaiting \n variety",
                  "Overweight,\n Adjust",
                  "Underweight,\n Adjust",
                  "Awaiting \n confirmation",
                  "Remove box"]
AWAITING_BATCH = 0
AWAITING_BOX = 1
AWAITING_PICKER = 2
AWAITING_VARIETY = 3
OVERWEIGHT_ADJUST = 4
UNDERWEIGHT_ADJUST = 5
AWAITING_CONFIRMATION = 6
REMOVE_BOX = 7
EDIT = 7

WINDOWW=800.0
WINDOWH=600.0
#WINDOWW=1024.0
#WINDOWH=768.0

class MainWindow(gtk.Window):
    saveWeight = False
    weightColor = "white"
    currentBatch = None
    currentPicker = None
    currentVariety = None
    currentPickerWeight = 0
    currentWeight = 0
    currentState = 0
    stableWeight = 0
    statusText = statusMessages[currentState]
    showWeight = False
    weightMin=0
    weightWindow = []
    for i in range(0,100):
        weightWindow.append(0)

    def __init__(self):
        super(MainWindow, self).__init__()

        #Thread to read from scale
        self.ts = utils.ThreadSerial()
        self.ts.daemon=True
        self.ts.start()

        # set minimum size and register the exit button
        self.set_size_request(int(WINDOWW), int(WINDOWH))
        self.connect("destroy", self.exit_callback)

        #Main HBox, pack into main window
        self.mainHbox = gtk.HBox()
        self.add(self.mainHbox)

        #statusFrame for leftmost VBox, pack into mainHbox
        self.statusFrame = gtk.Frame()
        self.statusFrame.set_size_request(int(WINDOWW/2.5), int(WINDOWH/6))
        self.mainHbox.pack_start(self.statusFrame)

        #Leftmost VBox, add to statusFrame
        self.statusVbox = gtk.VBox()
        self.statusFrame.add(self.statusVbox)

        #Extra Frame for Batch ComboBox, add to leftmost VBox
        self.batchFrame = gtk.Frame(label="Batch")
        self.batchFrame.set_size_request(0,0) # minimum as possible
        self.statusVbox.pack_start(self.batchFrame)

        #Add batch HBox for combo box and button to batchFrame

        #Batch ComboBox, pack into batch HBox
        self.batchComboBox = gtk.combo_box_new_text()
        self.batchFrame.add(self.batchComboBox)
        
        #Status feedback label
        self.statusLabel = gtk.Label()
        self.statusLabel.set_size_request(250,200)
        self.statusVbox.pack_start(self.statusLabel)
        style = "<span foreground='#000000' size='large' " + \
                "weight='bold' font_desc='Calibri 14'>"
        self.statusLabel.set_markup( style + self.statusText + "</span>")

        #Input Scroll bar
        adj1 = gtk.Adjustment(0.0, 0.0, 8001, 1, 1.0, 1.0)

        #self.hscale = gtk.HScale(adj1)
        #self.hscale.set_size_request(int(WINDOWW/4), 30)
        #self.hscale.set_update_policy(gtk.UPDATE_CONTINUOUS)
        #self.hscale.set_digits(1)
        #self.hscale.set_value_pos(gtk.POS_TOP)
        #self.hscale.set_draw_value(True)
        #self.statusVbox.pack_start(self.hscale, True, True, 0)
        #self.hscale.show()

        #Button to start thread, remove this later
        self.b = gtk.Button(stock=gtk.STOCK_OK)
        #self.statusVbox.pack_start(self.b)
        self.b.connect('clicked', self.history_callback)
        self.b.set_sensitive(False)

        # Button to commit the weight even if out of range
        #self.recordButton = gtk.Button(label="Record weight")
        #self.recordButton.connect('clicked', self.history_callback)
        #self.statusVbox.pack_start(self.recordButton)

        #Weight and offset display labels 
        weightDisplayFrame = gtk.Frame(label = "Weight")
        self.weightLabel = gtk.Label()
        self.event_box = gtk.EventBox()
        self.event_box.add(self.weightLabel)
        weightDisplayFrame.add(self.event_box)
        self.statusVbox.add(weightDisplayFrame)
        
        offsetDisplayFrame = gtk.Frame(label = "Offset")
        self.offsetLabel = gtk.Label()
        self.event_box1 = gtk.EventBox()
        self.event_box1.add(self.offsetLabel)
        offsetDisplayFrame.add(self.event_box1)
        self.statusVbox.add(offsetDisplayFrame)

        self.set_status_feedback()

        #Frame for middle VBox() containing pickers
        pickerFrame = gtk.Frame(label = "Pickers")
        pickerFrame.set_size_request(int(WINDOWW/2),int(WINDOWH/6))
        self.pickerVbox = gtk.VBox()
        pickerFrame.add(self.pickerVbox)
        self.mainHbox.pack_start(pickerFrame)

        self.historyVbox = gtk.VBox()
        self.varietiesFrame = gtk.Frame(label = "Varieties")
        self.varietiesFrame.set_size_request(int(WINDOWW/2), int(WINDOWH/2))
        self.historyVbox.pack_start(self.varietiesFrame)
	
        self.varietiesVbox = gtk.VBox()
        self.varietiesFrame.add(self.varietiesVbox)

        #Frame for rightmost VBox() containing entry history
        self.historyFrame = gtk.Frame()
        self.mainHbox.pack_start(self.historyFrame)
        self.historyFrame.set_size_request(int(WINDOWW/4),0)
        
        adj1 = gtk.Adjustment(0.0, 0.0, 101.0, 0.1, 1.0, 1.0)

        self.sw = gtk.ScrolledWindow(adj1)
        self.sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        self.historyFrame1 = gtk.Frame()
        self.historyFrame1.add(self.sw)
        self.historyFrame1.set_size_request(int(WINDOWW/2), int(WINDOWH/3))
        self.historyFrame.add(self.historyVbox)
        self.historyVbox.pack_start(self.historyFrame1)
        
        self.historyList = gtk.TreeView()
        self.historyStore = gtk.ListStore(str)
        column = gtk.TreeViewColumn("History", gtk.CellRendererText(), text=0)
        column.set_resizable(True)
        column.set_sort_column_id(0)
        self.historyList.append_column(column)
        self.historyList.set_model(self.historyStore)
        self.sw.add(self.historyList)
        
        self.editButtonBox = gtk.HBox()
        
        self.historyFrame2 = gtk.Frame()
        self.historyFrame2.set_size_request(int(WINDOWW/2), int(WINDOWH/24))
        self.historyVbox.pack_start(self.historyFrame2)
        self.historyFrame2.add(self.editButtonBox)
        
        self.editButton = gtk.Button(label="Edit")
        self.editButton.set_size_request(20,20)
        self.editButtonBox.pack_start(self.editButton)
        self.editButton.connect('clicked', self.edit_window)

        self.commitButton = gtk.Button(label="Commit")
        self.commitButton.connect('clicked', self.commit_callback)
        self.editButtonBox.pack_start(self.commitButton)
        
        self.add_initial_data()

        self.keepRunning=True #Kenji: flag to stop the thread
        self.count_in_thread(4.3)
        self.show_all()

        self.player = gst.element_factory_make("playbin2", "player")
        fakesink = gst.element_factory_make("fakesink", "fakesink")
        self.player.set_property("video-sink", fakesink)
        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.on_message)

    def add_initial_data(self):
        self.pickers = db.getActivePickers()
        self.batches = db.getActiveBatches()
        self.varieties = db.getActiveVarieties()
        for b in self.batches:
            self.batchComboBox.append_text("Batch No. " + b[0] + \
                                           " (" + b[1] + ") Room " + \
                                           b[2])
        buttons = []
        hboxes = []
        for j in range(0,len(self.pickers)/4+int(len(self.pickers)%4!=0)):
            hboxes.append(gtk.HBox())
            self.pickerVbox.pack_start(hboxes[j])
            for i in range(0,4):
                if 4*j+i >= len(self.pickers):
                    break
                button = gtk.Button(label = self.pickers[4*j+i][0]+". "+ self.pickers[4*j+i][1])
                button.set_size_request(14,10)
                button.connect("clicked", self.select_picker_callback, 4*j+i)
                buttons.append(button)
                hboxes[j].pack_start(button)
        self.varietiesHboxes = []
        varietiesButtons = []
        for j in range(0,len(self.varieties)/2+int(len(self.varieties)%2!=0)):
            self.varietiesHboxes.append(gtk.HBox())
            self.varietiesVbox.pack_start(self.varietiesHboxes[j])
            for i in range(0,2):
                if 2*j+i >= len(self.varieties):
                    break
                button = gtk.Button(label=self.varieties[2*j+i][1]) #self.varieties[2*j+i][0]+". "+ 
                button.set_size_request(14,15)
                button.connect("clicked", self.select_variety_callback, 2*j+i)
                varietiesButtons.append(button)
                self.varietiesHboxes[j].pack_start(button)
        self.historyEntries = []
        for entry in self.historyEntries:
            temp = []
            temp.append(entry)
            self.historyStore.append(temp)
        

    def edit_window(self, whatever):
        # add widgets
        self.start_stop("button")
        selection, iter = self.historyList.get_selection().get_selected()
        if iter is not None:
            self.edit_window = gtk.Window(gtk.WINDOW_TOPLEVEL)
            vb = gtk.VBox()
            editFrame = gtk.Frame(label="Modify Entry")
            f1 = gtk.Frame(label="Batch")
            f2 = gtk.Frame(label="Picker")
            f3 = gtk.Frame(label="Variety")
            f4 = gtk.Frame(label="")
            vb.pack_start(f1)
            vb.pack_start(f2)
            vb.pack_start(f3)
            vb.pack_start(f4)
            row = selection.get_path(iter)[0]
            deleteButton = gtk.Button(label="Delete Record")
            deleteButton.connect("clicked", self.modify_history_callback, iter, row, True)
            deleteButton.set_size_request(10,15)
            applyButton = gtk.Button(label="Apply Changes")
            applyButton.set_size_request(10,35)
            applyButton.connect("clicked", self.modify_history_callback, iter, row, False)
            editFrame.set_size_request(0,60)
            indexList = self.historyEntries[row][6]
            # get batches
            self.editBatchCombo = gtk.combo_box_new_text()
            #vb.pack_start(self.editBatchCombo)
            for b in self.batches:
                self.editBatchCombo.append_text("Batch " + b[0] +\
                                                " " + b[1] +\
                                                " Room " + b[2])
            self.editBatchCombo.set_active(indexList[0])
            # get pickers
            self.editPickerCombo = gtk.combo_box_new_text()
            #vb.pack_start(self.editPickerCombo)
            for p in self.pickers:
                self.editPickerCombo.append_text(p[0] + ". " + p[1] + " " + p[2])
            self.editPickerCombo.set_active(indexList[2])
            # get varieties
            self.editVarietiesCombo = gtk.combo_box_new_text()
            #vb.pack_start(self.editVarietiesCombo)
            for v in self.varieties:
                self.editVarietiesCombo.append_text(v[0] + " " + v[1])
            self.editVarietiesCombo.set_active(indexList[1])
            # pack everything and show window
            f1.add(self.editBatchCombo)
            f2.add(self.editPickerCombo)
            f3.add(self.editVarietiesCombo)
            vb2 = gtk.VBox()
            f5 = gtk.Frame()
            f5.set_size_request(100,50)
            vb2.pack_start(applyButton)
            vb2.pack_start(f5)
            vb2.pack_start(deleteButton)
            editFrame.add(vb)
            f4.add(vb2)
            self.edit_window.add(editFrame)
            self.edit_window.set_size_request(int(WINDOWW/2.7), int(WINDOWH/1.6));
            self.edit_window.show_all()
    
    def modify_history_callback(self, x, iter, row, delete):
            self.start_stop("button")
            self.historyStore.remove(iter)
            if delete is not True:
                entry = self.historyEntries[row]
                #modify      
                self.currentBatch_ = self.editBatchCombo.get_active()
                self.currentVariety = self.editVarietiesCombo.get_active()
                self.currentPicker = self.editPickerCombo.get_active()
                indexList = (self.currentBatch, self.currentVariety, self.currentPicker)
                #retain
                self.currentPickerWeight = entry[3]
                self.currentWeight = entry[4]
                self.historyEntries[row] = (self.pickers[self.currentPicker][0],
                                                self.batches[self.currentBatch_][0],
                                                self.varieties[self.currentVariety][0],
                                                self.currentPickerWeight,
                                                self.currentWeight,
                                                time.strftime("%Y-%m-%d %H:%M:%S",
                                                time.localtime()), indexList)
                #modify treeView model
                temp = []


		entry = "Picker No. " + str(self.pickers[self.currentPicker][0])
                entry += ", " +str(self.pickers[self.currentPicker][1])
                entry += " " + str(self.pickers[self.currentPicker][2])
		entry += ", Variety: " + self.varieties[self.currentVariety][0]
                entry += ". " + self.varieties[self.currentVariety][1]
                entry += ", Batch No. " + str(self.batches[self.currentBatch_][0])
                entry += " (" + str(self.batches[self.currentBatch_][1])
                entry += ") Room " + str(self.batches[self.currentBatch_][0])
                entry += ", Picker Weight: " + str(self.currentPickerWeight)
                entry += ", Final Weight: " + str(self.currentWeight)
                entry += ", Time: " + time.strftime("%Y-%m-%d %H:%M:%S",
                                                   time.localtime())
                """entry = "Batch No. " + str(self.batches[self.currentBatch_][0])
                entry += " (" + str(self.batches[self.currentBatch_][1])
                entry += ") Room " + str(self.batches[self.currentBatch_][0])
                entry += ", Variety: " + self.varieties[self.currentVariety][0]
                entry += ". " + self.varieties[self.currentVariety][1]
                entry += ", Picker No. " + str(self.pickers[self.currentPicker][0])
                entry += ", " +str(self.pickers[self.currentPicker][1])
                entry += " " + str(self.pickers[self.currentPicker][2])
                entry += ", Picker Weight: " + str(self.currentPickerWeight)
                entry += ", Final Weight: " + str(self.currentWeight)
                entry += ", Time: " + time.strftime("%Y-%m-%d %H:%M:%S",
                                                       time.localtime())"""
                temp.append(entry)
                self.historyStore.insert(row, temp)
                #self.historyList.set_model(self.historyStore)
                #self.show_all()
            #gtk.main_quit()
            else:
                self.historyEntries.pop(row)
            self.edit_window.destroy()


    def exit_callback(self, whatever):
        self.keepRunning=False
        self.ts.kill()
        gtk.main_quit()

    def select_picker_callback(self, buttonId, index):
        self.start_stop("button")
        self.currentPicker = index
        if self.currentState==AWAITING_PICKER:
            self.currentPickerWeight = self.currentWeight
            self.change_state()
            self.statusText = statusMessages[self.currentState]
            self.set_status_feedback()

    def select_variety_callback(self, buttonId, index):
        self.start_stop("button")
        self.currentVariety = index
        if self.currentState==AWAITING_VARIETY:
            self.change_state()
            self.statusText = statusMessages[self.currentState]
            self.set_status_feedback()

    def commit_callback(self, whatever):
        self.start_stop("button")
        for (picker, batch, variety,
             initWeight, finalWeight, timestamp, indexList) in self.historyEntries:
            db.addBox(picker, batch, variety,
                      initWeight, finalWeight, timestamp)
        # clear the history
        self.historyStore.clear()
        self.historyEntries = []
        self.show_all()

    def get_active_text(self, combobox):
        model = combobox.get_model()
        active = combobox.get_active()
        if active < 0:
            return None
        return model[active][0]

    def history_callback(self, button):
        self.start_stop("success")
        self.currentWeight = self.stableWeight
        temp = []
        indexList = []
        indexList.append(self.currentBatch)
        indexList.append(self.currentVariety)
        indexList.append(self.currentPicker)
        entry = "Picker No. " + str(self.pickers[self.currentPicker][0])
        entry += ", " +str(self.pickers[self.currentPicker][1])
        entry += " " + str(self.pickers[self.currentPicker][2])
        entry += ", Variety: " + self.varieties[self.currentVariety][0]
        entry += ". " + self.varieties[self.currentVariety][1]
        entry += ", Batch No. " + str(self.batches[self.currentBatch][0])
        entry += " (" + str(self.batches[self.currentBatch][1])
        entry += ") Room " + str(self.batches[self.currentBatch][0])
        entry += ", Picker Weight: " + str(self.currentPickerWeight)
        entry += ", Final Weight: " + str(self.currentWeight)
        entry += ", Time: " + time.strftime("%Y-%m-%d %H:%M:%S",
                                           time.localtime())
        temp.append(entry)
        self.historyEntries.append((self.pickers[self.currentPicker][0],
                                    self.batches[self.currentBatch][0],
                                    self.varieties[self.currentVariety][0],
                                    self.currentPickerWeight,
                                    self.currentWeight,
                                    time.strftime("%Y-%m-%d %H:%M:%S",
                                    time.localtime()), indexList))
        self.historyStore.append(temp)
        self.historyList.set_model(self.historyStore)
        self.show_all()

    def count_in_thread(self, maximum):
        Thread(target=self.count_up, args=(maximum,)).start()

    def set_status_feedback(self):
        self.event_box.modify_bg(gtk.STATE_NORMAL,
                                 gtk.gdk.color_parse(self.weightColor))
        self.event_box1.modify_bg(gtk.STATE_NORMAL,
                                  gtk.gdk.color_parse(self.weightColor))
        self.statusText = statusMessages[self.currentState]
        style = "<span foreground='#000000' size='large' " +\
                "weight='bold' font_desc='Calibri 20'>"
        self.statusLabel.set_markup( style + self.statusText + "</span>")
        if self.showWeight is True:
            style = "<span foreground='#FFFFFF' size='xx-large' " +\
                    "weight='bold' font_desc='Calibri 24'>"
            self.weightLabel.set_markup(style +\
                                        str("%.3f" % self.currentWeight) +\
                                        "</span>")
            if self.currentWeight < self.weightMin:
                    self.offsetLabel.set_markup(style +\
                                                str("%.3f" % (self.currentWeight-self.weightMin)) +\
                                                "</span>")
            else:
                    self.offsetLabel.set_markup(style +\
                                                str("+%.3f" % (self.currentWeight-self.weightMin)) +\
                                                "</span>")
        else:
            style = "<span foreground='#000000' size='xx-large' " +\
                    "weight='bold' font_desc='Calibri 24'>"
            self.weightLabel.set_markup( style + "N/A" + "</span>")
            self.offsetLabel.set_markup( style + "N/A" + "</span>")

    def check_box_removed(self):
        if self.hscale.get_value() < 100:
            self.boxRemoved = True
        else:
            self.boxRemoved = False

    def count_up(self, maximum):
        while (self.keepRunning==True):
            self.currentBatch = self.batchComboBox.get_active()
            self.currentWeight = self.ts.getWeight()
            if self.currentState == AWAITING_BATCH:
                if self.currentBatch is not None and self.currentBatch is not -1:
                    self.currentBatch = self.batchComboBox.get_active()
                    gobject.idle_add(self.change_state)
                    gobject.idle_add(self.set_status_feedback)
            elif self.saveWeight and self.currentWeight < 0.4:
                self.saveWeight = False
                self.currentWeight = self.stableWeight
                self.currentState = AWAITING_BOX
                self.showWeight = False
                self.weightColor = "white"
                gobject.idle_add(self.set_status_feedback)
                gobject.idle_add(self.history_callback, self.b)
            elif self.currentState == AWAITING_BOX:
                if self.currentWeight > 0.1:
                    gobject.idle_add(self.change_state)
                    gobject.idle_add(self.set_status_feedback)
            elif self.currentBatch is not None and self.currentWeight<0.1:
                self.currentState = AWAITING_BOX
                self.showWeight = False
                self.weightColor = "white"
                gobject.idle_add(self.set_status_feedback)
            if self.showWeight==True:
                self.weightWindow.pop(0)
                self.weightWindow.append(self.currentWeight)
                self.weightMin=float(self.varieties[self.currentVariety][2])
                self.weightTolerance=float(self.varieties[self.currentVariety][3])
                # If box weight is overweight
                if self.currentWeight>=self.weightMin+self.weightTolerance:
                #if self.currentWeight>=1.76:
                    self.weightColor = "red"
                    self.currentState = OVERWEIGHT_ADJUST
                    gobject.idle_add(self.b.set_sensitive,False)
                # If box weight is underweight
                elif self.currentWeight<self.weightMin:
                    gobject.idle_add(self.b.set_sensitive,False)
                #elif self.currentWeight<1.7:
                    self.weightColor = "blue"
                    self.currentState = UNDERWEIGHT_ADJUST
                # If box weight is within acceptable range
                else:
                    if self.weightColor is not "green":
                        self.start_stop("green")
                    self.weightColor = "green"
                    self.currentState = REMOVE_BOX
                    if self.weightWindow[0] == self.currentWeight:
                        self.stableWeight = self.weightWindow[0]
                        self.saveWeight = True
                    if self.saveWeight is False:
                        self.stableWeight = self.currentWeight
                        self.saveWeight = True
                        #gobject.idle_add(self.set_status_feedback)
                        #time.sleep(2)
                        
                        ##############ADDED#################
                        gobject.idle_add(self.b.set_sensitive,True)
                        ####################################
                                         
                        #if self.ts.getWeight() < 0.5 and self.ts.isStable():
                            #gobject.idle_add(self.history_callback, self.b)
                            #self.weightColor = "white"
                gobject.idle_add(self.set_status_feedback)
            time.sleep(0.01)


    def change_state(self):
        if self.currentState==AWAITING_BATCH:
            self.currentState=AWAITING_BOX
        elif self.currentState==AWAITING_BOX:
            self.currentState=AWAITING_VARIETY
        elif self.currentState==AWAITING_VARIETY:
            self.currentState=AWAITING_PICKER
        elif self.currentState==AWAITING_PICKER:
            self.showWeight = True
        elif self.currentState==REMOVE_BOX:
            self.showWeight = False
            self.currentState=AWAITING_BOX
            self.set_status_feedback()
            #self.currentPicker = None

    def start_stop(self, sound):
        path = 'file://{0}/'.format(os.getcwd())
        if sound=="success":
            self.player.set_property('uri', path + 'success.ogg'
            )
        elif sound=="green":
            self.player.set_property('uri', path + 'green.ogg')
        elif sound=="button":
            self.player.set_property('uri', path + 'button.ogg')
        self.player.set_state(gst.STATE_PLAYING)

    def on_message(self, bus, message):
        t = message.type
        if t == gst.MESSAGE_EOS:
            self.player.set_state(gst.STATE_NULL)
        elif t == gst.MESSAGE_ERROR:
            self.player.set_state(gst.STATE_NULL)
            err, debug = message.parse_error()
            print "Error: %s" % err, debug

    def main(self):
        gtk.main()

if __name__ == '__main__':
    gtk.gdk.threads_init() #serialize access to the interpreter
    w = MainWindow()
    w.main()
