# BotTender 2.0

BotTender 2.0 is a cocktail making machine built on a Raspberry Pi featuring a touchscreen interface, editable database of cocktails and ingredients, and an intuitive user interface. With BotTender, you can easily browse and make a variety of cocktails or create custom drinks by selecting the desired ingredients and their quantities. BotTender 2.0 is written in Python and uses Kivy for the GUI framework.

Why 2.0? BotTender 2.0 is a complete rewrite of a cocktail making machine I created in 2021.  

## Features

- Touchscreen interface for easy interaction
- Editable database of cocktails and ingredients
- Automatic calculation of ingredient quantities for selected cocktails
- Custom drink creation by choosing specific ingredients and quantities
- Pump configuration for assigning ingredients to pumps
- On Hand category for additional ingredient flexibility
- NFC tag unlocking to prevent accidental misconfigurations (optional)

## Prerequisites

Before setting up the BotTender 2.0 project, ensure you have the following prerequisites installed:

- [Python 3](https://www.python.org/downloads/)
- [Kivy](https://kivy.org/doc/stable/gettingstarted/installation.html#from-source) (installed from source for fullscreen functionality)
- [PN532](https://blog.stigok.com/2017/10/12/setting-up-a-pn532-nfc-module-on-a-raspberry-pi-using-i2c.html) library and configuration for NFC (optional)

## Installation & Setup

To install and set up the BotTender 2.0 project, follow these steps:

1. Clone this repository to your local machine and cd to the cloned directory.
    - ```
         git clone https://github.com/Terguttac/BotTender-2.0.git
         cd BotTender-2.0
      ```
2. Open `bottender.py` in a text editor.
3. If Kivy was installed from source and you wish to use the app fullscreen:
   - Uncomment `os.environ["KCFG_GRAPHICS_FULLSCREEN"]="auto"`.
4. If deploying with a touchscreen:
   - Uncomment `os.environ["KCFG_INPUT_MOUSE"]="False"`.
5. If you configure BotTender to autostart at launch you may need to change the `path_to_cocktails` and `path_to_ingredients` variables to full paths.
   - For example, `path_to_cocktails = '/home/YOURUSERNAME/BotTender-2.0/cocktails.json'`
6. If using an NFC chip to unlock:
   - Run `./get_key.py` and follow the instructions in the terminal.
7. Run `python3 bottender.py` to start the BotTender application.
8. Enjoy!

## Usage

#### A standard deployment of BotTender would follow these steps:

1. Unlock:
   - Tap the "Unlock" button and present the NFC tag (if NFC functionality is enabled).
2. Configure Pumps:
   - Tap the "Configure Pumps" button to assign ingredients to pumps.
3. Configure On Hand:
   - Tap the "Configure On Hand" button to specify ingredients you have available that aren't attached to pumps.
4. Lock:
   - Tap the "Lock" button to prevent accidental changes to the configurations.
5. View Available / Pour Custom:
   - Tap the "View Available" button to see a list of cocktails that can be made with the available ingredients.
   - Alternatively, tap the "Pour Custom" button to create a custom drink by selecting specific ingredients and quantities.

![BotTender Demo GIF](https://github.com/Terguttac/BotTender-2.0/blob/main/gifs/BotTender_demo.gif)


#### To edit the ingredient or cocktail databases, follow these steps:

1. Access the Options screen from the top bar.
2. Tap either edit ingredients or edit recipes
3. Select which action you want to do, "delete", "create", or "view all".
4. Follow the prompts.

![BotTender Drink Creation_GIF](https://github.com/Terguttac/BotTender-2.0/blob/main/gifs/create_demo_drink.gif)

## Further Explanation / Notes

- **On Hand**: The "On Hand" category allows you to add extra flexibility to the BotTender. When configured, cocktails with ingredients that are "On Hand" will be made available even though the ingredient can't be pumped. This is useful for ingredients that are incompatible/inconvenient, such as soda/bitters, or if all the pumps are in use. Cocktails that are available with "On Hand" ingredients are displayed in yellow. 

- **Strictness**: BotTender currently does not differentiate between different types of the same spirit, such as bourbon, rye, scotch, or Irish whiskey. This design choice was made to simplify the configuration and deployment process. However, if you want to restrict a cocktail to a specific type of spirit, you can add that specific type as a separate ingredient in the BotTender's ingredient database. For example, if you want an Old Fashioned cocktail to only be available with Rye whiskey, you can add an ingredient called "Whiskey - Rye" to the database and use it in the recipe for the Old Fashioned. This way, BotTender will suggest the cocktail only when "Whiskey - Rye" is available, ensuring the desired spirit type is used.

- **NFC Lock**: The NFC locking mechanism is intended to prevent accidental misconfigurations. If not using the NFC Chip there will be a quick flash of the popup when unlocking as you bypass the NFC ID check.

## Hardware

The following is the hardware I used to construct BotTender.
- Raspberry Pi
- [7'' touchscreen](https://www.amazon.com/Lebula-Touchscreen-Raspberry-1024X600-Capacitive/dp/B07VNX4ZWY/)
- [8x Peristaltic pumps](https://www.amazon.com/dp/B07Q1C3PW2/ref=twister_B07PZ6RXL2?_encoding=UTF8&th=1)
- [8 channel relay](https://www.amazon.com/ELEGOO-Channel-Optocoupler-Compatible-Raspberry/dp/B09ZQRLD95/)
- [PN532 chip / NFC tag](https://www.amazon.com/HiLetgo-Communication-Arduino-Raspberry-Android/dp/B01I1J17LC)

## Credits
- Cary M. - Designed and constructed the physical frame of BotTender.
- Maiyah M. - Helped assemble, test, film, and rubberduck.
- https://github.com/hoanhan101/pn532 - PN532 reader code
