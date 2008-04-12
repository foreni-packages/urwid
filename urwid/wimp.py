#!/usr/bin/python
#
# Urwid Window-Icon-Menu-Pointer-style widget classes
#    Copyright (C) 2004-2008  Ian Ward
#
#    This library is free software; you can redistribute it and/or
#    modify it under the terms of the GNU Lesser General Public
#    License as published by the Free Software Foundation; either
#    version 2.1 of the License, or (at your option) any later version.
#
#    This library is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with this library; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# Urwid web site: http://excess.org/urwid/

from widget import *
from container import *
from command_map import command_map


class SelectableIcon(Text):
	_selectable = True
	
	def render(self, size, focus=False):
		"""
		Render the text content of this widget with a cursor at
		position (1,0) when in focus.

		>>> si = SelectableIcon("[!]")
		>>> si
		<SelectableIcon selectable flow widget '[!]'>
		>>> si.render((4,),focus=True).cursor
		(1,0)
		"""
		(maxcol,) = size
		c = Text.render(self, (maxcol,), focus )
		if focus:
			c = CompositeCanvas(c)
			c.cursor = self.get_cursor_coords((maxcol,))
		return c
	
	def get_cursor_coords(self, size):
		"""
		Return the position of the cursor if visible.  This method
		is required for widgets that display a cursor.
		"""
		(maxcol,) = size
		if maxcol>1:
			return (1,0)

	def keypress(self, size, key):
		"""
		No keys are handled by this widget.  This method is
		required for selectable widgets.
		"""
		return key

class CheckBoxError(Exception):
	pass

