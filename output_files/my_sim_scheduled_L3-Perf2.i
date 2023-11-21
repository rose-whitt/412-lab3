ILOC Simulator, Version 412-2020-1
Interlock settings: branches 

0:	[loadI 8 => r1 (8); loadI 12 => r4 (12)]
1:	[load r1 (addr: 8) => r3 (3); nop ]
2:	[load r4 (addr: 12) => r5 (4); nop ]
3:	[nop ; nop ]
4:	[nop ; nop ]
5:	[nop ; nop ] *1
6:	[add r1 (8), r3 (3) => r2 (11); nop ] *2
7:	[store r2 (11) => r4 (addr: 12); sub r2 (11), r3 (3) => r0 (8)]
8:	[nop ; nop ]
9:	[nop ; nop ]
10:	[nop ; nop ]
11:	[nop ; nop ] *7
12:	[output 8 (3); nop ]
output generates => 3
13:	[store r0 (8) => r1 (addr: 8); nop ]
14:	[nop ; nop ]
15:	[nop ; nop ]
16:	[nop ; nop ]
17:	[nop ; nop ] *13
18:	[output 8 (8); nop ]
output generates => 8

Executed 19 instructions and 38 operations in 19 cycles.
