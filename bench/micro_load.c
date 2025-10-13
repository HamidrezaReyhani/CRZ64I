#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
int main(int argc, char **argv){
    long N = argc>1 ? atol(argv[1]) : 1000000;
    long size = argc>2 ? atol(argv[2]) : 10000000;
    int *A = malloc(size * sizeof(int));
    for(long i=0;i<size;i++) A[i]=i;
    volatile int sink=0;
    for(long i=0;i<N;i++){
        sink += A[i % size];
    }
    printf("%d\n", sink);
    return 0;
}
