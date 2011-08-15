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
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    active = models.BooleanField()
    discharged = models.BooleanField()

    class Meta:
        verbose_name_plural = 'Pickers'

    def __unicode__(self):
        return u'Picker ({picker_id} {picker_fullname})'.format(
            picker_id = str(self.id), picker_fullname = self.full_name()
        )

    def full_name(self):
        """
        Returns the full name of this picker.
        """
        return '{first_name} {last_name}'.format(
            first_name = self.first_name, last_name = self.last_name
        )

    def get_avg_init_weight(self, date = None, end_date = None):
        """
        Return the average initial weight of boxes by this picker.

        If date is not given, it will return the average of initial weights
        for all boxes picked by this picker. If date is given but not
        end_date, the average of initial weights for the boxes collected on
        date will be returned. If both date and end_date are given, the average
        of initial weights for all boxes picked between date and end_date
        will be returned.
        """
        if date is None:
            avg = Box.objects.filter(picker=self).aggregate(
                    Avg('initial_weight'))['initial_weight__avg']
        elif end_date is None:
            avg = Box.objects.filter(picker=self, batch__date = date).aggregate(
                    Avg('initial_weight'))['initial_weight__avg']
        else:
            avg = Box.objects.filter(
                picker = self,
                batch__date__gte = date,
                batch__date__lte = end_date
            ).aggregate(Avg('initial_weight'))['initial_weight__avg']
        return avg if (avg is not None) else 0.0

    def get_total_picked(self, date = None, end_date = None):
        """
        Return the total weight of all boxes picked by this picker.

        If date is not given, it will return the total of initial weights
        for all boxes picked by this picker. If date is given but not
        end_date, the total of initial weights for the boxes collected on
        date will be returned. If both date and end_date are given, the total
        of initial weights for all boxes picked between date and end_date
        will be returned.
        """
        if date is None:
            total = Box.objects.filter(picker=self).aggregate(
                        Sum('initial_weight'))['initial_weight__sum']
        elif end_date is None:
            total = Box.objects.filter(picker=self, batch__date=date).aggregate(
                        Sum('initial_weight'))['initial_weight__sum']
        else:
            total = Box.objects.filter(
                picker = self,
                batch__date__gte = date,
                batch__date__lte = end_date
            ).aggregate(Sum('initial_weight'))['initial_weight__sum']
        return total if (total is not None) else 0.0

    def get_time_worked_on(self,date):
        """
        Return total time worked for picker on a given day.
        """
        bundies = Bundy.objects.filter(picker = self,
                                       time_in__startswith = date,
                                       time_out__isnull = False)
        if bundies is not None:
            return sum([b.time_worked() for b in bundies], datetime.timedelta())
        return 0.0
            
    def get_time_worked_between(self, start_date, end_date):
        """
        Return total timed worked for picker between two given dates
        """
        bundies = Bundy.objects.filter(
            picker = self,
            time_in__gte = start_date,
            time_in__lte = end_date + datetime.timedelta(days=1),
            time_out__isnull = False
        )
        if bundies is not None:
            return sum([b.time_worked() for b in bundies], datetime.timedelta())
        return 0.0
        
class Bundy(models.Model):
    picker=models.ForeignKey(Picker)
    time_in=models.DateTimeField('Time In')
    time_out=models.DateTimeField('Time Out', blank=True, null=True)
    had_lunch=models.BooleanField()
    lunch_break=datetime.timedelta(minutes=30)

    class Meta:
        verbose_name_plural = 'Bundies'

    def __unicode__(self):
        return 'Bundy ({picker_name}) ({time_in})'.format(
            picker_name = self.picker.full_name(),
            time_in = str(self.time_in)
        )

    def time_worked(self):
        """
        Returns the total amount of time worked as a timedelta.
        """
        return (self.time_out - self.time_in-self.lunch_break if self.had_lunch
                else self.time_out-self.time_in)

class Room(models.Model):
    number = models.IntegerField()
    status = models.CharField(max_length=50)

    class Meta:
        verbose_name_plural = 'Rooms'

    def __unicode__(self):
        return 'Room {}'.format(str(self.number))

    def get_total_picked_on(self, date): 
        """
        Return total picked for this room on a given date.
        """
        total = Box.objects.filter(batch__flush__crop__room = self,
                                   batch__date = date).aggregate(
                                   Sum('initial_weight'))['initial_weight__sum']
        return total if (total is not None) else 0.0

    def get_total_picked_between(self, start_date, end_date): 
        """
        Return total picked for a picker, between two given dates given date
        """
        total = Box.objects.filter(batch__flush__crop__room = self,
                                   batch__date__gte = start_date, 
                                   batch__date__lte = end_date).aggregate(
                                   Sum('initial_weight'))['initial_weight__sum']
        return total if (total is not None) else 0.0

