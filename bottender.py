#!/usr/bin/env python3
import os 
os.environ["KCFG_GRAPHICS_FULLSCREEN"]="False"
#os.environ["KCFG_GRAPHICS_FULLSCREEN"]="auto" 
#os.environ["KCFG_INPUT_MOUSE"]="False"

from kivy.app import App
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from functools import partial
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.progressbar import ProgressBar
import json

from kivy.clock import Clock
from kivy.animation import Animation
from kivy.properties import NumericProperty
import time

from kivy.uix.actionbar import ActionBar

try:
	import RPi.GPIO as GPIO
	GPIO.setmode(GPIO.BCM)
except:
	print("No GPIO or NFC modules!")

try:
	from pn532.api import PN532
	nfc = PN532()
	nfc.setup()
	has_nfc = True
except:
	has_nfc = False
NFC_KEY = [] # PUT NFC KEY HERE!



SECONDS_PER_OZ = 18
INCOMPATIBLE = ['garnish', 'dry', 'carbonated', 'bitters']
MEASUREMENTS = {'tsp':0.166, 'tbsp':0.5, 'dashes':0.03, 'oz':1}
NUM_PUMPS = 8
CUSTOM_MAX = 5 # Maximum amount per ingredient in a custom drink.

pumps = {}
on_hand = []
PUMPS_GPIO = {'1':24, '2':23, '3':27, '4':26, '5':5, '6': 6, '7':13, '8':19, '9':13}
#PUMPS_GPIO keys are the pump numbers as shown in the GUI.
#PUMPS_GPIO values are the GPIO pins associated with the pumps, change the GPIO values as needed.

path_to_cocktails = 'cocktails.json'
path_to_ingredients = 'ingredients.json'

with open(path_to_cocktails) as drinks_file:
    cocktails = json.load(drinks_file)

with open(path_to_ingredients) as ingredients_file:
    ingredients = json.load(ingredients_file)




def start_pump(ingredient, *args):
	pump = list(pumps.keys())[list(pumps.values()).index(ingredient)]
	try:
		GPIO.setup(PUMPS_GPIO[pump], GPIO.OUT)
	except:
		pass

def stop_pump(ingredient, *args):
	pump = list(pumps.keys())[list(pumps.values()).index(ingredient)]
	try:
		GPIO.setup(PUMPS_GPIO[pump], GPIO.IN)
	except:
		pass

class NonScrollablePopup(Popup):
	pass

class ScrollablePopup(Popup):
	pass

class UnlockPopup(NonScrollablePopup):
	def unlock_prompt(self, unlock_button, options_button, pump_button, on_hand_button, *args):
		if unlock_button.state == 'down':
			self.open()
			self.scan_time = 5
			self.ids.grid.add_widget(Label(text=f'Unlock with NFC. \nThe screen will be locked for {self.scan_time} seconds', halign='center'))
			Clock.schedule_once(partial(self.scan_for_nfc, pump_button, on_hand_button, unlock_button, options_button))
			Clock.schedule_once(self.close_popup, self.scan_time)
		else:
			unlock_button.text = 'Unlock'
			options_button.disabled = True
			pump_button.disabled = True
			on_hand_button.disabled = True

	def scan_for_nfc(self, pump_button, on_hand_button, unlock_button, options_button, *args):
		if has_nfc == True:
			read = nfc.read(self.scan_time)
			if read == NFC_KEY:
				self.unlock(pump_button, on_hand_button, unlock_button, options_button)
		else:
			self.unlock(pump_button, on_hand_button, unlock_button, options_button)

	def unlock(self, pump_button, on_hand_button, unlock_button, options_button, *args):
				self.dismiss()
				pump_button.disabled = False
				on_hand_button.disabled = False
				unlock_button.text = 'Lock'
				options_button.disabled = False

	def close_popup(self, *args):
                self.dismiss()

