#ifndef DEFS_H
#define DEFS_H

typedef unsigned long long U64;

#define NAME "Vice 1.0"
#define BRD_SQ_NUM 120
#define MAXGAMEMOVES 2048

//label for what is within a grid square
enum {EMPTY, wP, wN, wB, wR, wQ, wK, bP, bN, bB, bR, bQ, bK };
//Next two lines are to define the rank and files of the board. The label of coordinates on the board
enum{ FILE_A, FILE_B, FILE_C, FILE_D, FILE_E, FILE_F, FILE_G, FILE_H, FILE_NONE};
enum{ RANK_1, RANK_2, RANK_3, RANK_4, RANK_5, RANK_6, RANK_7, RANK_8, RANK_NONE};

// colors to be used for the player
enum{ WHITE, BLACK, BOTH};

//squares on the board themselves
//NO_SQ is a border square
enum {
    A1 = 21, B1, C1, D1, E1, F1, G1, H1,
    A2 = 31, B2, C2, D2, E2, F2, G2, H2,
    A3 = 41, B3, C3, D3, E3, F3, G3, H3,
    A4 = 51, B4, C4, D4, E4, F4, G4, H4,
    A5 = 61, B5, C5, D5, E5, F5, G5, H5,
    A6 = 71, B6, C6, D6, E6, F6, G6, H6,
    A7 = 81, B7, C7, D7, E7, F7, G7, H7,
    A8 = 91, B8, C8, D8, E8, F8, G8, H8, NO_SQ
};

enum{ FALSE, TRUE}; 

// ints representing the castling motion
// 4 bits will tell us if we can still castle on a certain side or team
//for example, the black king is put in check but the white king and rooks remain unmoved so the array will look like
// 1 1 0 0
//if no check occurred then it would be this
// 1 1 1 1

enum{ WKCA = 1, WQCA = 2, BKCA = 4, BQCA = 8};

typedef struct {
    int move;
    int castlePerm;
    int enPas;
    int fiftyMove;
    U64 posKey;

} S_UNDO;

typedef struct {
    // a list of integers that tells whats on the board. it will 120 integers
    int pieces[BRD_SQ_NUM];
    // will be represented by the colors White, BLack, Both
    U64 pawns[3];

    //checks where kings are at
    int KingSq[2];
    // current side to move
    int side;
    //checks to see if enPas sqr is available
    int enPas;
    //Checks if 50 moves without pieces taken is done
    int fiftyMove;

    // How many half moves we are into the current search
    int ply;
    //Total culmanation of half moves done, meant to store repititions
    int hisPly;

    int castlePerm;

    U64 posKey;

    //Number of pieces left on the board, will be sorted by piece type
    int pceNum[13];

    //Number of pieces that are not a pawn
    int bigPce[3];
    //Number of Rooks and Queens
    int majPce[3];
    //Number of Bishops and Knights
    int minPce[3];

    // stores last move for the undo function
    S_UNDO history[MAXGAMEMOVES];

} S_BOARD; 

/* MACROS */

// When given the file and rank number, it will return the square from the 120 square array
#define FR2SQ(f,r) ( (21 + (f) )  + ( (r) * 10 ) )

/* GLOBALS */
extern int Sq120ToSq64[BRD_SQ_NUM];
extern int Sq64ToSq120[64];

/* FUNCTIONS */

extern void AllInit();
//init.c

#endif
