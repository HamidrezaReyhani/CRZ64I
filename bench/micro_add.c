#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
int main(int argc, char **argv){
    long N = argc>1 ? atol(argv[1]) : 100000000;
    volatile int a=1, b=2, c=0;
    for(long i=0;i<N;i++){
        c = a + b;
        a = c;
    }
    printf("%d\n", c);
    return 0;
}
