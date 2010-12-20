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
        return "Picker "  + str(self.id)  + ' ' +  self.fullName()
    def fullName(self):
        "Returns the full name of this picker"
        return self.firstName + ' ' + self.lastName

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
        return "Crop "  + str(self.id) + " (" +\
               self.startDateString() +  " - " +\
               self.endDateString() + ") " +\
               str(self.room)
    def startDateString(self):
        "Returns startDate as a string day/month/year"
        return  str(self.startDate.day) + "/" + \
                str(self.startDate.month) + "/" + \
                str(self.startDate.year)
    def endDateString(self):
        "Returns endDate as a string day/month/year"
        if self.endDate is None:
            return ''
        else:
            return  str(self.endDate.day) + "/" + \
                    str(self.endDate.month) + "/" + \
                    str(self.endDate.year)

class Flush(models.Model):
    startDate = models.DateField('date started')
    endDate = models.DateField('date completed', blank=True, null=True)
    flushNo = models.IntegerField()
    crop = models.ForeignKey(Crop, limit_choices_to = {'endDate__isnull':True})
    class Meta:
        verbose_name_plural="Flushes"
    def __unicode__(self):
        return "Flush " + str(self.flushNo) + " (" + \
            self.startDateString() + " - " +\
            self.endDateString() + ") " +\
            str(self.crop.room) + " ID " + str(self.id)
    def startDateString(self):
        "Returns startDate as a string day/month/year"
        return  str(self.startDate.day) + "/" + \
                str(self.startDate.month) + "/" + \
                str(self.startDate.year)
    def endDateString(self):
        "Returns endDate as a string day/month/year"
        if self.endDate is None:
            return ''
        else:
            return  str(self.endDate.day) + "/" + \
                    str(self.endDate.month) + "/" + \
                    str(self.endDate.year)

class Batch(models.Model):
    date = models.DateField('date started')
    flush = models.ForeignKey(Flush, limit_choices_to = {'endDate__isnull':True})
    class Meta:
        verbose_name_plural="Batches"
    def __unicode__(self):
        return "Batch " + str(self.id) + " (" + \
                self.dateString() + ") " +\
                str(self.flush.crop.room)
    def dateString(self):
        "Returns date as a string day/month/year"
        return  str(self.date.day) + "/" + \
                str(self.date.month) + "/" + \
                str(self.date.year)

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