class CheckBox(WidgetWrap):
	states = { 
		True: SelectableIcon("[X]"),
		False: SelectableIcon("[ ]"),
		'mixed': SelectableIcon("[#]") }
	reserve_columns = 4

	# allow users of this class to listen for change events
	# sent when the state of this widget is modified
	# (this variable is picked up by the MetaSignals metaclass)
	signals = ["change"]
	
	def __init__(self, label, state=False, has_mixed=False,
		     on_state_change=None, user_data=None):
		"""
		label -- markup for check box label
		state -- False, True or "mixed"
		has_mixed -- True if "mixed" is a state to cycle through
		on_state_change, user_data -- shorthand for connect_signal()
			function call for a single callback
		
		Signals supported: 'change'
		Register signal handler with:
		  connect_signal(check_box, 'change', callback [,user_data])
		where signal is signal(check_box, new_state [,user_data])
		Unregister signal handlers with:
		  disconnect_signal(check_box, 'change', callback [,user_data])

		>>> CheckBox("Confirm")
		<CheckBox selectable flow widget 'Confirm' state=False>
		>>> CheckBox("Yogourt", "mixed", True)
		<CheckBox selectable flow widget 'Yogourt' state='mixed'>
		>>> CheckBox("Extra onions", True)
		<CheckBox selectable flow widget 'Extra onions' state=True>
		"""
		self.__super.__init__(None) # self.w set by set_state below
		self._label = Text("")
		self.has_mixed = has_mixed
		self._state = None
		# The old way of listening for a change was to pass the callback
		# in to the constructor.  Just convert it to the new way:
		if on_state_change:
			connect_signal(self, 'change', on_state_change, user_data)
		self.set_label(label)
		self.set_state(state)
	
	def _repr_words(self):
		return self.__super._repr_words() + [
			repr(self.label)]
	
	def _repr_attrs(self):
		return dict(self.__super._repr_attrs(),
			state=self.state)
	
	def set_label(self, label):
		"""
		Change the check box label.

		label -- markup for label.  See Text widget for description
		of text markup.

		>>> cb = CheckBox("foo")
		>>> cb
		<CheckBox selectable flow widget 'foo' state=False>
		>>> cb.set_label(('bright_attr', "bar"))
		>>> cb
		<CheckBox selectable flow widget 'bar' state=False>
		"""
		self._label.set_text(label)
		# no need to call self._invalidate(). WidgetWrap takes care of
		# that when self.w changes
	
	def get_label(self):
		"""
		Return label text.

		>>> cb = CheckBox("Seriously")
		>>> cb.get_label()
		'Seriously'
		>>> cb.label  # Urwid 0.9.9 or later
		'Seriously'
		>>> cb.set_label([('bright_attr', "flashy"), " normal"])
		>>> cb.label  #  only text is returned 
		'flashy normal'
		"""
		return self._label.text
	label = property(get_label)
	
	def set_state(self, state, do_callback=True):
		"""
		Set the CheckBox state.

		state -- True, False or "mixed"
		do_callback -- False to supress signal from this change
		
		>>> changes = []
		>>> def callback_a(cb, state, user_data): 
		...     changes.append(("A", state, user_data))
		>>> def callback_b(cb, state): 
		...     changes.append(("B", state))
		>>> cb = CheckBox('test', False, False)
		>>> connect_signal(cb, 'change', callback_a, "user_a")
		>>> connect_signal(cb, 'change', callback_b)
		>>> cb.set_state(True) # both callbacks will be triggered
		>>> cb.state
		True
		>>> disconnect_signal(cb, 'change', callback_a, "user_a")
		>>> cb.state = False  # Urwid 0.9.9 or later
		>>> cb.state
		False
		>>> cb.set_state(True)
		>>> cb.state
		True
		>>> cb.set_state(False, False) # don't send signal
		>>> changes
		[('A', True, 'user_a'), ('B', True), ('B', False), ('B', True)]
		"""
		if self._state == state:
			return

		if state not in self.states:
			raise CheckBoxError("%s Invalid state: %s" % (
				repr(self), repr(state)))

		# self._state is None is a special case when the CheckBox
		# has just been created
		if do_callback and self._state is not None:
			self._emit('change', self, state)
		self._state = state
		# rebuild the display widget with the new state
		self.w = Columns( [
			('fixed', self.reserve_columns, self.states[state] ),
			self._label ] )
		self.w.focus_col = 0
		
	def get_state(self):
		"""Return the state of the checkbox."""
		return self._state
	state = property(get_state, set_state)
		
	def keypress(self, size, key):
		"""
		Toggle state on 'activate' command.  

		>>> assert command_map[' '] == 'activate'
		>>> assert command_map['enter'] == 'activate'
		>>> size = (10,)
		>>> cb = CheckBox('press me')
		>>> cb.state
		False
		>>> cb.keypress(size, ' ')
		>>> cb.state
		True
		>>> cb.keypress(size, ' ')
		>>> cb.state
		False
		"""
		if command_map[key] != 'activate':
			return key
		
		self.toggle_state()
		
	def toggle_state(self):
		"""
		Cycle to the next valid state.
		
		>>> cb = CheckBox("3-state", has_mixed=True)
		>>> cb.state
		False
		>>> cb.toggle_state()
		>>> cb.state
		True
		>>> cb.toggle_state()
		>>> cb.state
		'mixed'
		>>> cb.toggle_state()
		>>> cb.state
		False
		"""
		if self.state == False:
			self.set_state(True)
		elif self.state == True:
			if self.has_mixed:
				self.set_state('mixed')
			else:
				self.set_state(False)
		elif self.state == 'mixed':
			self.set_state(False)
		self._invalidate()

	def mouse_event(self, size, event, button, x, y, focus):
		"""
		Toggle state on button 1 press.
		
		>>> size = (20,)
		>>> cb = CheckBox("clickme")
		>>> cb.state
		False
		>>> cb.mouse_event(size, 'mouse press', 1, 2, 0, True)
		True
		>>> cb.state
		True
		"""
		if button != 1 or not is_mouse_press(event):
			return False
		self.toggle_state()
		return True
	
		
