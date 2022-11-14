shader_type canvas_item;

void fragment() {
	if (!(abs(UV.x*2.-1.) + UV.y < 1.)) {
		COLOR = vec4(0,0,0,0);
	}
}
