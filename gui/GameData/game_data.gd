extends Node

const BASE_URL := "https://raw.githubusercontent.com/Kengxxiao/ArknightsGameData/master/zh_CN/gamedata"
const SKIN_TABLE_URL := BASE_URL + "/excel/skin_table.json"
const CHARACTER_TABLE_URL := BASE_URL + "/excel/character_table.json"
const BATTLEEQUIP_TABLE_URL := BASE_URL + "/excel/battle_equip_table.json"
const STAGE_TABLE_URL := BASE_URL + "/excel/stage_table.json"

var skin_table := {}
var character_table := {}
var battle_equip_table := {}
var stage_table := {}
var rune_stage_table := {}

func _ready():
	# Get Game Tables
	var urls := [SKIN_TABLE_URL, CHARACTER_TABLE_URL, BATTLEEQUIP_TABLE_URL, STAGE_TABLE_URL]
	var dicts := ["skin_table", "character_table", "battle_equip_table", "stage_table"]
	for i in range(len(dicts)):
		var http := HTTPRequest.new()
		add_child(http)
		http.connect("request_completed", _http_request_completed.bind(dicts[i]))
		http.accept_gzip = false
		
		var error := http.request(urls[i])
		if error != OK:
			push_error("Error creating request for " + urls[i] + ": " + error)

signal skin_table_loaded()
signal character_table_loaded()
signal battle_equip_table_loaded()
signal stage_table_loaded()
signal rune_stage_table_loaded()

func _http_request_completed(result, response_code, headers, body : PackedByteArray, dict_to_update : String):
	set(dict_to_update, JSON.parse_string(body.get_string_from_ascii()))
	emit_signal(dict_to_update + "_loaded")
	print(dict_to_update + " loaded.")
