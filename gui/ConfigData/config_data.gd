extends Node

# Change your dev path in the exported property
@export var dev_path = "C:\\Users\\Logos\\DoctoratePy\\"

var BASE_PATH = OS.get_executable_path() if not OS.is_debug_build() else dev_path
var CRISIS_PATH = BASE_PATH + "data\\crisis\\"
var START_PATH = BASE_PATH + "start.bat"
var CONFIG_PATH = BASE_PATH + "config\\config.json"

var crisis = {}
var crisis_dirty = true
var config = {}

var dirty = false:
	set(value):
		dirty = value
		if dirty and autosave:
			save_to_disk()
var autosave = false

func _ready():
	for f in DirAccess.get_files_at(CRISIS_PATH):
		if "json" in f:
			var file = FileAccess.open(CRISIS_PATH + f, FileAccess.READ)
			crisis[f.substr(0, len(f)-5)] = JSON.parse_string(file.get_as_text())
	var file = FileAccess.open(CONFIG_PATH, FileAccess.READ)
	config = JSON.parse_string(file.get_as_text())

func save_to_disk():
	for c in crisis.keys():
		var file = FileAccess.open(CRISIS_PATH + c + ".json", FileAccess.WRITE)
		file.store_string(JSON.stringify(crisis[c], "\t"))
	var file = FileAccess.open(CONFIG_PATH, FileAccess.WRITE)
	file.store_string(JSON.stringify(config, "\t"))
	dirty = false