class RadioButton(CheckBox):
	states = { 
		True: SelectableIcon("(X)"),
		False: SelectableIcon("( )"),
		'mixed': SelectableIcon("(#)") }
	reserve_columns = 4

	def __init__(self, group, label, state="first True",
		     on_state_change=None, user_data=None):
		"""
		group -- list for radio buttons in same group
		label -- markup for radio button label
		state -- False, True, "mixed" or "first True"
		on_state_change, user_data -- shorthand for connect_signal()
			function call for a single callback

		This function will append the new radio button to group.
		"first True" will set to True if group is empty.

		>>> bgroup = [] # button group
		>>> b1 = RadioButton(bgroup, "Agree")
		>>> b2 = RadioButton(bgroup, "Disagree")
		>>> len(bgroup)
		2
		>>> b1
		<RadioButton selectable flow widget 'Agree' state=True>
		>>> b2
		<RadioButton selectable flow widget 'Disagree' state=False>
		"""
		if state=="first True":
			state = not group
		
		self.group = group
		self.__super.__init__(label, state, False, on_state_change, 
			user_data)
		group.append(self)
	

	
	def set_state(self, state, do_callback=True):
		"""
		Set the RadioButton state.

		state -- True, False or "mixed"
		do_callback -- False to supress signal from this change

		If state is True all other radio buttons in the same button
		group will be set to False.

		>>> bgroup = [] # button group
		>>> b1 = RadioButton(bgroup, "Agree")
		>>> b2 = RadioButton(bgroup, "Disagree")
		>>> b3 = RadioButton(bgroup, "Unsure")
		>>> b1.state, b2.state, b3.state
		(True, False, False)
		>>> b3.set_state(True)
		>>> b1.state, b2.state, b3.state
		(False, False, True)
		"""
		if self._state == state:
			return

		self.__super.set_state(state, do_callback)

		# if we're clearing the state we don't have to worry about
		# other buttons in the button group
		if state is not True:
			return

		# clear the state of each other radio button
		for cb in self.group:
			if cb is self: continue
			if cb._state:
				cb.set_state(False)
	
	
	def toggle_state(self):
		"""
		Set state to True.
		
		>>> bgroup = [] # button group
		>>> b1 = RadioButton(bgroup, "Agree")
		>>> b2 = RadioButton(bgroup, "Disagree")
		>>> b1.state, b2.state
		(True, False)
		>>> b2.toggle_state()
		>>> b1.state, b2.state
		(False, True)
		>>> b2.toggle_state()
		>>> b1.state, b2.state
		(False, True)
		"""
		self.set_state(True)

			

class Button(WidgetWrap):
	button_left = Text("<")
	button_right = Text(">")

	def selectable(self):
		return True
	
	def __init__(self, label, on_press=None, user_data=None):
		"""
		label -- markup for button label
		on_press -- callback function for button "press"
		           on_press( button object, user_data=None)
                user_data -- additional param for on_press callback,
		           ommited if None for compatibility reasons
		"""
		self.__super.__init__(None) # self.w set by set_label below
			
		self.set_label( label )
		self.on_press = on_press
		self.user_data = user_data
	
	def set_label(self, label):
		self.label = label
		self.w = Columns([
			('fixed', 1, self.button_left),
			Text( label ),
			('fixed', 1, self.button_right)],
			dividechars=1)
		self._invalidate()
	
	def get_label(self):
		return self.label
	
	def render(self, size, focus=False):
		"""Display button. Show a cursor when in focus."""
		(maxcol,) = size
		canv = self.__super.render(size, focus=focus)
		canv = CompositeCanvas(canv)
		if focus and maxcol >2:
			canv.cursor = (2,0)
		return canv

	def get_cursor_coords(self, size):
		"""Return the location of the cursor."""
		(maxcol,) = size
		if maxcol >2:
			return (2,0)
		return None

	def keypress(self, size, key):
		"""Call on_press on spage or enter."""
		if key not in (' ','enter'):
			return key

		if self.on_press:
			if self.user_data is None:
				self.on_press(self)
			else:
				self.on_press(self, self.user_data)

	def mouse_event(self, size, event, button, x, y, focus):
		"""Call on_press on button 1 press."""
		if button != 1 or not is_mouse_press(event):
			return False
			
		if self.on_press:
			self.on_press( self )
			return True
		return False
	


def _test():
	import doctest
	doctest.testmod()

if __name__=='__main__':
	_test()