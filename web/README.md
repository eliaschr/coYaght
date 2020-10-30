# DeepSeaRobotix - coYaght
---

This file describes the way the web user interface works

![coYaght UI Image](images/coYaghtUI.gif)

When the user visits the IP of coYaght using http://192.168.111.10 the first thing that appears is the logo of the virtual company, **DeepSeaRobotix**. At the bottom of the screen there is a status bar that indicates if the Raspberry system is connected to the Arduino hardware and the time the RTC has. In the beginning the Status is _Connecting..._
When the connection of the server to the Arduino is established the Status is changed to _Connected_ and the logo of the company just moves to the upper left corner of the page. The main screen appears.

## Main Screen and UI usage

The main screen is split into four sections:

* The upper right section presents the live streaming of the Raspberry Pi's camera. Upon loading the page, the video streaming starts. Under the camera window there is the _Pause_ button. When pressed it freezes the video and stop streaming. Alos, a _Play_ button takes its place which when pressed it restarts the camera streaming.
* The upper left section contains line graphs that represent the values measured by Arduino. When the page is first loaded they are stopped. By clicking on the _Play_ button just under the graphs, the system starts taking measurements. When the _Play_ button is pressed the _Stop_ one takes its place. When pressed it commands the system to stop taking measurements.
	* The upper canvas presents the **Pressure** and the **Temperature** measurements. The pressure can be presented as _KPa_ or as Depth in _meters_. The type of the pressure presentation is selected by the radio buttons just underneath this graph set.
	* The lower canvas presents the **Ambient Light** measurement in _Lux_ and the **Power Voltage** of the system in _Volts_.
* The lower left section contains the navigation buttons that move the coYaght vertically (_Ascent_ and _Dive_).
* The lower right section contains all the buttons that navigate the coYaght horizontally; _Forward_, _Backwards_, _Rotate left_, _Rotate right_, _Turn left forward_, _Turn left Backwards_, _Turn right forward_, _Turn right backwards_.

Since using the mouse to navigate the coYaght is tricky, there are some keyboard buttons used to activate the same visual buttons:

* Q: Ascent to surface
* A: Dive
* NumPad 8: Move forward
* NumPad 2: Move backwards
* NumPad 6: Rotate right
* NumPad 4: Rotate left
* NumPad 9: Turn right forward
* NumPad 3: Turn right backwards
* NumPad 7: Turn left forward
* NumPad 1: Turn left backwards

On the graphs, when the mouse pointer points at a graph node, a tooltip appears that presents the graph name, and its value. This is very useful to track the precise value as just observing the graph is not accurate. Every time the _Play_ button of the graphs is pressed to start taking measurements, the previous graphs are reset and a new "session" starts.

## Files of the web user interface

The main file is the [_index.html_](index.html). It is a simple HTML file that contains all the graphical components used in the User Interface. It also loads the rest of the necessary files, stylesheets and JavaScript code.
All the necessary stylesheets are in the [_styles_](styles) directory. They are needed to apply styling on the page components:
* [_main.css_](styles/main.css): This is the file that applies styling to [_index.html_](index.html) page components
* [_tooltip.css_](styles/tooltip.css): This file contains styling rules for the tooltips that appear on the graphs when the mouse pointer points a graph node.
* [_util.css_](styles/util.css): This file contains all the rules that are applied on the graphs.

Both [_tooltip.css_](styles/tooltip.css) and [_util.css_](styles/util.css) are coded by Google Inc.

In the [_images_](images) directory contains all the needed images that appear on the web user interface.

Finally in the [scripts](scripts) directory there are JavaScript files for the automation of the page. The files that lie in this directory are:

* [_main.js_](scripts/main.js): Contains the JavaScript code for the user interface. It handles all the keystrokes and the communication to the server and the rest of the animations.

The rest of the code comes from [Google Inc.](https://developers.google.com/chart/). It is used for creating the graphs on the page. Their files are:
* loader.js
* jsapi_compiled_corechart_module.js
* jsapi_compiled_default_module.js
* jsapi_compiled_graphics_module.js
* jsapi_compiled_ui_module.js
