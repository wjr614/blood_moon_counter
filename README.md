# Blood Moon Counter
A simple Breath of the Wild debug tool for Cemu, tested in US v208

## Usage
Requires no mods or file edits.
Simply launch BOTW in Cemu, set the Cemu folder in the tool, and hit connect.

## Features
### View Only:
Displays:
* The game's internal value for the blood moon counter and scheduling flags.
* Readable countdown in HH:MM:SS format, and total seconds
* Whether the blood moon is currently scheduled to occur this in-game day

### Cheats/Write Tools
**Warning: This tool writes directly to your game's active memory, and has only been tested in versions listed below. If something goes wrong, your save data could be corrupted. Use the cheats at your own risk.**
Tools:
* Reset Blood Moon's active timer
* Remove increments of 1, 5, and 30 minutes from the time remaining
* Set custom values for both time remaining and the internal counter value
* Toggle the scheduled blood moon flags

## Testing and Important Info
###  Warning
This tool assumes static memory offsets based on Breath of the Wild [Us v208]. In my testing they have remained the same across computer resets, Cemu resets, graphics packs, and save files, but pointers are not used. These values being at the same memory addresses consistently does not guarentee they will remain there in all scenarios.

If it writes to the wrong value, your save data can be corrupted, make sure you verify that display values look accurate before using cheat tools.

### How to find your Cemu Folder
In Cemu: "File" --> "Open Cemu Folder"