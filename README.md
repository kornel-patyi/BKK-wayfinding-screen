# BKK wayfinding screen

#### Video Demo:

#### Description: This program simulates a real-life wayfinding screen used by BKK - Centre for Budapest Transport - all around the city of Budapest.


## How to use
If you want to use the application first you have to set the `BKK_API_KEY` system variable with a valid api BKK API key which can be acquired from [BKK's website](https://opendata.bkk.hu/home) (thankfully the website is also available in English besides Hungarian).

After this you need to type in a stops name for which you want to open the display (e.g. Deák Ferenc tér). If there are stops with the given name the aplication will prompt you to choose, which search result would you like to create a display for.

After choosing a correct number a new window will be lauched displaying the corresponding wayfinding screen.


## Implementation
### Classes
The application uses two classes. A `Sprite` class for the static image elements (like the BKK and Budapest logo) and a `Text` class for the static textual elements, like the stop name and the labels. The `Text` class inherits from the `Sprite` class.

### Functions
The `get_data_for_stops` function returns a list of all the which stop at each stop from the given `stop_ids` iterable.<br>
The `refresh_data` function returns the upcoming departures for the given `stop_id`.
The `refresh_data` function is used to update the upcoming departures on a separate thread every 5 seconds after the screen has been opened.

### Dependecies
`Tabulate` is used to create the table from which the user can choose the desired stop.<br>
`Pygame` is used to generate the graphics for the wayfinding screen.<br>
`Requests` is used to send api calls to the BKK api.<br>
Besides these two all the other modules used, such as `os`, `sys`, `json`, `threading`, `time` are built in Python modules.

### Files
The program uses two folders, one for storing the used fonts and one for all the other assets.
#### Fonts
The two fonts are used are Arial for the stickers around the display and modified version of (to support specific accented characters in Hungarian, such as *ŐőŰű*) [JD LCD Rounded](https://www.dafont.com/jd-lcd-rounded.font) for the texts displayed by the screen.
#### Assets
The `static_elements.json` stores the positions for all the static elements (including texts and images) around the wayfinding screen.<br>
Images are stored in `png` format to maximize quality while minimizing file size.

## Licences
**JD LCD Rounded** - was made by *Jecko Development* and is distributed with the *Creative Commons Attribution Share Alike* license.