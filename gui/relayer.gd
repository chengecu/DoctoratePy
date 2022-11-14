extends Node

# Relays ready, process and input to parent.
# Tracks parent's properties and notifies parent on update.


var last_state := {}
var on_process := []

func _ready():
	var on_ready_regex = RegEx.new()
	on_ready_regex.compile("^_ready_(.+)")
	var on_process_regex := RegEx.new()
	on_process_regex.compile("^_process_(.+)")
	var tracking_regex := RegEx.new()
	tracking_regex.compile("^_on_(.+)_changed")
	for fun in get_parent().get_method_list():
		var result := on_process_regex.search(fun["name"])
		if result:
			on_process.append(fun)
		result = on_ready_regex.search(fun["name"])
		if result:
			get_parent().call(fun["name"])
		result = tracking_regex.search(fun["name"])
		if result:
			var val = get_parent().get(result.strings[1])
			last_state[result.strings[1]] = val.hash() if (val is Array or val is Dictionary) else val


func _process(dt):
	for fun in on_process:
		if len(fun["args"]) == 1:
			get_parent().call(fun["name"], dt)
		else:
			get_parent().call(fun["name"])
		
	for prop in last_state.keys():
		var val = get_parent().get(prop)
		var new = val.hash() if (val is Array or val is Dictionary) else val
		if new != last_state[prop]:
			last_state[prop] = new
			get_parent().call("_on_" + prop + "_changed")
