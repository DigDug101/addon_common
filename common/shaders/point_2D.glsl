uniform mat4  MVPMatrix;        // pixel matrix
uniform vec2  screensize;       // width,height of screen (for antialiasing)
uniform vec2  center;           // center of point
uniform float radius;           // radius of circle
uniform float border;           // width of border
uniform vec4  color;            // color point
uniform vec4  colorBorder;      // color of border

/////////////////////////////////////////////////////////////////////////
// vertex shader

in vec2 pos;                    // four corners of point ([0,0], [0,1], [1,1], [1,0])

noperspective out vec2 vpos;    // position scaled by screensize

void main() {
    vec2 p = center + vec2((pos.x - 0.5) * (radius+border), (pos.y - 0.5) * (radius+border));
    gl_Position = MVPMatrix * vec4(p, 0.0, 1.0);
    vpos = vec2(gl_Position.x * screensize.x, gl_Position.y * screensize.y);  // just p?
}


/////////////////////////////////////////////////////////////////////////
// fragment shader

in vec2 vpos;

void main() {
    vec2 ctr = (MVPMatrix * vec4(center, 0.0, 1.0)).xy;
    float d = distance(vpos, vec2(ctr.x * screensize.x, ctr.y * screensize.y));
    if(d > radius + border) discard;
    if(d <= radius) {
        float d2 = radius - d;
        gl_FragColor = mix(colorBorder, color, clamp(d2 - border/2, 0.0, 1.0));
    } else {
        float d2 = d - radius;
        gl_FragColor = mix(colorBorder, vec4(0,0,0,0), clamp(d2 - border/2, 0.0, 1.0));
    }
}