class RecipePopup(NonScrollablePopup):
	'''
	Popup that displays the ingredients of the selected recipe, the button to
	interact with the recipe changes depending on what screen called the popup.
	'''
	def view_recipe(self, recipe, parent, *args):
		self.ids.grid.clear_widgets()
		self.title = recipe
		for ingredient in cocktails[recipe]:
			reference = cocktails[recipe][ingredient]
			if reference['type'] != 'garnish':
					if ingredient in on_hand:
						self.ids.grid.add_widget(Label(
							text = f"{reference['amount']} {reference['measurement']} {ingredient}",
							color=(1,1,0,1)))
					else:
						self.ids.grid.add_widget(Label(text = 
							f"{reference['amount']} {reference['measurement']} {ingredient}"))
			else: 
				self.ids.grid.add_widget(Label(text = f'Garnish: {ingredient}'))
		if parent.name == 'available_cocktails':
			self.button = Button(text=f'Make {recipe}')
			self.button.bind(on_release=partial(ProgressBarPopup().build_screen, recipe, parent))
			self.button.bind(on_release=self.dismiss)
			self.ids.grid.add_widget(self.button)
		elif parent.name == 'delete_recipe':
			self.ids.grid.add_widget(Button(
				text = f"Delete {recipe}", 
				on_release = partial(parent.delete_recipe, recipe, self)))
		
		self.open()




class ProgressBarPopup(NonScrollablePopup):
	'''
	Popup that displays the progress of each ingredient as a moving bar.
	When complete, clears the popup to display a completion message.
	the 'custom' paramter indactes whether the call comes from the CustomDrinkScreen
	If so, set the unit to ounces since custom drinks do not support other units of 
	measurement.
	'''
	def build_screen(self, recipe, parent, *args, custom=False):
		parent.manager.current = 'home'
		if custom == True:
			self.title = 'Making custom drink'
		else:
			self.title = f'Making {recipe}'
		self.ids.grid.clear_widgets()
		self.auto_dismiss = False
		self.clocks = []
		self.time_to_finish = 0

		if custom:
			self.recipe = recipe
		else:
			self.recipe = cocktails[recipe]

		for ingredient in self.recipe:
				if ingredient in pumps.values():
					self.ids.grid.add_widget(Label(text=f'Pouring {ingredient}'))
					self.progress_bar = MyProgressBar()
					self.ids.grid.add_widget(self.progress_bar)
					if custom == True:
						unit = 'oz'
						amount = recipe[ingredient]
					else:
						unit = self.recipe[ingredient]['measurement']
						amount = self.recipe[ingredient]['amount']
					self.seconds_to_pour = (float(amount) * MEASUREMENTS[unit]) * SECONDS_PER_OZ
					if self.time_to_finish < self.seconds_to_pour:
						self.time_to_finish = self.seconds_to_pour

					Clock.schedule_once(partial(self.count_time, self.progress_bar, self.seconds_to_pour))
					self.schedule_stop = Clock.schedule_once(partial(stop_pump, ingredient), self.seconds_to_pour)
					self.clocks.append(self.schedule_stop)
					start_pump(ingredient)
		self.ids.grid.add_widget(Button(text='Cancel', on_release=self.cancel_pumps))
		Clock.schedule_once(self.complete_popup, self.time_to_finish)
		

		self.open()	
	
	def complete_popup(self, *args):
		self.ids.grid.clear_widgets()
		self.ids.grid.add_widget(Label(text = 'Drink complete!'))
		for ingredient in self.recipe:
			if ingredient not in pumps.values():
				if self.recipe[ingredient]['type'] == 'garnish':
					self.ids.grid.add_widget(Label(text=f"Don't forget to garnish with {ingredient}!", color=(1,1,0,1)))
				elif self.recipe[ingredient]['type'] == 'soda':
					self.ids.grid.add_widget(Label(text=f"Don't forget to top off with {ingredient}!", color=(1,1,0,1)))
				else:
					self.ids.grid.add_widget(Label(text=f"Don't forget to add {self.recipe[ingredient]['amount']} {self.recipe[ingredient]['measurement']} {ingredient}!", color=(1,1,0,1)))
		self.ids.grid.add_widget(Button(text = 'Dismiss', on_release = self.dismiss))

	def count_time(self, specific_bar, seconds_to_pour, *kwargs):
		specific_bar.max = seconds_to_pour
		specific_bar.a = seconds_to_pour
		specific_bar.b = seconds_to_pour
		specific_bar.start()

	def cancel_pumps(self, ingredient, *args):
		for ingredient in self.recipe:
			if ingredient in pumps.values():
				stop_pump(ingredient)
				for my_clock in self.clocks:
					my_clock.cancel()
				self.ids.grid.clear_widgets()
				self.ids.grid.add_widget(Label(text='Drink Cancelled'))
				self.ids.grid.add_widget(Button(text='Close', on_release=self.dismiss))


