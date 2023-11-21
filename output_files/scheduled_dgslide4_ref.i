// Average Ready Queue Length: 0
// COMP 412, Lab 3 Reference Implementation
[ loadI  12 => r3 ; loadI  8 => r1 ]
[ nop    ; mult   r1, r3  => r2 ]
[ nop    ; nop ]
[ nop    ; nop ]
[ add    r1, r2  => r0 ; nop ]