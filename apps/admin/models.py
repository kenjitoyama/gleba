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
    apps.admin.models

Purpose:
    This module contains the data models of Gleba.
"""
import datetime
from django.db import models
from django.db.models import Avg, Sum, Min, Max

class Picker(models.Model):
    first_name = models.CharField(max_length = 50)
    last_name = models.CharField(max_length = 50)
    active = models.BooleanField()
    discharged = models.BooleanField()

    class Meta:
        verbose_name_plural = 'Pickers'

    def __unicode__(self):
        return u'Picker ({picker_id} {picker_fullname})'.format(
            picker_id = str(self.id),
            picker_fullname = self.full_name()
        )

    def full_name(self):
        """
        Returns the full name of this picker.
        """
        return '{first_name} {last_name}'.format(
            first_name = self.first_name,
            last_name = self.last_name
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
            avg = Box.objects.filter(
                picker = self
            ).aggregate(Avg('initial_weight'))['initial_weight__avg']
        elif end_date is None:
            avg = Box.objects.filter(
                picker = self,
                batch__date = date
            ).aggregate(Avg('initial_weight'))['initial_weight__avg']
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

        Note: date is relative to the batch date, and not to the date that
        the box was weighed.
        """
        if date is None:
            total = Box.objects.filter(
                picker = self
            ).aggregate(Sum('initial_weight'))['initial_weight__sum']
        elif end_date is None:
            total = Box.objects.filter(
                picker = self,
                batch__date = date
            ).aggregate(Sum('initial_weight'))['initial_weight__sum']
        else:
            total = Box.objects.filter(
                picker = self,
                batch__date__gte = date,
                batch__date__lte = end_date
            ).aggregate(Sum('initial_weight'))['initial_weight__sum']
        return total if (total is not None) else 0.0

    def get_daily_totals(self, start_date, end_date):
        """
        Returns a list of all boxes picked between start_date and end_date.
        """
        return Box.objects.filter(
            picker = self,
            batch__date__gte = start_date,
            batch__date__lte = end_date
        )

    def get_daily_hours(self, start_date, end_date):
        """
        Returns a list of all bundies between start_date and end_date.
        """
        return Bundy.objects.filter(
            picker = self,
            time_in__gte = start_date,
            time_in__lte = end_date,
            time_out__isnull = False
        )

    def get_time_worked(self, date, end_date = None):
        """
        Return total time worked that this picker has worked.

        If end_date is not given, then the total time that this picker has
        worked on date will be returned, otherwise the total time between
        date and end_date will be returned.
        """
        if end_date is None:
            bundies = Bundy.objects.filter(
                picker = self,
                time_in__startswith = date,
                time_out__isnull = False
            )
        else:
            bundies = Bundy.objects.filter(
                picker = self,
                time_in__gte = date,
                time_in__lte = end_date + datetime.timedelta(days = 1),
                time_out__isnull = False
            )
        if bundies is not None:
            return sum([b.time_worked() for b in bundies],
                        datetime.timedelta())
        return 0.0
            
class Bundy(models.Model):
    picker = models.ForeignKey(Picker)
    time_in = models.DateTimeField('Time In')
    time_out = models.DateTimeField('Time Out', blank = True, null = True)
    had_lunch = models.BooleanField()
    lunch_break = datetime.timedelta(minutes = 30)

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
        return (self.time_out - self.time_in-self.lunch_break
                if self.had_lunch
                else self.time_out-self.time_in)

class Room(models.Model):
    number = models.IntegerField()
    status = models.CharField(max_length = 50)

    class Meta:
        verbose_name_plural = 'Rooms'

    def __unicode__(self):
        return 'Room {}'.format(str(self.number))

    def get_total_picked(self, date, end_date = None):
        """
        Return total picked for this room on a given date.

        If end_date is not given, then the total picked for this room
        will be returned, otherwise the total picked between date and
        end_date will be returned.
        """
        if end_date is None:
            total = Box.objects.filter(
                batch__flush__crop__room = self,
                batch__date = date
            ).aggregate(Sum('initial_weight'))['initial_weight__sum']
        else:
            total = Box.objects.filter(
                batch__flush__crop__room = self,
                batch__date__gte = date,
                batch__date__lte = end_date
            ).aggregate(Sum('initial_weight'))['initial_weight__sum']
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
        date_format = '{year}-{month}-{day}'
        date = self.end_date
        if start:
            date = self.start_date
        return date_format.format(
            day =   str(date.day),
            month = str(date.month),
            year =  str(date.year)
        )

    def get_total_picked(self, date, end_date = None):
        """
        Return total picked for this cop on a given date.

        If end_date is not given, then the total picked for this crop
        will be returned, otherwise the total picked between date and
        end_date will be returned.
        """
        if end_date is None:
            total = Box.objects.filter(
                batch__flush__crop = self,
                batch__date = date
            ).aggregate(Sum('initial_weight'))['initial_weight__sum']
        else:
            total = Box.objects.filter(
                batch__flush__crop = self,
                batch__date__gte = date,
                batch__date__lte = end_date
            ).aggregate(Sum('initial_weight'))['initial_weight__sum']
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
        date_format = '{year}-{month}-{day}'
        date = self.end_date
        if start:
            date = self.start_date
        return date_format.format(
            day =   str(date.day),
            month = str(date.month),
            year =  str(date.year)
        )

    def get_total_picked(self, date, end_date = None):
        """
        Return total picked for this flush on a given date.

        If end_date is not given, then the total picked for this flush
        will be returned, otherwise the total picked between date and
        end_date will be returned.
        """
        if end_date is None:
            total = Box.objects.filter(
                batch__flush = self,
                batch__date = date
            ).aggregate(Sum('initial_weight'))['initial_weight__sum']
        else:
            total = Box.objects.filter(
                batch__flush = self,
                batch__date__gte = date,
                batch__date__lte = end_date
            ).aggregate(Sum('initial_weight'))['initial_weight__sum']
        return total if (total is not None) else 0.0

class Batch(models.Model):
    date = models.DateField('date started')
    flush = models.ForeignKey(
        Flush,
        limit_choices_to = {'end_date__isnull': True}
    )

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
        return '{year}-{month}-{day}'.format(
            day =   str(self.date.day),
            month = str(self.date.month),
            year =  str(self.date.year)
        )

class Variety(models.Model):
    name = models.CharField(max_length = 50)
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
