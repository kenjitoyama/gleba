"""
Copyright (C) 2010-2011 Simon Dawson, Meryl Baquiran, Chris Ellis
and Daniel Kenji Toyama 

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
    gleba.glebaAdmin.admin

Purpose:
    This module provides some customizations to the default Django admin page.
"""
from gleba.glebaAdmin.models import Picker
from gleba.glebaAdmin.models import Room
from gleba.glebaAdmin.models import Crop
from gleba.glebaAdmin.models import Flush
from gleba.glebaAdmin.models import Batch
from gleba.glebaAdmin.models import Variety
from gleba.glebaAdmin.models import Box
from gleba.glebaAdmin.models import Bundy
from django.contrib import admin

class PickerAdmin(admin.ModelAdmin):
    list_display = ('firstName', 'lastName', 'active', 'discharged')
    list_filter = ('firstName', 'lastName', 'active', 'discharged')
    search_fields = ['firstName', 'lastName', 'id']
    fieldsets = [
        ('First Name', {'fields': ['firstName']}),
        ('Last Name',  {'fields': ['lastName']}),
        ('Is the picker active?',  {'fields': ['active']}),
        ('Is the picker discharged?',  {'fields': ['discharged']}),
    ]

class RoomAdmin(admin.ModelAdmin):
    list_filter = ('number', 'status')
    search_fields = ['number']
    fieldsets = [
        ('Number',  {'fields': ['number']}),
        ('Status',  {'fields': ['status']}),
    ]

class CropAdmin(admin.ModelAdmin):
    date_hierarchy = 'startDate'
    list_display = ('startDate', 'endDate', 'room')
    list_filter = ('startDate', 'endDate', 'room')
    search_fields = ['id', 'room__number']
    fieldsets = [
        ('Start Date',  {'fields': ['startDate']}),
        ('End Date',  {'fields': ['endDate']}),
        ('Room',  {'fields': ['room']}),
    ]

class FlushAdmin(admin.ModelAdmin):
    date_hierarchy = 'startDate'     
    list_display = ('startDate', 'endDate', 'flushNo', 'crop')
    list_filter = ('startDate', 'endDate', 'flushNo', 'crop')
    search_fields = ['crop__id', 'flushNo']
    fieldsets = [
        ('Start Date',  {'fields': ['startDate']}),
        ('End Date',  {'fields': ['endDate']}),
        ('Flush Number',  {'fields': ['flushNo']}),
        ('Crop',  {'fields': ['crop']}),
    ]

class BatchAdmin(admin.ModelAdmin):
    list_display = ('date', 'flush')
    list_filter = ('date', 'flush')
    date_hierarchy = 'date'
    search_fields = ['id', 'flush__flushNo']
    fieldsets = [
        ('Date',  {'fields': ['date']}),
        ('Flush Number',  {'fields': ['flush']}),
    ]

class VarietyAdmin(admin.ModelAdmin):
    list_display = ('name', 'active')
    list_filter = ('name', 'active')
    search_fields = ['id', 'name']
    fieldsets = [
        ('Name',  {'fields': ['name']}),
        ('Is it still being picked?',  {'fields': ['active']}),
        ('Ideal weight for this variety', {'fields': ['idealWeight']}),
        ('Tolerance from the ideal weight in kg', {'fields': ['tolerance']}),
    ]

class BoxAdmin(admin.ModelAdmin):
    list_display = ('contentVariety', 'batch', 'picker','initialWeight','finalWeight')
    list_filter = ('contentVariety', 'batch', 'picker')
    search_fields = ['id', 'contentVariety__variety', 'picker__id', 'picker__firstName', 'picker__lastName']
    fieldsets = [
        ('Initial weight',  {'fields': ['initialWeight']}),
        ('Final weight',  {'fields': ['finalWeight']}),
        ('Variety',  {'fields': ['contentVariety']}),
        ('Timestamp',  {'fields': ['timestamp']}),
        ('Picker',  {'fields': ['picker']}),
        ('Batch',  {'fields': ['batch']}),
    ]

class BundyAdmin(admin.ModelAdmin):
    list_display = ('timeIn', 'timeOut', 'picker', 'hadLunch')
    list_filter = ('timeIn', 'timeOut', 'picker', 'hadLunch')
    search_fields = ['picker__id', 'picker__firstName', 'picker__lastName']
    fieldsets = [
        ('Time In', {'fields': ['timeIn']}),
        ('Time Out', {'fields': ['timeOut']}),
        ('Picker',  {'fields': ['picker']}),
        ('Had Lunch', {'fields': ['hadLunch']}),
    ]



admin.site.register(Picker, PickerAdmin)
admin.site.register(Room, RoomAdmin)
admin.site.register(Crop, CropAdmin)
admin.site.register(Flush, FlushAdmin)
admin.site.register(Batch, BatchAdmin)
admin.site.register(Variety, VarietyAdmin)
admin.site.register(Box, BoxAdmin)
admin.site.register(Bundy, BundyAdmin)