class MyProgressBar(ProgressBar):
	a = NumericProperty()
	b = NumericProperty()

	def start(self):
		Animation.cancel_all(self)
		self.anim = Animation(a=0, duration = self.a)
		self.anim.start(self)

	def on_a(self, instance, value):
		self.value = self.b - value

	def stop(self):
		self.anim.stop(self)


class IngredientSelectionPopup(ScrollablePopup):
	def select_type(self, parent, *args, add=False, remove=False, pump=None):
		self.title = "Select Type"
		self.ids.grid.clear_widgets()
		self.ingredients = ingredients
		for ingredient_type in sorted(self.ingredients):
			self.button = Button(text=ingredient_type)
			if pump != None:
				if ingredient_type == 'garnish' or ingredient_type == 'dry' or ingredient_type == 'carbonated':
					continue
			if add == True:
				self.button.bind(on_release=partial(EditIngredientDBPopup().add_new_ingredient, ingredient_type, self))
			else:
				self.button.bind(on_release=partial(self.select_specific, ingredient_type, parent, remove, pump))
			self.button.size_hint_y = None
			self.ids.grid.add_widget(self.button)
		self.open()

	def select_specific(self, ingredient_type, parent, remove, pump, *args):
		self.title = "Select Ingredient"
		self.ids.grid.clear_widgets()
		for ingredient in sorted(self.ingredients[ingredient_type]):
			if remove == True:
				self.ids.grid.add_widget(Button(text=ingredient, size_hint_y=None, on_release=partial(EditIngredientDBPopup().remove_ingredient, ingredient, ingredient_type, self)))
			#If the ingredient is already set to a pump, don't create a button for it.
			elif pump != None:
				if ingredient in pumps.values():
					continue
				else:
					self.ids.grid.add_widget(Button(text=ingredient, size_hint_y=None, on_release=partial(parent.set_ingredient, ingredient, ingredient_type, pump)))
			else:
				self.ids.grid.add_widget(Button(text=ingredient, size_hint_y=None, on_release=partial(parent.set_ingredient, ingredient, ingredient_type, pump)))

class EditIngredientDBPopup(NonScrollablePopup):
	def add_new_ingredient(self, ingredient_type, parent, *args):
		parent.dismiss()
		self.title = f'Add Ingredient To {ingredient_type.capitalize()}'
		self.text_input = TextInput(font_size=28)
		self.ids.grid.add_widget(self.text_input)
		self.ids.grid.add_widget(Button(text='Cancel', on_release=self.dismiss))
		self.ids.grid.add_widget(Button(text='Confirm',on_release=partial(self.write_changes, None, ingredient_type, add=True)))
		self.open()

	def remove_ingredient(self, ingredient, ingredient_type, parent, *args):
		parent.dismiss()
		self.title = f'Remove {ingredient} From {ingredient_type.capitalize()}'
		self.ids.grid.add_widget(Label(text=f'Are you sure you want to remove {ingredient} from {ingredient_type}?'))
		self.ids.grid.add_widget(Button(text='Cancel', on_release=self.dismiss))
		self.ids.grid.add_widget(Button(text='Confirm',on_release=partial(self.write_changes, ingredient, ingredient_type, add=False)))
		self.open()


	def write_changes(self, ingredient, ingredient_type, *args, add=True):
		if add == True:
			if ingredient_type == 'juices':
				self.ingredient_name = self.text_input.text + ' juice'
			elif ingredient_type == 'bitters':
				self.ingredient_name = self.text_input.text + ' bitters'
			else:
				self.ingredient_name = self.text_input.text
			ingredients[ingredient_type].append(self.ingredient_name.lower())
		else:
			ingredients[ingredient_type].remove(ingredient)
		with open(path_to_ingredients, "w") as ingredients_file:
			json.dump(ingredients, ingredients_file, indent=4)
		self.dismiss()


