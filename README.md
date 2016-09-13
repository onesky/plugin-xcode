OneSky Xcode Plugin
=======================

This plugin lets you sync localizable string resources and translations with OneSky server without logging on to OneSky web admin.

*Note this plugin is not supported in Xcode 8. See [ here ] (https://support.oneskyapp.com/hc/en-us/articles/227128928-Is-the-Xcode-plugin-compatible-with-Xcode-8-) for more information


Installation
------------

1. Download [`OneSkyPlugin.zip`](https://github.com/onesky/plugin-xcode/releases/download/1.8.8/OneSkyPlugin.zip) in the release tab and unzip the folder into `~/Library/Application Support/Developer/Shared/Xcode/Plug-ins/`. If this is the first Plug-ins that you use in Xcode, the Plug-ins directory does not exist. In this case, creating the directory manually would do. Then, Relaunch Xcode.
2. To uninstall, just remove the plugin from there (and restart Xcode) and the project property cache file in `~/Library/Application Support/OneSky/OneSkyProperties.plist`.

Project Settings
----------------

1. Go to **Menu > Editor > OneSky > Project Properties...**
2. Key in your `API Key`, `API Secret`, these parameters can be found on your OneSky web admin dashboard.
3. Select the target `Project` from the project list.
4. Select the `Base Language` of your project.

![project_properties.png](/Images/project_properties.png)

Generate/Update Strings
------------
This tool generates .strings files in base language for both Interface Builder and Source (.m, .c) files, new strings will be merged into existing files. New files will be added to the project and target automatically.

1. Go to **Menu > Editor > OneSky > Generate/Update Strings Files...**
2. Select the files for strings generation and press `Generate`.

![generate_strings.png](/Images/generate_strings.png)


Upload Strings
------------

1. Go to **Menu > Editor > OneSky > Upload Strings...**
2. Select the files to upload to OneSky and press `Upload`.

![upload_strings.png](/Images/upload_strings.png)

Download Translations
-----------------

1. Go to **Menu > Editor > OneSky > Download Translations...**
2. Select the translations to download from OneSky and press `Download`.

![download_translations.png](/Images/download_translations.png)

Support
-------
http://support.oneskyapp.com/

Helpful articles
-------
[ How to support OneSky Xcode plugin in Xcode 8 ] (https://support.oneskyapp.com/hc/en-us/articles/227128928-Is-the-Xcode-plugin-compatible-with-Xcode-8-)

[ How to find API key ](http://support.oneskyapp.com/hc/en-us/articles/206887797-How-to-find-your-API-keys-)

[ Supported languages in iOS ](http://support.oneskyapp.com/hc/en-us/articles/206217438-Languages-supported-by-iOS-)

[More from here](http://support.oneskyapp.com/hc/en-us/sections/201079608-API-and-plugins)
