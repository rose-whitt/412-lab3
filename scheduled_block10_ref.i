// Average Ready Queue Length: 1
// COMP 412, Lab 3 Reference Implementation
[ loadI  1 => r5 ; loadI  1024 => r2 ]
[ lshift r5, r5  => r38 ; loadI  4 => r3 ]
[ lshift r38, r5  => r36 ; add    r5, r38  => r23 ]
[ lshift r36, r5  => r37 ; add    r2, r3  => r0 ]
[ lshift r37, r5  => r7 ; add    r36, r37  => r24 ]
[ lshift r7, r5  => r35 ; add    r23, r24  => r15 ]
[ lshift r35, r5  => r33 ; add    r7, r35  => r21 ]
[ lshift r33, r5  => r34 ; add    r7, r5  => r6 ]
[ lshift r34, r5  => r31 ; add    r33, r34  => r22 ]
[ lshift r31, r5  => r32 ; add    r21, r22  => r16 ]
[ lshift r32, r5  => r29 ; add    r31, r32  => r19 ]
[ lshift r29, r5  => r30 ; add    r15, r16  => r12 ]
[ lshift r30, r5  => r27 ; add    r29, r30  => r20 ]
[ lshift r27, r5  => r28 ; add    r19, r20  => r13 ]
[ lshift r28, r5  => r25 ; add    r27, r28  => r17 ]
[ lshift r25, r5  => r26 ; lshift r5, r6  => r4 ]
[ add    r25, r26  => r18 ; lshift r26, r5  => r10 ]
[ add    r17, r18  => r14 ; sub    r4, r5  => r1 ]
[ add    r13, r14  => r11 ; nop ]
[ add    r11, r12  => r9 ; nop ]
[ add    r9, r10  => r8 ; nop ]
[ store  r8 => r2 ; nop ]
[ store  r1 => r0 ; nop ]
[ nop    ; nop ]
[ nop    ; nop ]
[ nop    ; nop ]
[ nop    ; nop ]
[ output 1024 ; nop ]
[ output 1028 ; nop ]