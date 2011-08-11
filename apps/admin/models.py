"""
Copyright (C) Simon Dawson, Kenji Toyama, Meryl Baquiran, Chris Ellis 2010-2011
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

Author(s):
    Simon Dawson
    Daniel Kenji Toyama

Path: 
    apps.admin.models

Purpose:
    This module contains the data models of Gleba.
"""
from django.db import models
from django.db.models import Avg, Sum, Min, Max
import datetime

class Picker(models.Model):
    firstName = models.CharField(max_length=50)
    lastName = models.CharField(max_length=50)
    active = models.BooleanField()
    discharged = models.BooleanField()

    class Meta:
        verbose_name_plural = 'Pickers'

    def __unicode__(self):
        return u'Picker ({picker_id} {picker_fullname})'.format(
            picker_id = str(self.id), picker_fullname = self.fullName()
        )

    def fullName(self):
        """
        Returns the full name of this picker.
        """
        return '{first_name} {last_name}'.format(
            first_name = self.firstName, last_name = self.lastName
        )

    def getAvgInitWeight(self):
        """
        Return the average initial weight of boxes picker by picker.
        """
        avg = Box.objects.filter(picker=self).aggregate(
                Avg('initialWeight'))['initialWeight__avg']
        return avg if (avg is not None) else 0.0

    def getAvgInitWeightOn(self, date):
        """
        Return the average initial weight of boxes picker by picker on date.
        """
        avg = Box.objects.filter(picker=self, batch__date=date).aggregate(
                Avg('initialWeight'))['initialWeight__avg']
        return avg if (avg is not None) else 0.0

    def getAvgInitWeightBetween(self, start_date, end_date):
        """
        Return the average initial weight of boxes picker by picker.
        """
        avg = Box.objects.filter(picker=self,
                                 batch__date__gte = start_date,
                                 batch__date__lte = end_date).aggregate(
                                 Avg('initialWeight'))['initialWeight__avg']
        return avg if (avg is not None) else 0.0

    def getTotalPicked(self):
        """
        Return total picked for a picker forever.
        """
        total = Box.objects.filter(picker=self).aggregate(
                    Sum('initialWeight'))['initialWeight__sum']
        return total if (total is not None) else 0.0

    def getTotalPickedOn(self, date): 
        """
        Return total picked for a picker forever, on a given date.
        """
        total = Box.objects.filter(picker=self, batch__date=date).aggregate(
                    Sum('initialWeight'))['initialWeight__sum']
        return total if (total is not None) else 0.0

    def getTotalPickedBetween(self, start_date, end_date): 
        """
        Return total picked for a picker, between two given dates given date.
        """
        total = Box.objects.filter(picker = self,
                                   batch__date__gte = start_date,
                                   batch__date__lte = end_date).aggregate(
                                   Sum('initialWeight'))['initialWeight__sum']
        return total if (total is not None) else 0.0

    def getTimeWorkedOn(self,date):
        """
        Return total time worked for picker on a given day.
        """
        bundies = Bundy.objects.filter(picker = self,
                                       timeIn__startswith = date,
                                       timeOut__isnull = False)
        if bundies is not None:
            return sum([b.timeWorked() for b in bundies], datetime.timedelta())
        return 0.0
            
    def getTimeWorkedBetween(self, start_date, end_date):
        """
        Return total timed worked for picker between two given dates
        """
        bundies = Bundy.objects.filter(
            picker = self,
            timeIn__gte = start_date,
            timeIn__lte = end_date + datetime.timedelta(days=1),
            timeOut__isnull = False
        )
        if bundies is not None:
            return sum([b.timeWorked() for b in bundies], datetime.timedelta())
        return 0.0
        
class Bundy(models.Model):
    picker=models.ForeignKey(Picker)
    timeIn=models.DateTimeField('Time In')
    timeOut=models.DateTimeField('Time Out', blank=True, null=True)
    hadLunch=models.BooleanField()

    lunchBreak=datetime.timedelta(minutes=30)

    class Meta:
        verbose_name_plural = 'Bundies'

    def __unicode__(self):
        return 'Bundy ({picker_name}) ({time_in})'.format(
            picker_name = self.picker.fullName(),
            time_in = str(self.timeIn)
        )

    def timeWorked(self):
        """
        Returns the amount of time worked as a timedelta" 
        """
        return (self.timeOut - self.timeIn-self.lunchBreak if self.hadLunch
                else self.timeOut-self.timeIn)

class Room(models.Model):
    number = models.IntegerField()
    status = models.CharField(max_length=50)

    class Meta:
        verbose_name_plural = 'Rooms'

    def __unicode__(self):
        return 'Room {}'.format(str(self.number))

    def getTotalPickedOn(self, date): 
        """
        Return total picked for this room on a given date.
        """
        total = Box.objects.filter(batch__flush__crop__room = self,
                                   batch__date = date).aggregate(
                                   Sum('initialWeight'))['initialWeight__sum']
        return total if (total is not None) else 0.0

    def getTotalPickedBetween(self, start_date, end_date): 
        """
        Return total picked for a picker, between two given dates given date
        """
        total = Box.objects.filter(batch__flush__crop__room = self,
                                   batch__date__gte = start_date, 
                                   batch__date__lte = end_date).aggregate(
                                   Sum('initialWeight'))['initialWeight__sum']
        return total if (total is not None) else 0.0

