#ifndef BOLT_H
#define BOLT_H
#include <time.h>
#include <stdio.h>
#include <math.h>
#include <string.h>
#ifdef BOLT_OFF
#define BOLT(l,b) b
#define BOLT_STATS()
#else
typedef struct{char n[32];long c,t,m,x;double s;} _B;static _B _l[64];static int _n=0;
static inline void _e(const char* n,long v){
 _B* s=0;for(int i=0;i<_n;i++)if(!strcmp(_l[i].n,n)){s=&_l[i];break;}
 if(!s&&_n<64){s=&_l[_n++];strncpy(s->n,n,31);s->m=v;s->x=v;}
 if(s){s->c++;s->t+=v;s->s+=(double)v*v;if(v<s->m)s->m=v;if(v>s->x)s->x=v;}
}
#define BOLT(l,b) do{struct timespec s,e;clock_gettime(CLOCK_MONOTONIC,&s);{b;}clock_gettime(CLOCK_MONOTONIC,&e);_e(l,(e.tv_sec-s.tv_sec)*1000000000L+(e.tv_nsec-s.tv_nsec));}while(0)
static inline void BOLT_STATS(){
 for(int i=0;i<_n;i++){_B* s=&_l[i];double a=(double)s->t/s->c,d=sqrt(fmax(0,s->s/s->c-a*a));
 printf("%-16s n=%-8ld μ=%.1fns σ=%.1fns [%ldns…%ldns]\n",s->n,s->c,a,d,s->m,s->x);}}
#endif
#endif
