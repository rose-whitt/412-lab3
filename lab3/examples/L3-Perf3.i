// Example from Lab3 Performance Video, Slide 10ff
//
loadI 1024 => r3
loadI    4 => r4
load  r3   => r2
add   r3, r4 => r1
load  r1     => r0
store r3     => r2
store r1     => r0
output 2048
output 2052
