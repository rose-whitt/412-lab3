// Example from the Lab 3 Dependence Graph Lecture
// The first example uses operations that are not in the ILOC subset for
// this project; this file is the second example shown, for example, on
// Slide 8.  
// To make it suitable for testing, I added a store and an output at
// the end of the block.
//SIM INPUT:  -i 8 3 4 
//OUTPUT:     104
loadI   8     => r1
loadI  12     => r2
mult   r1,r2  => r3
add    r1, r3 => r4
store  r4     => r2
output 12
