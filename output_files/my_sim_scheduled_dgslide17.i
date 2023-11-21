ILOC Simulator, Version 412-2020-1
Interlock settings: branches 

0:	[loadI 8 => r3 (8); loadI 12 => r4 (12)]
1:	[add r3 (8), r4 (12) => r1 (20); nop ]
2:	[load r1 (addr: 20) => r0 (0); nop ]
3:	[load r3 (addr: 8) => r2 (3); nop ]
4:	[nop ; nop ]
5:	[nop ; nop ]
6:	[nop ; nop ] *2
7:	[nop ; nop ] *3
8:	[store r0 (0) => r1 (addr: 20); nop ]
9:	[nop ; nop ]
10:	[nop ; nop ]
11:	[nop ; nop ]
12:	[nop ; nop ] *8
13:	[output 12 (4); nop ]
output generates => 4

Executed 14 instructions and 28 operations in 14 cycles.
