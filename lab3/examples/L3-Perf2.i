// Example from the Lab 3 Performance Video, Slide 15
//SIM INPUT -i 8 3 4
//OUTPUT:  3 8
//
loadI   8 => r1
loadI  12 => r2
load   r1 => r3
load   r2 => r4
add    r1,r3 => r5
store  r5 => r2
output  8
sub    r5,r3 => r6
store  r6 => r1
output  8
