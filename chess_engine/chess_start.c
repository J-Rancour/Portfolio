// Credit for coding goes to Bluefever Software on Youtube.com. I am only following along his videos to help me learn C and actively create a project at the same time.

#include "stdio.h"
#include "defs.h"

extern int Sq120ToSq64[BRD_SQ_NUM];


int main() {

    AllInit();

    int index = 0;
    
    for(index = 0; index < BRD_SQ_NUM; ++index) {
        if(index%10==0) printf("\n");
        printf("%5d", Sq120ToSq64[index]);
    }

    printf("\n");
    printf("\n");
    for(index = 0; index < 64; ++index) {
        if(index%8==0) printf("\n");
        //print each number within 5 character widths
        printf("%5d", Sq64ToSq120[index]);
    }


    return 0;
}