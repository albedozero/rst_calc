#!/usr/bin/env python

# Calculate the rise, transit, and set times at Winer Obs. for Sun or 
# user-specified source name on current day [default] or user-specified date

# RLM April 12 2008 - added sesame_resolve from KMI
# 13 Sept 2012 convert from pynova to pyephem, clean up code, add planets

import ephem as ep # pyephem library
from sys import argv
from urllib import quote, urlopen
from re import split as regex_split
import os.path
import wx

pi = 3.14159265359
deg = pi/180.

##### User-configurable stuff
DEFAULT_WIDTH  = 700		# app default width
DEFAULT_HEIGHT = 600		# app default height
# Set observer lat/long 
myloc  = ep.Observer()
myloc.lat = ep.degrees(str(0.55265/deg))
myloc.long = ep.degrees(str(-1.93035/deg))
#####

class SesameError(Exception): pass
class NameNotFoundError(Exception): pass

class MainWindow(wx.Frame):
	def __init__(self, filename='noname.txt'):
		super(MainWindow, self).__init__(None, size=(600,200))

### Make and place all the controls
		
		self.objectLabel = wx.StaticText(self, label="Object:")
		self.dateLabel = wx.StaticText(self, label="Date (MM/DD/YYYY):")
		self.object = wx.TextCtrl(self, -1,style=wx.TE_RIGHT|wx.TE_PROCESS_ENTER,size=wx.Size(250,22))
		self.date = wx.DatePickerCtrl(self, -1)
		self.submit = wx.Button(self, -1, "Search")
		self.output = wx.TextCtrl(self,style=wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_NOHIDESEL)
		(y, m, d) = ep.now().triple()
		self.date.SetValue(wx.DateTimeFromDMY(d, m-1, y))

		self.sizer_ctrl = wx.GridBagSizer(vgap=10, hgap=10)
		self.sizer_main = wx.BoxSizer(wx.VERTICAL)

		szflags=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL
		self.sizer_ctrl.Add(self.objectLabel, pos=(0,0), flag=szflags)
		self.sizer_ctrl.Add(self.object, pos=(0,1), span=(1,2), flag=wx.EXPAND|szflags)
		self.sizer_ctrl.Add(self.dateLabel, pos=(1,0), flag=szflags)
		self.sizer_ctrl.Add(self.date, pos=(1,1),flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL)
		self.sizer_ctrl.Add(self.submit, pos=(1,2), flag=szflags)

		self.sizer_main.Add(self.sizer_ctrl, border=5, flag=wx.EXPAND|wx.ALL)
		self.sizer_main.Add(self.output, proportion=1, flag=wx.EXPAND)

### Event Bindings
		self.object.Bind(wx.EVT_TEXT_ENTER, self.OnSubmit)
		self.submit.Bind(wx.EVT_BUTTON, self.OnSubmit)
		self.Bind(wx.EVT_CLOSE, self.OnQuit)

### Create Menus
		fileMenu = wx.Menu()
		item = fileMenu.Append(wx.ID_EXIT, '&Quit', 'Terminate the program')
		self.Bind(wx.EVT_MENU, self.OnQuit, item)

		helpMenu = wx.Menu()
		item = helpMenu.Append(wx.ID_ABOUT, '&About', 'Information about this program')
		self.Bind(wx.EVT_MENU, self.OnAbout, item)

		menuBar = wx.MenuBar()
#		menuBar.Append(fileMenu, '&File') # Mac OS X makes its own
		menuBar.Append(helpMenu, '&Help')
		self.SetMenuBar(menuBar)

		super(MainWindow, self).SetTitle('RST - Rise Set Time')
		self.CreateStatusBar()
		self.SetSizerAndFit(self.sizer_main)
		self.SetSize(size=wx.Size(DEFAULT_WIDTH,DEFAULT_HEIGHT))

	def OnAbout(self, event):
		description = \
""" Rise/Set Time Calculator is an astronomical
observation planning tool. Enter the name of
an object to produce an hour-by-hour table
of its elevation on the given date.

RST uses the SIMBAD astronomical database to
resolve object names and obtain positions.
The PyEphem libraray is used to calculate
ephemerides of solar system objects.
"""

		info = wx.AboutDialogInfo()
		
		info.SetName('RST Calculator')
		info.SetVersion('0.2')
		info.SetDescription(description)
		info.SetCopyright('(C) 2013 University of Iowa Physics and Astronomy')
		info.SetWebSite('http://astro.physics.uiowa.edu/rigel')
		info.AddDeveloper('Robert Mutel (robert-mutel@uiowa.edu)')
		info.AddDeveloper('Kevin Ivarsen (kivarsen@gmail.com)')
		info.AddDeveloper('Bill Peterson (bill.m.peterson@gmail.com)')
		
		wx.AboutBox(info)
		return

	def OnQuit(self, event):
		self.Destroy()
		
	def OnSubmit(self, event):
		searchtext = self.object.GetValue()
		if (searchtext == ''): return
		obsdate = str(self.date.GetValue().Format('%Y/%m/%d'))
		self.output.Clear()
		try:
			self.SetStatusText('Querying SIMBAD Server...')
			self.output.AppendText(calc_rst(searchtext,obsdate))
			self.output.ShowPosition(0)
		except NameNotFoundError:
			self.SetStatusText('Name not found by SIMBAD')
		except SesameError as e:
			self.SetStatusText('SIMBAD server error:', e)
		else:
			self.SetStatusText('')

# Nuts and Bolts

