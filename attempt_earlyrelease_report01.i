[ loadI 4 => r10 ; loadI 2000 => r32 ]
[ add r32,r10 => r29 ; nop ]
[ add r29,r10 => r28 ; nop ]
[ add r28,r10 => r27 ; nop ]
[ add r27,r10 => r26 ; nop ]
[ add r26,r10 => r15 ; nop ]
[ load r28 => r23 ; nop ]
[ load r27 => r22 ; nop ]
[ load r26 => r24 ; nop ]
[ load r15 => r25 ; nop ]
[ load r32 => r30 ; nop ]
[ load r29 => r31 ; add r15,r10 => r1 ]
[ nop ; mult r22,r23 => r21 ]
[ add r23,r22 => r18 ; nop ]
[ nop ; mult r24,r25 => r20 ]
[ store r3 => r1 ; loadI 2000 => r14 ]
[ add r30,r31 => r19 ; add r14,r10 => r11 ]
[ add r20,r21 => r16 ; add r18,r19 => r17 ]
[ add r16,r17 => r3 ; add r11,r10 => r9 ]
[ store r3 => r1 ; add r9,r10 => r8 ]
[ load r14 => r12 ; nop ]
[ load r11 => r13 ; nop ]
[ load r9 => r7 ; nop ]
[ load r8 => r6 ; nop ]
[ load r14 => r12 ; nop ]
[ load r11 => r13 ; nop ]
[ load r9 => r7 ; nop ]
[ load r8 => r6 ; mult r12,r13 => r5 ]
[ add r6,r7 => r4 ; nop ]
[ nop ; mult r12,r13 => r5 ]
[ nop ; mult r12,r13 => r5 ]
[ add r6,r7 => r4 ; nop ]
[ add r6,r7 => r4 ; nop ]
[ add r4,r5 => r2 ; nop ]
[ add r2,r3 => r0 ; nop ]
[ store r0 => r1 ; nop ]
[ nop ; nop ]
[ nop ; nop ]
[ nop ; nop ]
[ nop ; nop ]
[ output 2024  ; nop ]

