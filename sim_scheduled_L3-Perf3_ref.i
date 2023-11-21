ILOC Simulator, Version 412-2020-1
Interlock settings: branches 

0:	[loadI 4 => r4 (4); loadI 1024 => r3 (1024)]
1:	[load r3 (addr: 1024) => r2 (0); add r3 (1024), r4 (4) => r1 (1028)]
2:	[load r1 (addr: 1028) => r0 (0); nop ]
3:	[nop ; nop ]
4:	[nop ; nop ]
5:	[nop ; nop ] *1
6:	[store r3 (1024) => r2 (addr: 0); nop ] *2
7:	[store r1 (1028) => r0 (addr: 0); nop ]
8:	[nop ; nop ]
9:	[nop ; nop ]
10:	[nop ; nop ] *6
11:	[nop ; nop ] *7
12:	[output 2048 (0); nop ]
output generates => 0
13:	[output 2052 (0); nop ]
output generates => 0

Executed 14 instructions and 28 operations in 14 cycles.
