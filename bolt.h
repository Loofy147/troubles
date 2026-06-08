#ifndef BOLT_H
#define BOLT_H
#include <time.h>
#include <stdio.h>
#include <math.h>
#include <string.h>
#ifdef BOLT_OFF
#define BOLT(l,b) b
#define BOLT_STATS()
#define BOLT_CHECK()
#define BOLT_ARM(e,r,t)
#else
typedef struct{char n[32];long c,t,m,x;double s;} _B;static _B _l[128];static int _n=0;
static long _gn=0,_ge=0,_gt=50,_gT=0;static double _gr=0;static int _gb=0;
static inline void _e(const char* n,long v){
 unsigned int h=0;const char* p=n;while(*p)h=h*33+*p++;int i=h&127,o=i;
 while(_l[i].n[0]&&strcmp(_l[i].n,n)){i=(i+1)&127;if(i==o)return;}
 if(_gb)return;_gn++;_gT+=v;
 if(_ge&&_gn>=_ge){memset(_l,0,sizeof(_l));_gn=0;_gT=0;_n=0;printf("⚡ Bolt Epoch Reset\n");}
 if(_gr&&_gn%1000==0){long o=_gn*_gt;if((double)o/(o+_gT)>_gr){_gb=1;printf("⚡ Bolt Tripwire\n");}}
 unsigned int h=0;const char* p=n;while(*p)h=h*33+*p++;int i=h%128,o=i;
 while(_l[i].n[0]&&strcmp(_l[i].n,n)){i=(i+1)%128;if(i==o)return;}
 _B* s=&_l[i];if(!s->n[0]){strncpy(s->n,n,31);s->m=v;s->x=v;_n++;}
 s->c++;s->t+=v;s->s+=(double)v*v;if(v<s->m)s->m=v;if(v>s->x)s->x=v;
}
#define BOLT(l,b) do{if(_gb){b;}else{struct timespec s,e;clock_gettime(CLOCK_MONOTONIC,&s);{b;}clock_gettime(CLOCK_MONOTONIC,&e);_e(l,(e.tv_sec-s.tv_sec)*1000000000L+(e.tv_nsec-s.tv_nsec));}}while(0)
#define BOLT_ARM(e,r,t) do{_ge=e;_gr=r;_gt=t;_gn=0;_gT=0;_gb=0;}while(0)
static inline void BOLT_STATS(){
 for(int i=0;i<128;i++)if(_l[i].n[0]){_B* s=&_l[i];double a=(double)s->t/s->c,d=sqrt(fmax(0,s->s/s->c-a*a));
 printf("%-16s n=%-8ld μ=%.1fns σ=%.1fns [%ldns…%ldns]\n",s->n,s->c,a,d,s->m,s->x);}}
static inline void BOLT_CHECK(){
 struct timespec s,e;long n=1000000;clock_gettime(CLOCK_MONOTONIC,&s);
 for(long i=0;i<n;i++){BOLT("check",{});}clock_gettime(CLOCK_MONOTONIC,&e);
 double t=(double)((e.tv_sec-s.tv_sec)*1000000000L+(e.tv_nsec-s.tv_nsec))/n;
 printf("⚡ C Bolt Tax: %.1fns/call\n",t);}
#endif
#endif