class Crop(models.Model):
    start_date = models.DateField('date started')
    end_date = models.DateField('date completed', blank = True, null = True)
    room = models.ForeignKey(Room)

    class Meta:
        verbose_name_plural = 'Crops'

    def __unicode__(self):
        return 'Crop {crop_id} ({start_date} ~ {end_date}) {room}'.format(
            crop_id = str(self.id),
            start_date = self.date_string(),
            end_date = self.date_string(start = False),
            room = str(self.room)
        )

    def date_string(self, start = True):
        """
        Returns start_date or end_date as a string day/month/year.

        If start is True (the default) then start_date will be returned,
        otherwise end_date will be returned.
        """
        date_format = '{day}/{month}/{year}'
        if start:
            return date_format.format(day =   str(self.start_date.day),
                                      month = str(self.start_date.month),
                                      year =  str(self.start_date.year))
        else:
            return date_format.format(day =   str(self.end_date.day),
                                      month = str(self.end_date.month),
                                      year =  str(self.end_date.year))

    def get_total_picked_on(self, date): 
        """
        Return total picked for this cop on a given date.
        """
        total = Box.objects.filter(batch__flush__crop = self,
                                   batch__date = date).aggregate(
                                   Sum('initial_weight'))['initial_weight__sum']
        return total if (total is not None) else 0.0

    def get_total_picked_between(self, start_date, end_date): 
        """
        Return total picked for a picker, between two given dates given date.
        """
        total = Box.objects.filter(batch__flush__crop = self,
                                   batch__date__gte = start_date, 
                                   batch__date__lte = end_date).aggregate(
                                   Sum('initial_weight'))['initial_weight__sum']
        return total if (total is not None) else 0.0

class Flush(models.Model):
    start_date = models.DateField('date started')
    end_date = models.DateField('date completed', blank = True, null = True)
    flush_no = models.IntegerField()
    crop = models.ForeignKey(Crop, limit_choices_to = {'end_date__isnull':True})

    class Meta:
        verbose_name_plural = 'Flushes'

    def __unicode__(self):
        if self.end_date is None:
            end_date_string = 'unfinished'
        else:
            end_date_string = self.date_string(start = False)
        return ('Flush {flush_no} ({start_date} ~ {end_date}) ' +\
               '{room} ID {flush_id}').format(
            flush_no = self.flush_no,
            start_date = self.date_string(),
            end_date = end_date_string,
            room = str(self.crop.room),
            flush_id = self.id
        )

    def date_string(self, start = True):
        """
        Returns start_date or end_date as a string day/month/year.

        If start is True (the default) then start_date will be returned,
        otherwise end_date will be returned.
        """
        date_format = '{day}/{month}/{year}'
        if start:
            return date_format.format(day =   str(self.start_date.day),
                                      month = str(self.start_date.month),
                                      year =  str(self.start_date.year))
        else:
            return date_format.format(day =   str(self.end_date.day),
                                      month = str(self.end_date.month),
                                      year =  str(self.end_date.year))

    def get_total_picked_on(self, date): 
        """
        Return total picked for this flush on a given date.
        """
        total = Box.objects.filter(batch__flush = self,
                                   batch__date = date).aggregate(
                                   Sum('initial_weight'))['initial_weight__sum']
        return total if (total is not None) else 0.0

    def get_total_picked_between(self, start_date, end_date): 
        """
        Return total picked for this flush between two given dates.
        """
        total = Box.objects.filter(batch__flush = self,
                                   batch__date__gte = start_date, 
                                   batch__date__lte = end_date).aggregate(
                                   Sum('initial_weight'))['initial_weight__sum']
        return total if (total is not None) else 0.0

class Batch(models.Model):
    date = models.DateField('date started')
    flush = models.ForeignKey(Flush,
                              limit_choices_to = {'end_date__isnull': True})

    class Meta:
        verbose_name_plural = 'Batches'

    def __unicode__(self):
        return 'Batch {batch_id} ({batch_date}) {room}'.format(
            batch_id = str(self.id),
            batch_date = self.date_string(),
            room = str(self.flush.crop.room)
        )

    def date_string(self):
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
    minimum_weight = models.FloatField()
    tolerance = models.FloatField()
    active = models.BooleanField()

    class Meta:
        verbose_name_plural = 'Varieties'

    def __unicode__(self):
        return 'Variety {name}'.format(
            name = str(self.name)
        )

class Box(models.Model):
    initial_weight = models.FloatField()
    final_weight = models.FloatField()
    timestamp = models.DateTimeField('time weighted')
    variety = models.ForeignKey(Variety)
    picker = models.ForeignKey(Picker)
    batch = models.ForeignKey(Batch)

    class Meta:
        verbose_name_plural = 'Boxes'

    def __unicode__(self):
        return 'Box {box_id} contains {variety} picked by {picker}'.format(
            box_id = str(self.id),
            variety = str(self.variety),
            picker = str(self.picker)
        )
