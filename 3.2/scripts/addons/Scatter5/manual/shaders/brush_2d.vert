in vec2 position;
uniform mat4 viewProjectionMatrix;
uniform float radius;
uniform vec2 coordinates;

void main()
{
    vec2 p = (position * radius) + coordinates;
    gl_Position = viewProjectionMatrix * vec4(p.x, p.y, 0.0f, 1.0f);
}