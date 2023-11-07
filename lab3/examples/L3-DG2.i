// Example from the Dependence Graph Lecture
//SIM INPUT:  -i 8 3 4
//OUTPUT:  4
//
loadI  8     => r1
loadI 12     => r2
add   r1,r2  => r3
load  r3     => r4
load  r1     => r5
store r4     => r3
output 12