class Crop(models.Model):
    startDate = models.DateField('date started')
    endDate = models.DateField('date completed', blank = True, null = True)
    room = models.ForeignKey(Room)

    class Meta:
        verbose_name_plural = 'Crops'

    def __unicode__(self):
        return 'Crop {crop_id} ({start_date} ~ {end_date}) {room}'.format(
            crop_id = str(self.id),
            start_date = self.dateString(),
            end_date = self.dateString(start = False),
            room = str(self.room)
        )

    def dateString(self, start = True):
        """
        Returns startDate or endDate as a string day/month/year.

        If start is True (the default) then startDate will be returned,
        otherwise endDate will be returned.
        """
        date_format = '{day}/{month}/{year}'
        if start:
            return date_format.format(day =   str(self.startDate.day),
                                      month = str(self.startDate.month),
                                      year =  str(self.startDate.year))
        else:
            return date_format.format(day =   str(self.endDate.day),
                                      month = str(self.endDate.month),
                                      year =  str(self.endDate.year))

    def getTotalPickedOn(self, date): 
        """
        Return total picked for this cop on a given date.
        """
        total = Box.objects.filter(batch__flush__crop = self,
                                   batch__date = date).aggregate(
                                   Sum('initialWeight'))['initialWeight__sum']
        return total if (total is not None) else 0.0

    def getTotalPickedBetween(self, start_date, end_date): 
        """
        Return total picked for a picker, between two given dates given date.
        """
        total = Box.objects.filter(batch__flush__crop = self,
                                   batch__date__gte = start_date, 
                                   batch__date__lte = end_date).aggregate(
                                   Sum('initialWeight'))['initialWeight__sum']
        return total if (total is not None) else 0.0

class Flush(models.Model):
    startDate = models.DateField('date started')
    endDate = models.DateField('date completed', blank = True, null = True)
    flushNo = models.IntegerField()
    crop = models.ForeignKey(Crop, limit_choices_to = {'endDate__isnull':True})

    class Meta:
        verbose_name_plural = 'Flushes'

    def __unicode__(self):
        if self.endDate is None:
            end_date_string = 'unfinished'
        else:
            end_date_string = self.dateString(start = False)
        return ('Flush {flush_no} ({start_date} ~ {end_date}) ' +\
               '{room} ID {flush_id}').format(
            flush_no = self.flushNo,
            start_date = self.dateString(),
            end_date = end_date_string,
            room = str(self.crop.room),
            flush_id = self.id
        )

    def dateString(self, start = True):
        """
        Returns startDate or endDate as a string day/month/year.

        If start is True (the default) then startDate will be returned,
        otherwise endDate will be returned.
        """
        date_format = '{day}/{month}/{year}'
        if start:
            return date_format.format(day =   str(self.startDate.day),
                                      month = str(self.startDate.month),
                                      year =  str(self.startDate.year))
        else:
            return date_format.format(day =   str(self.endDate.day),
                                      month = str(self.endDate.month),
                                      year =  str(self.endDate.year))

    def getTotalPickedOn(self, date): 
        """
        Return total picked for this flush on a given date.
        """
        total = Box.objects.filter(batch__flush = self,
                                   batch__date = date).aggregate(
                                   Sum('initialWeight'))['initialWeight__sum']
        return total if (total is not None) else 0.0

    def getTotalPickedBetween(self, start_date, end_date): 
        """
        Return total picked for this flush between two given dates.
        """
        total = Box.objects.filter(batch__flush = self,
                                   batch__date__gte = start_date, 
                                   batch__date__lte = end_date).aggregate(
                                   Sum('initialWeight'))['initialWeight__sum']
        return total if (total is not None) else 0.0

class Batch(models.Model):
    date = models.DateField('date started')
    flush = models.ForeignKey(Flush,
                              limit_choices_to = {'endDate__isnull': True})

    class Meta:
        verbose_name_plural = 'Batches'

    def __unicode__(self):
        return 'Batch {batch_id} ({batch_date}) {room}'.format(
            batch_id = str(self.id),
            batch_date = self.dateString(),
            room = str(self.flush.crop.room)
        )

    def dateString(self):
        """
        Returns date as a string day/month/year.
        """
        return '{day}/{month}/{year}'.format(
            day =   str(self.date.day),
            month = str(self.date.month),
            year =  str(self.date.year)
        )

class Variety(models.Model):
    name = models.CharField(max_length=50)
    idealWeight = models.FloatField()
    tolerance = models.FloatField()
    active = models.BooleanField()

    class Meta:
        verbose_name_plural = 'Varieties'

    def __unicode__(self):
        return 'Variety {name}'.format(
            name = str(self.name)
        )

class Box(models.Model):
    initialWeight = models.FloatField()
    finalWeight = models.FloatField()
    timestamp = models.DateTimeField('time weighted')
    contentVariety = models.ForeignKey(Variety)
    picker = models.ForeignKey(Picker)
    batch = models.ForeignKey(Batch)

    class Meta:
        verbose_name_plural = 'Boxes'

    def __unicode__(self):
        return 'Box {box_id} contains {variety} picked by {picker}'.format(
            box_id = str(self.id),
            variety = str(self.contentVariety),
            picker = str(self.picker)
        )
