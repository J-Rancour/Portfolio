// Credit for coding goes to Bluefever Software on Youtube.com. I am only following along his videos to help me learn C and actively create a project at the same time.

#include "stdio.h"
#include "defs.h"

extern int Sq120ToSq64[BRD_SQ_NUM];


int main() {

    AllInit();

    //example of using ASSERT for reference
    // int num = 2;
    // int nuts = 4;

    // ASSERT(num==nuts);
    
    //prints the board in the 120 based index and then in the 64 based index for representation of bits in each board
    // int index = 0;
    
    // for(index = 0; index < BRD_SQ_NUM; ++index) {
    //     if(index%10==0) printf("\n");
    //     printf("%5d", Sq120ToSq64[index]);
    // }

    // printf("\n");
    // printf("\n");
    // for(index = 0; index < 64; ++index) {
    //     if(index%8==0) printf("\n");
    //     //print each number within 5 character widths
    //     printf("%5d", Sq64ToSq120[index]);
    // }

    //Example of adding a pawn to D2 and G2 printed compared to empty board
    //Note the D2 pawn has not been removed when adding and printing G2.
    //Uncomment prints to see such
    U64 playBitBoard = 0ULL;

    // printf("Start:\n\n");
    // PrintBitBoard(playBitBoard);

    playBitBoard |= (1ULL << SQ64(D2));
    playBitBoard |= (1ULL << SQ64(D3));
    playBitBoard |= (1ULL << SQ64(D4));

    printf("\n");
    PrintBitBoard(playBitBoard);

    int count = CNT(playBitBoard);

    printf("Count:%d\n", count);

    // printf("D2 Added: \n\n");
    // PrintBitBoard(playBitBoard);

    //playBitBoard |= (1ULL << SQ64(G2));
    // printf("G2 Added:\n\n");
    // PrintBitBoard(playBitBoard);

    int index = POP(&playBitBoard);
    printf("index:%d\n", index);
    PrintBitBoard(playBitBoard);
    count = CNT(playBitBoard);
    printf("Count:%d\n", count);
    


    return 0;
}