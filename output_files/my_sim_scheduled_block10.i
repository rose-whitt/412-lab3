ILOC Simulator, Version 412-2020-1
Interlock settings: branches 

0:	[loadI 1 => r5 (1); loadI 1024 => r2 (1024)]
1:	[lshift r5 (1), r5 (1) => r38 (2); loadI 4 => r3 (4)]
2:	[lshift r38 (2), r5 (1) => r36 (4); add r5 (1), r38 (2) => r23 (3)]
3:	[lshift r36 (4), r5 (1) => r37 (8); add r2 (1024), r3 (4) => r1 (1028)]
4:	[lshift r37 (8), r5 (1) => r7 (16); add r36 (4), r37 (8) => r24 (12)]
5:	[lshift r7 (16), r5 (1) => r35 (32); add r23 (3), r24 (12) => r15 (15)]
6:	[lshift r35 (32), r5 (1) => r33 (64); add r7 (16), r35 (32) => r21 (48)]
7:	[lshift r33 (64), r5 (1) => r34 (128); add r7 (16), r5 (1) => r6 (17)]
8:	[lshift r34 (128), r5 (1) => r31 (256); add r33 (64), r34 (128) => r22 (192)]
9:	[lshift r31 (256), r5 (1) => r32 (512); add r21 (48), r22 (192) => r16 (240)]
10:	[lshift r32 (512), r5 (1) => r29 (1024); add r31 (256), r32 (512) => r19 (768)]
11:	[lshift r29 (1024), r5 (1) => r30 (2048); add r15 (15), r16 (240) => r12 (255)]
12:	[lshift r30 (2048), r5 (1) => r27 (4096); add r29 (1024), r30 (2048) => r20 (3072)]
13:	[lshift r27 (4096), r5 (1) => r28 (8192); add r19 (768), r20 (3072) => r13 (3840)]
14:	[lshift r28 (8192), r5 (1) => r25 (16384); add r27 (4096), r28 (8192) => r17 (12288)]
15:	[lshift r25 (16384), r5 (1) => r26 (32768); lshift r5 (1), r6 (17) => r4 (131072)]
16:	[add r25 (16384), r26 (32768) => r18 (49152); lshift r26 (32768), r5 (1) => r10 (65536)]
17:	[add r17 (12288), r18 (49152) => r14 (61440); sub r4 (131072), r5 (1) => r0 (131071)]
18:	[add r13 (3840), r14 (61440) => r11 (65280); nop ]
19:	[add r11 (65280), r12 (255) => r9 (65535); nop ]
20:	[add r9 (65535), r10 (65536) => r8 (131071); nop ]
21:	[store r8 (131071) => r2 (addr: 1024); nop ]
22:	[nop ; nop ]
23:	[nop ; nop ]
24:	[nop ; nop ]
25:	[nop ; nop ] *21
26:	[store r0 (131071) => r1 (addr: 1028); nop ]
27:	[nop ; nop ]
28:	[nop ; nop ]
29:	[nop ; nop ]
30:	[nop ; nop ] *26
31:	[output 1024 (131071); nop ]
output generates => 131071
32:	[output 1028 (131071); nop ]
output generates => 131071

Executed 33 instructions and 66 operations in 33 cycles.
