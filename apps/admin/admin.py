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
    apps.admin.admin

Purpose:
    This module provides some customizations to the default Django admin page.
"""
from apps.admin.models import Picker
from apps.admin.models import Room
from apps.admin.models import Crop
from apps.admin.models import Flush
from apps.admin.models import Batch
from apps.admin.models import Variety
from apps.admin.models import Box
from apps.admin.models import Bundy
from django.contrib import admin

class PickerAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'active', 'discharged')
    list_filter = ('first_name', 'last_name', 'active', 'discharged')
    search_fields = ['first_name', 'last_name', 'id']
    fieldsets = [
        ('First Name', {'fields': ['first_name']}),
        ('Last Name',  {'fields': ['last_name']}),
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
    date_hierarchy = 'start_date'
    list_display = ('start_date', 'end_date', 'room')
    list_filter = ('start_date', 'end_date', 'room')
    search_fields = ['id', 'room__number']
    fieldsets = [
        ('Start Date',  {'fields': ['start_date']}),
        ('End Date',  {'fields': ['end_date']}),
        ('Room',  {'fields': ['room']}),
    ]

class FlushAdmin(admin.ModelAdmin):
    date_hierarchy = 'start_date'     
    list_display = ('start_date', 'end_date', 'flush_no', 'crop')
    list_filter = ('start_date', 'end_date', 'flush_no', 'crop')
    search_fields = ['crop__id', 'flush_no']
    fieldsets = [
        ('Start Date',  {'fields': ['start_date']}),
        ('End Date',  {'fields': ['end_date']}),
        ('Flush Number',  {'fields': ['flush_no']}),
        ('Crop',  {'fields': ['crop']}),
    ]

class BatchAdmin(admin.ModelAdmin):
    list_display = ('date', 'flush')
    list_filter = ('date', 'flush')
    date_hierarchy = 'date'
    search_fields = ['id', 'flush__flush_no']
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
        ('Ideal weight for this variety', {'fields': ['minimum_weight']}),
        ('Tolerance from the minimum weight in kg', {'fields': ['tolerance']}),
    ]

class BoxAdmin(admin.ModelAdmin):
    list_display = ('variety', 'batch', 'picker','initial_weight','final_weight')
    list_filter = ('variety', 'batch', 'picker')
    search_fields = ['id', 'variety__variety', 'picker__id', 'picker__first_name', 'picker__last_name']
    fieldsets = [
        ('Initial weight',  {'fields': ['initial_weight']}),
        ('Final weight',  {'fields': ['final_weight']}),
        ('Variety',  {'fields': ['variety']}),
        ('Timestamp',  {'fields': ['timestamp']}),
        ('Picker',  {'fields': ['picker']}),
        ('Batch',  {'fields': ['batch']}),
    ]

class BundyAdmin(admin.ModelAdmin):
    list_display = ('time_in', 'time_out', 'picker', 'had_lunch')
    list_filter = ('time_in', 'time_out', 'picker', 'had_lunch')
    search_fields = ['picker__id', 'picker__first_name', 'picker__last_name']
    fieldsets = [
        ('Time In', {'fields': ['time_in']}),
        ('Time Out', {'fields': ['time_out']}),
        ('Picker',  {'fields': ['picker']}),
        ('Had Lunch', {'fields': ['had_lunch']}),
    ]



admin.site.register(Picker, PickerAdmin)
admin.site.register(Room, RoomAdmin)
admin.site.register(Crop, CropAdmin)
admin.site.register(Flush, FlushAdmin)
admin.site.register(Batch, BatchAdmin)
admin.site.register(Variety, VarietyAdmin)
admin.site.register(Box, BoxAdmin)
admin.site.register(Bundy, BundyAdmin)
