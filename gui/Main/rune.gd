extends Control

@export var id = ""

func _process(delta):
	visible = id != ""
	modulate.a = 0 if id == "_placeholder" else 1
	$Button.disabled = not visible or id == "_placeholder"