class NumPickerPopup(NonScrollablePopup):
	'''
	A popup that prompts the user to select amounts via up and down arrows.
	Increments by the selected amount and then updates the screen tha called it.
	'''
	def input_amount(self, parent, ingredient, amounts, *args, unit='oz'):
		self.ids.grid.clear_widgets()
		self.unit = unit
		
		if ingredient in amounts and amounts[ingredient] > 0:
			self.total = amounts[ingredient]
		else:
			self.total = 0
		self.ingredient = ingredient

		self.build_popup(parent)		
		self.open()

	def build_popup(self, parent, *args):
		self.total_label = Label(text = f"{self.total} {self.unit} {self.ingredient}", size_hint_y=.4)
		self.ids.grid.add_widget(self.total_label)

		self.amount = .25
		self.button_grid = GridLayout(cols = 3)
		for i in range(1,4):
			self.button_grid.add_widget(Button(text='v', on_press=partial(self.adjust_total, -(self.amount), parent)))
			self.button_grid.add_widget(Button(text=f"{self.amount} {self.unit}"))
			self.button_grid.add_widget(Button(text='^', font_size= 40, on_press=partial(self.adjust_total, self.amount, parent)))

			# multiply self.amount by 2 to increase the amount per button with each iteration (.25, .5, 1.0)
			self.amount *= 2

		self.confirm_button = Button(text='Confirm', on_press=partial(self.update_ingredient, parent, self.unit))

		self.button_grid.add_widget(Label())

		self.button_grid.add_widget(self.confirm_button)
		self.ids.grid.add_widget(self.button_grid)


	def adjust_total(self, amount, parent, *args):
		if (self.total + amount) <= CUSTOM_MAX and self.total + amount >= 0:
			self.total += amount
			self.total_label.text = f"{self.total} {self.unit} {self.ingredient}"

	def update_ingredient(self, parent, unit, *args):
		self.dismiss()
		parent.update_ingredient(self.ingredient, self.total, unit)

class TopBar(ActionBar):
	pass

class BaseScreen(Screen):
	pass

class ScrollableScreen(Screen):
	pass

class AvailableCocktailScreen(ScrollableScreen):
	def on_enter(self, *args):
		'''
		Check the ingredients of each cocktail in the database against the current
		ingredients attached to the pumps. If all ingredients are attached, create
		a button for that cocktail. Clicking the button creates a popup listing
		the ingredients and a button to begin pouring the drink.
		'''
		self.ids.grid.clear_widgets()
		for recipe in sorted(cocktails):
			cocktail_ingredients = set(cocktails[recipe].keys())
			for ingredient in cocktails[recipe]:
				if cocktails[recipe][ingredient]['type'] == 'garnish':
					cocktail_ingredients.discard(ingredient)
			available_ingredients = set(list(pumps.values()) + on_hand)
			if cocktail_ingredients.issubset(pumps.values()):	
				self.ids.grid.add_widget(Button(
					text = recipe,
					on_release = partial(RecipePopup().view_recipe, recipe, self),
					size_hint_y=None))
			elif cocktail_ingredients.issubset(available_ingredients):	
				self.ids.grid.add_widget(Button(
					text = f'[color=fff333]{recipe}[/color]',markup=True,size_hint_y=None,
					on_release = partial(RecipePopup().view_recipe, recipe, self)))
			
class AllCocktailScreen(ScrollableScreen):
	def __init__(self, **kwargs):
		super(AllCocktailScreen, self).__init__(**kwargs)
	'''
	Create a button for each cocktail in the database. This menu does not
	offer a button to pour drinks. Instead, it allows easy reference of all 
	cocktails that have been added to the database. 
	'''
	def on_enter(self, *args):	
		self.ids.grid.clear_widgets()
		for recipe in sorted(cocktails):
			self.ids.grid.add_widget(Button(
				text = recipe,
				size_hint_y= None,
				on_release = partial(RecipePopup().view_recipe, recipe, self)))