def sesame_resolve(name):  # This handy function from KMI
	url = "http://vizier.u-strasbg.fr/viz-bin/nph-sesame/-oI/SNV?"
	object = quote(name)
	ra = None
	dec = None
	identifiers = []
	try:
		simbad_lines = urlopen(url + object).readlines()
	except Exception, e:
		raise SesameError("Unable to connect to Sesame server", e)
	for line in simbad_lines:
		line = line.strip()
		if line.startswith("%J "):
			fields = regex_split(r" +", line)
			try:
				ra = float(fields[1])/15.0 # raises ValueError, IndexError
				dec = float(fields[2]) # raises ValueError, IndexError
			except (ValueError, IndexError), e:
				raise SesameError("Error parsing Sesame response", e)
		if line.startswith("%I "):
			fields = line.split(" ", 1)
			try:
				identifiers.append(fields[1]) # raises IndexError
			except IndexError, e:
				raise SesameError("Error parsing Sesame response", e)
	if ra == None or dec == None:
		raise NameNotFoundError("Name not found by Sesame server")
	return (ra, dec, identifiers)

def set_object(objname):
	if any(objname.lower() == planet for planet in planets):
		i = planets.index(objname.lower())
		obj = ep_planets[i]
		obj.compute(winer)
		objra = obj.ra; objdec = obj.dec
		ids = ''
	else:
		(rahr, decdeg, ids) = sesame_resolve(objname)
		objra = hr2hms(rahr); objdec = deg2dms(decdeg)
		db_str = '%s,f|M|x,%s,%s,0.0,2000' % (objname,objra,objdec)
		obj = ep.readdb(db_str); obj.compute(winer)
	return objra,objdec,ids, obj

def hr2hms(rahr):
	rahms = str(ep.hours(rahr*pi/12))
	return rahms
	   
def deg2dms(decdeg):
	decdms = str(ep.degrees(decdeg*pi/180.))
	return decdms
	
def get_times(t):
	myloc.date = t
	local =     str(ep.Date(myloc.date - 7*ep.hour)).split()[1][0:8]
	ut =        str(t).split()[1][0:8]
	lst =       str(myloc.sidereal_time()).split()[0][0:8]
	return local,ut,lst

def calc_rst(objname, ymd=""):
	if (ymd==''):
		myloc.date = ep.now()
	else:
		myloc.date = ymd

	# Define objname, objra, objdec, ids
	objra,objdec,ids,obj = set_object(objname)

	# Calculate JD and date strings
	jd_ep = float(ep.Date(myloc.date)); jd = jd_ep + 2415020
	(y, m, d) = myloc.date.triple()
	date_str = "%02d/%02d/%04d" % (m, d, y)

	# Calculate local times of astronomical dusk, dawn on specified date 
	sun = ep.Sun()
	myloc.horizon = twilight_elev
	sun.compute(winer)
	
	dawn = ep.Date(sun.rise_time - 7*ep.hour)
	(y, m, d) = dawn.triple()
	dawn_str = "%02d/%02d/%04d" % (m, d, y)
	
	dusk = ep.Date(sun.set_time - 7*ep.hour)
	(y, m, d) = dusk.triple()
	dusk_str = "%02d/%02d/%04d" % (m, d, y)

	out_str = 'Object = %s, Date: %s JD: %8.1f\n' % (objname, date_str,jd)
	out_str += 'RA(J2000): %s, Dec(J2000): %s\n\n' % (objra,objdec)
	out_str += 'Dusk, dawn: %s - %s MST\n\n' % (dusk_str, dawn_str)
	out_str += '  MST        UT        LST      Elevation\n'
	out_str += '-----------------------------------------\n' 

	# print hourly elevations and times when object is above min_elev and time is between dusk and dawn
	myloc.horizon = min_elev
	myloc.date = obj.rise_time
	nhr = 0 
	for n in range(0,24):
		obj.compute(winer)
		sun.compute(winer)
		eldeg = float(obj.alt)/deg
		elsun = float(sun.alt)/deg
		local,ut,lst = get_times(myloc.date)
		if eldeg > float(min_elev) and elsun < float(twilight_elev): 
			out_str += '%s   %s  %s      %4.1f\n' % (local, ut, lst, eldeg)
			nhr += 1
		myloc.date += ep.hour

	# Warnings:  if object is unobservable on requested date, or if transit occours during day
	if nhr == 0:
		out_str += '\nWarning: Object %s not observable between dusk and dawn on %s\n' % (objname, str(myloc.date).split()[0])
	else:
		out_str += '\n%s is observable for about %i hours on %s\n\n' % (objname, nhr, date_str)
		myloc.date = obj.transit_time
		sun.compute(winer); elsun = float(sun.alt)/deg
		if elsun > float(twilight_elev):
			t = str(ep.Date(myloc.date - 7*ep.hour)).split()[1][0:8]
			out_str += '\nWarning: Transit occurs during daytime (%s MST), use LSTSTART option when schedling' % t
	if ids != '':
		out_str += "\nSource also known as:"
		out_str += '; '.join(ids)
		out_str += '\n'
	return out_str

# MAIN

# List of planets (& Moon (& Pluto)) known to ephem
planets =    ['moon',    'mercury',   'venus',   'mars',     'jupiter',    'saturn',    'uranus',    'neptune',    'pluto']
ep_planets = [ep.Moon(), ep.Mercury(), ep.Venus(), ep.Mars(), ep.Jupiter(), ep.Saturn(), ep.Uranus(), ep.Neptune(), ep.Pluto()]


min_elev = '+10'        # Define minimum observable elevation in degrees
twilight_elev = '-12'  # Define solar elevation at astronomical twilight, when roof opens


app = wx.App(redirect=False)
frame = MainWindow()
frame.Show()
app.MainLoop()
