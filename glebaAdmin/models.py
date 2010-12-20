from django.db import models

# Create your models here.
class Picker(models.Model):
    firstName = models.CharField(max_length=50)
    lastName = models.CharField(max_length=50)
    active = models.BooleanField()
    discharged = models.BooleanField()
    class Meta:
        verbose_name_plural="Pickers"
    def __unicode__(self):
        return "Picker " + str(self.id) + " " + self.firstName + " " + self.lastName

class Bundy(models.Model):
    picker=models.ForeignKey(Picker)
    timeIn=models.DateTimeField('Time In')
    timeOut=models.DateTimeField('Time Out', blank=True, null=True)
    class Meta:
        verbose_name_plural="Bundies"
    def __unicode__(self):
        return "Bundy " + str(self.picker) + ' ' + str(self.timeIn)
    def timeWorked(self):
        "Returns the amount of hours worked in this bundy"
        return (self.timeOut-self.timeIn).seconds/3600.0

class Room(models.Model):
    number = models.IntegerField()
    status = models.CharField(max_length=50)
    class Meta:
        verbose_name_plural="Rooms"
    def __unicode__(self):
        return "Room " + str(self.number)

class Crop(models.Model):
    startDate = models.DateField('date started')
    endDate = models.DateField('date completed', blank=True, null=True)
    room = models.ForeignKey(Room)
    class Meta:
        verbose_name_plural="Crops"
    def __unicode__(self):
        if(self.endDate == None):
            return "Crop " + str(self.id) + " (" + \
                str(self.startDate.day) + "/" + \
                str(self.startDate.month) + "/" + \
                str(self.startDate.year) + " - ) " + \
                str(self.room)
        else:
            return "Crop " + str(self.id) + " (" + \
                str(self.startDate.day) + "/" + \
                str(self.startDate.month) + "/" + \
                str(self.startDate.year) + " - " + \
                str(self.endDate.day) + "/" + \
                str(self.endDate.month) + "/" + \
                str(self.endDate.year) + ") " + \
                str(self.room)

class Flush(models.Model):
    startDate = models.DateField('date started')
    endDate = models.DateField('date completed', blank=True, null=True)
    flushNo = models.IntegerField()
    crop = models.ForeignKey(Crop, limit_choices_to = {'endDate__isnull':True})
    class Meta:
        verbose_name_plural="Flushes"
    def __unicode__(self):
        if(self.endDate == None):
            return "Flush " + str(self.flushNo) + " (" + \
                str(self.startDate.day) + "/" + \
                str(self.startDate.month) + "/" + \
                str(self.startDate.year) + " - ) " + \
                str(self.crop.room) + " ID " + str(self.id)
        else:
            return "Flush " + str(self.flushNo) + " (" + \
                str(self.startDate.day) + "/" + \
                str(self.startDate.month) + "/" + \
                str(self.startDate.year) + " - " + \
                str(self.endDate.day) + "/" + \
                str(self.endDate.month) + "/" + \
                str(self.endDate.year) + ") " + \
                str(self.crop.room) + " ID " + str(self.id)

class Batch(models.Model):
    date = models.DateField('date started')
    flush = models.ForeignKey(Flush, limit_choices_to = {'endDate__isnull':True})
    class Meta:
        verbose_name_plural="Batches"
    def __unicode__(self):
        return "Batch " + str(self.id) + " (" + \
                str(self.date.day) + "/" + \
                str(self.date.month) + "/" + \
                str(self.date.year) + ") " + \
                str(self.flush.crop.room)

class Mushroom(models.Model):
    variety = models.CharField(max_length=50)
    idealWeight = models.FloatField()
    tolerance = models.FloatField()
    active = models.BooleanField()
    class Meta:
        verbose_name_plural="Mushrooms"
    def __unicode__(self):
        return "Mushroom " + str(self.variety)

class Box(models.Model):
    initialWeight = models.FloatField()
    finalWeight = models.FloatField()
    timestamp = models.DateTimeField('time weighted')
    contentVariety = models.ForeignKey(Mushroom)
    picker = models.ForeignKey(Picker)
    batch = models.ForeignKey(Batch)
    class Meta:
        verbose_name_plural="Boxes"
    def __unicode__(self):
        return "Box " + str(self.id) + ", contains " + str(self.contentVariety) + " picked by " + str(self.picker)
