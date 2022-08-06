uniform float darken;
out vec4 fragColor;

void main() {
    // pattern - note: zero is in bottom left..
    // 1 0 0
    // 0 0 1
    // 0 1 0
    
    vec4 a = blender_srgb_to_framebuffer_space(vec4(0.0, 0.0, 0.0, 1.0));
    vec4 b = blender_srgb_to_framebuffer_space(vec4(0.0, 0.0, 0.0, darken));
    if(mod(floor(gl_FragCoord.x), 3) == 0 && mod(floor(gl_FragCoord.y), 3) == 2){
        fragColor = a;
    }else if(mod(floor(gl_FragCoord.x), 3) == 1 && mod(floor(gl_FragCoord.y), 3) == 0){
        fragColor = a;
    }else if(mod(floor(gl_FragCoord.x), 3) == 2 && mod(floor(gl_FragCoord.y), 3) == 1){
        fragColor = a;
    }else{
        fragColor = b;
    }
}