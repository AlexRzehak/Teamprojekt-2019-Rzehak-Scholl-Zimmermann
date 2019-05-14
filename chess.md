# Week 2: Paint a chess board

### [<- Back](/index.md) to project overview.

Our solution to the task of painting a chessboard on a 1000x1000 Window:

First the global variables WSIZE and OFFSET are set by a user-input in the console. WSIZE represents the size of the Window, OFFSET the width of the margin on the sides of the window. 
We then set the Window to the size WSIZExWSIZE at the position 310, 40 (this way a window of the original size 1000x1000 will be in the middle of a 1920x1080 screen).
The Chessbard itself is a scaled with the Window (the margin is substracted):
 - chessSize = WSIZE - 2 * OFFSET, 
 - tileSize = chessSize/8

A white background with a black border in the size of the chessBoard will serve as all the white tiles and yield a border around the whole board. The black tiles then get painted on with the pen disabled to prevent antoher border.

There are a number of different ways to paint the tiles. For example one can simply set up each of the 32 tiles seperatly.
Another possibility would be to create a nested for-loop (rows and collumns).
We ended up opting for a vectorial solution:

More information will likely follow.
