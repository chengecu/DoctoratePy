# DoctoratePy
Python server implementation of a certain anime tower defense game. This repo is for the CN TapTap Version.

Discord Invite: [Link](https://discord.gg/pUj8HQ5FQU)

## How To

1. Install [mitmproxy](https://mitmproxy.org/) and [python3](https://www.python.org/downloads/).
2. Download adb ([Link](https://adbinstaller.com/)) and then set it up as environment variable ([Link](https://docs.oracle.com/en/database/oracle/machine-learning/oml4r/1.5.1/oread/creating-and-modifying-environment-variables-on-windows.html#GUID-DD6F9982-60D5-48F6-8270-A27EC53807D0)).
3. Clone the repo.
4. Open emulator and make sure adb is working.
5. Run `setup_mitmproxy.bat` until you get a `Mitmproxy cert is already installed as system certificate. Exiting....` message.
6. Configure your proxy ip address in `fridahook.py` on line `115`.
7. Run `start.bat` in the cloned folder.

Note: There should be a total of 4 cmd windows opened.

## Currently tested emulator to be working
1. LDPlayer9

## Changing contengency contract season
Change the value of key `selectedCrisis` in `config\config.json` to whatever you want. The avaiable seasons are in `data\crisis`.

## Customizing indivual operators level, potentials, skill ranks and others
Customize each operator indivually by adding new info in `customUnitInfo` key in `config\config.json`. You can find <operator_key_name> from [here](https://raw.githubusercontent.com/Kengxxiao/ArknightsGameData/master/zh_CN/gamedata/excel/character_table.json). By default, all characters will have max level, max potentials, max mastery.

- `favorPoint` - Trust points (25570 is 200% Trust) [link to exact point to %](https://gamepress.gg/arknights/core-gameplay/arknights-guide-operator-trust)
- `mainSkillLvl` - Skill Rank (Put mastery at 0 if this is lower than 7)
- `potentialRank` - 0-5
- `evolvePhase` - 0 - E0, 1 - E1, 2 - E2
- `skills` - Mastery level for each skill starting from S1.

### Format
```
"<operator_key_name>": {
    "favorPoint": 25570,
    "mainSkillLvl": 7,
    "potentialRank": 2,
    "level": 50, 
    "evolvePhase": 1,
    "skills": [1, 0]
}
```

## Customizing support unit
Customize the support unit list by changing the unit info in `assistUnit` key in `config\config.json`. All characters info can be found [here](https://raw.githubusercontent.com/Kengxxiao/ArknightsGameData/master/zh_CN/gamedata/excel/character_table.json).

- `charId` - key of the character
- `skinId` - skinId of the character (Skin List can be found [here](https://raw.githubusercontent.com/Kengxxiao/ArknightsGameData/master/zh_CN/gamedata/excel/skin_table.json))
- `skillIndex` - Skill Index of the support unit (Index starts from 0).

Note: Characters stats and skill masteries are based on the above parameters.

### Format
```
{
    "charId": "char_350_surtr",
    "skinId": "char_350_surtr@it#1",
    "skillIndex": 2
}
```

## GUI

The included DoctorateGUI.exe is a Windows binary for a GUI application. You can use it to change your configuration data and launch start.bat.

The GUI is a Godot 4 project. Godot 4 is in beta, however it's very stable and has significant improvements from Godot 3. If you would like to adjust the GUI yourself, Godot 4 can be obtained from dev snapshots in the official [Godot news](https://godotengine.org/news/default/1). 
To edit the project, load project.godot inside /gui/ with a Godot 4 build.
To export an executable, follow the [Godot export guidelines](https://docs.godotengine.org/en/stable/tutorials/export/exporting_projects.html).

## TODO
- ...
