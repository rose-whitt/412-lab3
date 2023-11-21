ILOC Simulator, Version 412-2020-1
Interlock settings: branches 

0:	[loadI 4 => r10 (4); loadI 2000 => r32 (2000)]
1:	[add r32 (2000), r10 (4) => r29 (2004); nop ]
2:	[add r29 (2004), r10 (4) => r28 (2008); nop ]
3:	[add r28 (2008), r10 (4) => r27 (2012); nop ]
4:	[add r27 (2012), r10 (4) => r26 (2016); nop ]
5:	[add r26 (2016), r10 (4) => r15 (2020); nop ]
6:	[load r28 (addr: 2008) => r23 (2); nop ]
7:	[load r27 (addr: 2012) => r22 (3); nop ]
8:	[load r26 (addr: 2016) => r24 (4); nop ]
9:	[load r15 (addr: 2020) => r25 (5); nop ]
10:	[load r32 (addr: 2000) => r30 (0); nop ] *6
11:	[load r29 (addr: 2004) => r31 (1); add r15 (2020), r10 (4) => r1 (2024)] *7
12:	[nop ; mult r22 (3), r23 (2) => r21 (6)] *8
13:	[add r23 (2), r22 (3) => r18 (5); nop ] *9
14:	[nop ; mult r24 (4), r25 (5) => r20 (20)] *10 *12
15:	[store r3 (0) => r1 (addr: 2024); loadI 2000 => r14 (2000)] *11
16:	[add r30 (0), r31 (1) => r19 (1); add r14 (2000), r10 (4) => r11 (2004)] *14
17:	[add r20 (20), r21 (6) => r16 (26); add r18 (5), r19 (1) => r17 (6)]
18:	[add r16 (26), r17 (6) => r3 (32); add r11 (2004), r10 (4) => r9 (2008)]
19:	[store r3 (32) => r1 (addr: 2024); add r9 (2008), r10 (4) => r8 (2012)] *15
20:	[load r14 (addr: 2000) => r12 (0); nop ]
21:	[load r11 (addr: 2004) => r13 (1); nop ]
22:	[load r9 (addr: 2008) => r7 (2); nop ]
23:	[load r8 (addr: 2012) => r6 (3); nop ] *19
24:	[load r14 (addr: 2000) => r12 (0); nop ] *20
25:	[load r11 (addr: 2004) => r13 (1); nop ] *21
26:	[load r9 (addr: 2008) => r7 (2); nop ] *22
27:	[load r8 (addr: 2012) => r6 (3); mult r12 (0), r13 (1) => r5 (0)] *23
28:	[add r6 (3), r7 (2) => r4 (5); nop ] *24
29:	[nop ; mult r12 (0), r13 (1) => r5 (0)] *25 *27
30:	[nop ; mult r12 (0), r13 (1) => r5 (0)] *26
31:	[add r6 (3), r7 (2) => r4 (5); nop ] *27 *29
32:	[add r6 (3), r7 (2) => r4 (5); nop ] *30
33:	[add r4 (5), r5 (0) => r2 (5); nop ]
34:	[add r2 (5), r3 (32) => r0 (37); nop ]
35:	[store r0 (37) => r1 (addr: 2024); nop ]
36:	[nop ; nop ]
37:	[nop ; nop ]
38:	[nop ; nop ]
39:	[nop ; nop ] *35
40:	[output 2024 (37); nop ]
output generates => 37

Executed 41 instructions and 82 operations in 41 cycles.