class CustomCocktailScreen(Screen):
	'''
	List each ingredient configured to the pumps. On press, open the NumPicker popup.
	Reset and Confirmation buttons to set all values to 0 or to confirm and pump the custom
	drink.
	'''
	def on_enter(self, *args):
		self.ids.grid.cols = NUM_PUMPS
		self.amounts = {}
		self.build_screen()

	def build_screen(self, *args):
		self.ids.grid.clear_widgets()

		'''
		Check if there is at least 1 pump with a set ingredient.
		If so, build the GUI for each configured pump.
		'''
		self.ids.grid.clear_widgets()
		if len(pumps.values()) == 0:
			self.ids.grid.add_widget(Label(text="No pumps are configured!"))

		else:
			self.inner_grid = GridLayout(cols=4, size_hint_x=.5)

			for ingredient in pumps.values():
				if ingredient in self.amounts:
					self.button = Button(text = f'{self.amounts[ingredient]} oz {ingredient}')
				else:
					self.button = Button(text = ingredient)	
				if len(pumps.values()) < 5:
					self.button.font_size = (self.button.width / (len(pumps.values())+1))
				else:
					self.button.font_size = (self.button.width / 5)					
				self.button.bind(on_release = partial(NumPickerPopup().input_amount, self, ingredient, self.amounts))
				self.inner_grid.add_widget(self.button)

			self.ids.grid.add_widget(self.inner_grid)

		
		self.bottom_grid = GridLayout(cols=2, size_hint_y=.2)
		if len(self.ids.outer_grid.children) == 1:
			self.ids.outer_grid.add_widget(self.bottom_grid)
			
			self.bottom_grid.add_widget(Button(text = 'Reset', on_release = self.clear_amounts))
			self.bottom_grid.add_widget(Button(text = 'Confirm', on_release = self.confirmation_popup))
	
	def update_ingredient(self, ingredient, amount, *args):
		self.amounts[ingredient] = amount
		self.build_screen()


	def clear_amounts(self, *args):
		self.amounts.clear()
		self.build_screen()

	def confirmation_popup(self, *args):
		self.popup = NonScrollablePopup(title = 'Confirm Custom Drink')
		for ingredient in self.amounts:
			if self.amounts[ingredient] > 0:
				self.popup.ids.grid.add_widget(Label(text=f'{self.amounts[ingredient]} oz {ingredient}'))
		self.popup.ids.grid.add_widget(Button(text='Cancel', on_release=self.popup.dismiss))
		self.popup.ids.grid.add_widget(Button(text='Confirm & Pour', on_release=self.open_progress_popup))

		self.popup.open()

	def open_progress_popup(self, *args):
		self.popup.dismiss()
		ProgressBarPopup().build_screen(self.amounts, self, custom=True)
		self.amounts={}
		self.build_screen()

class CreateNewCocktailScreen(Screen):
	def on_enter(self, *args):
		self.recipe = {}
		self.ids.ingredient_grid.clear_widgets()
		self.ids.button_grid.clear_widgets()
		self.select_ingredient_popup = IngredientSelectionPopup()
		self.error_popup = NonScrollablePopup(title='ERROR')
		self.error_popup.ids.grid.add_widget(Label(text='A cocktail requires a name and at least two ingredients!'))
		self.build_screen()

	def build_screen(self, *args):
		self.label = Label(text='Ingredients', font_size=28)
		self.ids.ingredient_grid.add_widget(self.label)

		self.ids.button_grid.add_widget(Label(text="Name:", font_size=28, size_hint_y=.5))
		self.textinput = (TextInput(size_hint_y = .5, font_size=28))
		self.ids.button_grid.add_widget(self.textinput)
		self.ingredient_popup = IngredientSelectionPopup()
		self.ids.button_grid.add_widget(Button(text='Add\nIngredient',
			on_release=partial(self.ingredient_popup.select_type, self)))
		self.ids.button_grid.add_widget(Button(text='Confirm', on_release=self.save_recipe))

	def save_recipe(self, *args):
		if len(self.recipe.keys()) <= 1 or self.textinput.text == "":
			self.error_popup.open()	
		else:
			cocktails[self.textinput.text.title()] = self.recipe
			with open(path_to_cocktails, "w") as drinks_file:
				json.dump(cocktails, drinks_file, indent=4)
			self.manager.current='home'

	def set_ingredient(self, ingredient, ingredient_type, *args):
		self.ingredient_popup.dismiss()
		self.ingredient_type = ingredient_type
		self.measurement_popup = NonScrollablePopup()
		if ingredient_type != 'garnish':
			for unit in sorted(MEASUREMENTS):
				self.measurement_popup.ids.grid.add_widget(Button(text=unit, on_release=partial(NumPickerPopup().input_amount, self, ingredient, "", unit=unit)))
			self.measurement_popup.open()
		else:
			self.update_ingredient(ingredient, 0, None)

	def update_ingredient(self, ingredient, total, unit):
		self.measurement_popup.dismiss()
		if self.label:
			self.ids.ingredient_grid.remove_widget(self.label)
		self.recipe[ingredient] = {"amount":str(total), "measurement":unit, "type":self.ingredient_type}
		self.ids.ingredient_grid.add_widget(Label(text=f"{total} {unit} {ingredient.capitalize()}", font_size=28))


