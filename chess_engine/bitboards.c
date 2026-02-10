#include "stdio.h"
#include "defs.h"

void PrintBitBoard(U64 bb) {

    U64 shiftMe = 1ULL;
    int rank = 0;
    int file = 0;
    int sq = 0;
    int sq64 = 0;

    printf("\n");
    //starting at the 8th rank file A, we are descending ranks and ascending files in each rank
    //printing one square after the other
    for(rank = RANK_8; rank >= RANK_1; --rank) {
        for(file = FILE_A; file <= FILE_H; ++file) {
            sq = FR2SQ(file, rank); //120 based index
            sq64 = SQ64(sq); // 64 based index
            //if shifting ULL by 64 based index and bitwise ended in the bitboard
            //print X if nonzero
            //print - if zero
            if((shiftMe << sq64) & bb)
                printf("X");
                else
                printf("-");
            
        }
        printf("\n");
    }
    printf("\n\n");

}