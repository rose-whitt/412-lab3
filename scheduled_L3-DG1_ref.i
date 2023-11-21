// Average Ready Queue Length: 0
// COMP 412, Lab 3 Reference Implementation
[ loadI  12 => r0 ; loadI  8 => r2 ]
[ nop    ; mult   r2, r0  => r3 ]
[ nop    ; nop ]
[ nop    ; nop ]
[ add    r2, r3  => r1 ; nop ]
[ store  r1 => r0 ; nop ]
[ nop    ; nop ]
[ nop    ; nop ]
[ nop    ; nop ]
[ nop    ; nop ]
[ output 12 ; nop ]