class DeleteCocktailScreen(AllCocktailScreen):
	'''
	Uses the AllCocktailScreen class to build the screen. 
	'''
	def __init__(self, **kwargs):
		super(DeleteCocktailScreen, self).__init__(**kwargs)
	
	def delete_recipe(self, recipe, popup, *args):
		popup.dismiss()
		cocktails.pop(recipe)
		with open(path_to_cocktails, "w") as drinks_file:
			json.dump(cocktails, drinks_file, indent=4)
		self.manager.current = 'home'

class IngredientsHomeScreen(BaseScreen):
	def on_enter(self, *args):
		self.ids.grid.clear_widgets()
		self.ids.grid.cols = 2
		self.ids.grid.add_widget(Button(text='View All Ingredients', on_release=partial(IngredientSelectionPopup().select_type, self)))
		self.ids.grid.add_widget(Button(text='Add Ingredient', on_release=partial(IngredientSelectionPopup().select_type, self, add=True)))
		self.ids.grid.add_widget(Button(text='Delete Ingredient', on_release=partial(IngredientSelectionPopup().select_type, self, remove=True)))

	#This function is just to satisfy IngredientSelectionPopup's callback
	def set_ingredient(self, *args):
		pass

class PumpConfigScreen(BaseScreen):
	def on_enter(self):
		global pumps
		self.get_current_config(self)


	def get_current_config(self, *args):
		self.ingredient_popup = IngredientSelectionPopup()
		self.ids.grid.clear_widgets()
		for pump in range(1, NUM_PUMPS+1):
			if str(pump) in pumps:
				self.button = Button(text=f"Pump #{pump} - {pumps[str(pump)]}")
			else:
				self.button = Button(text=f"Pump #{pump} - Unselected")
			self.button.bind(on_release = partial(self.ingredient_popup.select_type, self, pump=pump))
			self.ids.grid.add_widget(self.button)

	def set_ingredient(self, ingredient, ingredient_type, pump, *args):
		self.ingredient_popup.dismiss()
		pumps[str(pump)]=ingredient
		self.get_current_config()

class OnHandConfigScreen(BaseScreen):
	'''
	This screen allows for additional ingredients to be even if they are not compatible with the pump.
	By configuring these ingredients, you can control how strict the available cocktails list will be.
	If you only want drinks that can be completely pumped, do not configure any ingredients through this screen.
	Alternatively, if it is acceptable to manually add certain ingredients, such as soda water, add those 
	ingredients here.
	'''
	def on_enter(self):
		global on_hand
		self.ingredient_popup = IngredientSelectionPopup()
		self.get_current_config()

	def get_current_config(self, *args):
		self.ids.grid.clear_widgets()
		self.ingredient_grid = GridLayout(cols=3)
		self.ids.grid.add_widget(self.ingredient_grid)
		for ingredient in on_hand:
			self.ingredient_grid.add_widget(Label(text=ingredient))
		self.bottom_grid = GridLayout(cols=2, size_hint_y=.6)
		self.ids.grid.add_widget(self.bottom_grid)
		self.bottom_grid.add_widget(Button(text='Reset', on_release=partial(self.clear_ingredients, self)))
		self.bottom_grid.add_widget(Button(text='Add Ingredient', on_release=partial(self.ingredient_popup.select_type, self)))

	def set_ingredient(self, ingredient, *args):
		on_hand.append(ingredient)
		self.get_current_config()
		self.ingredient_popup.dismiss()

	def clear_ingredients(self, *args):
		on_hand.clear()
		self.get_current_config()

class TopBar(ActionBar):
	pass

class RecipesHomeScreen(Screen):
	pass

class Bottender(BoxLayout):
    pass

class BottenderApp(App):
    def build(self):
        return Bottender()

if __name__ == "__main__":
	BottenderApp().run()
