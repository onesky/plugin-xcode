OneSky Plugin for Xcode
=======================

This library lets you sync localizable string resources and translations with OneSky server without logging on to OneSky web admin.


Installation
------------

1. Download [`OneSkyPlugin.zip`](https://github.com/onesky/plugin-xcode/releases/download/1.4.9/OneSkyPlugin.zip) in the release tab and unzip the folder into `~/Library/Application Support/Developer/Shared/Xcode/Plug-ins/`. If this is the first Plug-ins that you use in Xcode, the Plug-ins directory does not exist. In this case, creating the directory manually would do. Then, Relaunch Xcode. 
2. To uninstall, just remove the plugin from there (and restart Xcode) and the project property cache file in `~/Library/Application Support/OneSky/OneSkyProperties.plist`.

Project Settings
----------------

1. Go to **Menu > Editor > OneSky > Project Properties...**
2. Key in your `API Key`, `API Secret`, these parameters can be found on your OneSky web admin dashboard.
3. Select the target `Project` from the project list.
4. Select the `Base Language` of your project.

![project_properties.png](https://raw.github.com/onesky/plugin-xcode/master/Images/project_properties.png)

Generate/Update Strings
------------
This tool generates .strings files in base language for both Interface Builder and Source (.m, .c) files, new strings will be merged into existing files. New files will be added to the project and target automatically.

1. Go to **Menu > Editor > OneSky > Generate/Update Strings Files...**
2. Select the files for strings generation and press `Generate`.

![generate_strings.png](https://raw.github.com/onesky/plugin-xcode/master/Images/generate_strings.png)


Send Strings
------------

1. Go to **Menu > Editor > OneSky > Send Strings...**
2. Select the files to send to OneSky and press `Send`.

![send_strings.png](https://raw.github.com/onesky/plugin-xcode/master/Images/send_strings.png)

Sync Translations
-----------------

1. Go to **Menu > Editor > OneSky > Sync Translations...**
2. Select the translations to download from OneSky and press `Sync`.

![sync_translations.png](https://raw.github.com/onesky/plugin-xcode/master/Images/sync_translations.png)

Support
-------
http://support.oneskyapp.com/

Helpful articles
-------
[ How to find API key ](http://support.oneskyapp.com/solution/categories/74754/folders/150388/articles/89104-how-to-find-your-api)

[ Supported languages in iOS ](http://support.oneskyapp.com/solution/categories/74754/folders/122474/articles/70697-supported-ios)

[More from here](http://support.oneskyapp.com/solution/categories)
